#Copyright (C) 2014  Mark Decker

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>


#reads a fortran namelist file that contains default parameter values
#replaces the parameter values in the namelist file with user defined values
#can also update the year in the namelist file for running a model over multiple years

import re
import sys
import os
import string
from collections import OrderedDict 
import time
import logging

class cable_namelist(object):
    """Class containing information and functions to create a namelist file needed to run cable"""

    def __init__(self,nml_out_dir='.',nml_file='cable.nml'):

        self.out_dir = nml_out_dir

        self.nml_file  = os.path.join(self.out_dir,nml_file)


        self.logger = self.nml_logger(None)

        self.nml_data_out = self.def_namelist()

    def save_params(**kwargs):
        user_choices = {}
        if kwargs is not None:
           for key,val in kwargs.iteritems():
               user_choices[key2] = val

        self.user_choices = user_choices

    def nml_logger(self,app_logger):

        #set up logger to keep track of everything
        if app_logger is None:
            logger = logging.getLogger('cable_namelist')
        elif not isinstance(app_logger,logging.Logger):
            logger = logging.getLogger('cable_namelist')
        else:
            logger = app_logger

        log_handler = logging.FileHandler(os.path.join(self.out_dir,'cable_namelist.log') )
        log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        log_handler.setLevel(logging.INFO)

        logger.addHandler(log_handler)

        return logger

        self.nml_data_out = '' 

    def remove_first_last_nml_lines(self,contents):


        return contents,first_line,last_line

    def find_all_nml_key_vals(self,contents):
    
        parameters = OrderedDict()                  #keep the order of the parameters to enable easier comparisons to default
    
        for line in contents:
      
            check_comment = line.strip()
    
            if (len(check_comment) > 1):
                if cmp(check_comment[0],'!'):
                    pname,pvalue = line.split('=',1)
                    parameters[ pname.strip() ] = pvalue.strip()


        return parameters

    def update_parameters(self,new_parameters=None):
        if new_parameters is not None:

            new_parameters = OrderedDict(new_parameters)

            try:
               contents = self.nml_file.read()
            except:
               contents = self.def_namelist()

            contents = contents.split('\n')

            self.nml_data_out = contents.pop(0)+'\n'
            last_line  = ''                                   #remove &end from the namelist
            while '&end' not in last_line:                    #so we can add new parameters and values
                last_line = contents.pop()                    #may need to pop several times due to trailing \n's

            parameters = self.find_all_nml_key_vals(contents)

            for pname,pvalue in new_parameters.items():  #assume extra parameters not in the default namelist belong
                parameters[pname] = pvalue                     #this will let through typos.  be careful

            for pname,pvalue in parameters.items():
                self.nml_data_out += '  '+str(pname)+' = '+str(pvalue)+'\n'

            self.nml_data_out += last_line+'\n'

            self.write_namelist_file()
         

    def set_parameters(self):
        """ writes the parameters in the namelist file.  Default values read from default file 
        with user defined values passed in using parameter_names=list and parameter_values=list"""

        self.nml_file_template=self.def_namelist()
 
        contents = self.nml_file_template.split('\n')                 #split file into list using \n

        self.nml_data_out = contents.pop(0)+'\n'

        last_line  = ''                                   #remove &end from the namelist
        while '&end' not in last_line:                    #so we can add new parameters and values
           last_line = contents.pop()                    #may need to pop several times due to trailing \n's

        parameters = self.find_all_nml_key_vals(contents)

        for pname,pvalue in self.user_choices.items():  #assume extra parameters not in the default namelist belong
            parameters[pname] = pvalue                     #this will let through typos.  be careful

        for pname,pvalue in parameters.items():
            self.nml_data_out += '  '+str(pname)+' = '+str(pvalue)+'\n'

        self.nml_data_out += last_line+'\n'

    #for gswp3 runs to continue need to update year each sim
    def set_year(self,NewYear):
        """ changes the year and restart input/output file names in cable.nml"""
        #contents          = open(self.nml_file).read()    #read the namelist file 
        self.year         = NewYear                                #store the new year in self
        prev_year         = self.year - 1
        restart_in_string = "filename%restart_in = ' '"            #blank if we are updating namelist for first time

        new_restart_in = "filename%restart_in = 'restart_"+str(prev_year)+".nc'"  #restart if we have updated previously

        #sometimes year not in output,log, and restart files
        files_without_year = []
        files_without_year.append(["'cable_output.nc'","'cable_output_"+str(self.year)+".nc'"])
        #log file
        files_without_year.append(["'cable_log.txt'","'cable_log_"+str(self.year)+".txt'"])
        #output restart file
        files_without_year.append(["'restart_out.nc'","'restart_"+str(self.year)+".nc'"])

        #find YYYY pattern, replace with self.year
        #this will not work with new yearstart and yearend namelist options and if restart_in is set
        #so ensure restart in is correct after sub
        year_pattern = re.compile('(?<!Haverd)[1-2][0-9][0-9][0-9]')         
        #contents = year_pattern.sub(str(self.year), contents)   #replace year
        self.nml_data_out = year_pattern.sub(str(self.year), self.nml_data_out)

        #restart in now had wrong year
        restart_pattern = re.compile("filename%restart_in = 'restart_[1-2][0-9][0-9][0-9].nc'")  #look for restart_YYYY.nc
        #contents = restart_pattern.sub(new_restart_in,contents)                  #remove restart file
        self.nml_data_out = restart_pattern.sub(new_restart_in,self.nml_data_out)                  #remove restart file

        for [old_file,new_file] in files_without_year:
            if old_file in self.nml_data_out:
                #contents = contents.replace(old_file,new_file)
                self.nml_data_out = self.nml_data_out.replace(old_file,new_file)
      

    def write_namelist_file(self):
        if os.path.isfile(self.nml_file):
            os.rename(self.nml_file,\
                      os.path.join(self.out_dir,'.{}_cable.nml'.format(str(time.time()))) )
        output_file = open(self.nml_file,'w')        #open the namelist file for writting
        output_file.write(self.nml_data_out)                    #write new contents to the namelist file
        output_file.flush()
        output_file.close() 

    def def_namelist(*args):
        def_nml ="""&cable
   filename%met = " "
   filename%out = "cable_output.nc"
   filename%log = "cable_log.txt"
   filename%restart_in  = "restart_in.nc" 
   filename%restart_out = "restart_out.nc"
   filename%type    = "CABLE_GSWP3_HGSD_DRT_Surface_Data_veg_fix_dtb_2.nc"
   filename%veg    = "def_veg_params_zr_clitt_correct.txt"
   filename%soil    = "def_soil_params.txt"
   filename%gw_elev = "GSWP3_elevation_slope_mean_stddev_dtb.nc"
   filename%path    = './'
   vegparmnew = .TRUE.  ! using new format when true
   soilparmnew = .true.  ! using new format when true
   spinup = .true.  ! do we spin up the model?
   delsoilM = 0.05   ! allowed variation in soil moisture for spin up
   delsoilT = 0.05   ! allowed variation in soil temperature for spin up
   output%restart = .TRUE.  ! should a restart file be created?
   output%met = .TRUE.  ! input met data
   output%flux = .TRUE.  ! convective, runoff, NEE
   output%soil = .TRUE.  ! soil states
   output%snow = .TRUE.  ! snow states
   output%radiation = .TRUE.  ! net rad, albedo
   output%carbon    = .TRUE.  ! NEE, GPP, NPP, stores
   output%veg       = .TRUE.  ! vegetation states
   output%params    = .TRUE.  ! input parameters used to produce run
   output%balances  = .TRUE.  ! energy and water balances
   output%averaging = "all"
   check%ranges     = .FALSE.  ! variable ranges, input and output
   check%energy_bal = .TRUE.  ! energy balance
   check%mass_bal   = .TRUE.  ! water/mass balance
   verbose = .FALSE. ! write details of every grid cell init and params to log?
   leaps = .false. ! calculate timing with leap years?
   logn = 88      ! log file number - declared in input module
   fixedCO2 = 390.0   ! if not found in met file, in ppmv
   spincasainput = .FALSE.    ! input required to spin casacnp offline
   spincasa      = .FALSE.     ! spin casa before running the model if TRUE, and should be set to FALSE if spincasainput = .TRUE.
   l_casacnp     = .FALSE.  ! using casaCNP with CABLE 
   l_laiFeedbk   = .FALSE.  ! using prognostic LAI
   l_vcmaxFeedbk = .FALSE.  ! using prognostic Vcmax
   icycle = 0   ! BP pull it out from casadimension and put here; 0 for not using casaCNP, 1 for C, 2 for C+N, 3 for C+N+P
   casafile%cnpipool=' *** SET PATH IN cable.nml *** '
   casafile%cnpbiome=' *** SET PATH IN cable.nml *** '
   casafile%cnpepool='poolcnpOut.csv'    ! end of run pool size
   casafile%cnpmetout='casamet.nc'                ! output daily met forcing for spinning casacnp
   casafile%cnpmetin=''          ! list of daily met files for spinning casacnp
   casafile%phen=' *** SET PATH IN cable.nml *** '
   casafile%cnpflux='cnpfluxOut.csv'
   ncciy = 0 ! 0 for not using gswp; 4-digit year input for year of gswp met
   gswpfile%rainf = "./gswp/Rainf/GSWP3.BC.Rainf.3hrMap.1901.nc"
   gswpfile%snowf = "./gswp/Snowf/GSWP3.BC.Snowf.3hrMap.1901.nc"
   gswpfile%LWdown= "./gswp/LWdown/GSWP3.BC.LWdown.3hrMap.1901.nc"
   gswpfile%SWdown= "./gswp/SWdown/GSWP3.BC.SWdown.3hrMap.1901.nc" 
   gswpfile%PSurf = "./gswp/PSurf/GSWP3.BC.PSurf.3hrMap.1901.nc"
   gswpfile%Qair  = "./gswp/Qair/GSWP3.BC.Qair.3hrMap.1901.nc"
   gswpfile%Tair  = "./gswp/Tair/GSWP3.BC.Tair.3hrMap.1901.nc"
   gswpfile%wind  = "./gswp/Wind/GSWP3.BC.Wind.3hrMap.1901.nc"
   gswpfile%mask  = "./surface_data/GSWP3_landmask.nc"
   redistrb = .FALSE.  ! Turn on/off the hydraulic redistribution
   wiltParam = 0.5
   satuParam = 0.8
   cable_user%FWSOIL_SWITCH = 'Haverd2013'        ! choices are: 
                                                 ! 1. standard 
                                                 ! 2. non-linear extrapolation 
                                                 ! 3. Lai and Ktaul 2000 
                                                 ! 4. Haverd2013
                              
   cable_user%DIAG_SOIL_RESP = 'ON ' 
   cable_user%LEAF_RESPIRATION = 'ON ' 
   cable_user%RUN_DIAG_LEVEL= 'BASIC'        ! choices are: 
                                                 ! 1. BASIC
                                                 ! 1. NONE
   cable_user%CONSISTENCY_CHECK= .TRUE.      ! TRUE outputs combined fluxes at each timestep for comparisson to A control run 
   cable_user%CASA_DUMP_READ = .FALSE.      ! TRUE reads CASA forcing from netcdf format
   cable_user%CASA_DUMP_WRITE = .FALSE.      ! TRUE outputs CASA forcing in netcdf format
   cable_user%SSNOW_POTEV= 'HDM'      ! Humidity Deficit Method
   cable_user%GW_MODEL = .true.       !True means use the groundwater module, false means use default soil snow scheme
   cable_user%GSWP3 = .false.
   cable_user%GS_SWITCH = 'medlyn'
   cable_user%or_evap = .true.
   CABLE_USER%YEARSTART = 0
   CABLE_USER%YEAREND = 0
   cable_user%L_NEW_ROUGHNESS_SOIL = .true.
   cable_user%call_climate = .false.
   cable_user%soil_struc='default'
   cable_user%litter = .false.
   cable_user%max_spins = 15
   gw_params%subsurface_sat_drainage = .false.
   gw_params%ssgw_ice_switch = .true.
   gw_params%MaxSatFraction     = -1.0  !No sat/unsat fractions used in large scale modeling
   gw_params%MaxHorzDrainRate   = 7e-4  !ranges from 1e-2 to 1e-6
   gw_params%EfoldHorzDrainRate = 5.0   !ranges from 0 to 10
   gw_params%hkrz = 0.0                 !efold**-1 for increasing hk, cheap macro pores
   gw_params%zdepth = 0.0               !depth at whick macropores end

&end
"""
        return def_nml

if __name__ == '__main__':


    cust_opts = {}

    cust_opts['cable%spinup']                 = ".false."
    cust_opts['cable%output%averaging']       = "'monthly'"
    cust_opts['cable%cable_user%alt_forcing'] = ".false."

    cust_opts['cable%gw_params%MaxHorzDrainRate']  = 5e-4
    cust_opts['cable%gw_params%EfoldHorzDrainRate']= 0.3
    cust_opts['cable%gw_params%MaxSatFraction']    = 0.3
    cust_opts['cable%cable_user%GW_MODEL']         = ".true."

    cust_opts['cable%filename%type'] ="'surface_data/gridinfo_CSIRO_1x1.nc'"
    cust_opts['cable%filename%veg']  ="'surface_data/def_veg_params.txt'"
    cust_opts['cable%filename%soil'] ="'surface_data/def_soil_params.txt'"

    source_directory = '.'#/srv/ccrc/data03/z3362708/CABLE/CABLE_AUX-dev/offline'

    cablenamelist = cable_namelist(source_directory,**cust_opts)
    cablenamelist.set_parameters()
    cablenamelist.set_year(1986)
    cablenamelist.write_namelist_file()
    #for runyear in range(1987,1989):
    #    prevyear = runyear - 1
    #    cablenamelist.update_year(prevyear,runyear)

    with open(cablenamelist.nml_file) as f:
        print(f.read())

    #new_opts = {}
    #new_opts['gw_params%MaxHorzDrainRate']  = 5e-7
    #new_opts['gw_params%EfoldHorzDrainRate']= 0.9
    #new_opts['gw_params%MaxSatFraction']    = 0.1

    #cablenamelist.update_parameters(new_parameters=new_opts)
    #with open(cablenamelist.nml_file) as f:
    #    print(f.read())

