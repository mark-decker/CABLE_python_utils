#!/usr/bin/env python


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


# Script to create CABLE (compiling and making necessary directories) and run CABLE in offline mode

#TODO : transfer model output to another server.  perform analysis on the output

import os
import sys
import subprocess
import shutil
from create_cable_nml import cable_namelist
from build_cable import build_model

class ModelParams(object):
    """
    class that holds tunable parameters.  takes a list of parameter names and a list of 
    parameter values and zips both into a dict
    """

    def __init__(self,parameter_names,parameter_values):
        self.params = dict(zip(parameter_names,parameter_values))


class pycable(object):
    """
    Class containing model run information.
    To build, specify the parameters, and run the model do the following:

    modelrun = runinfo(dirs,start_year,end_year,buildtime_switches)
    modelrun.SetupRundir()
    modelrun.compile_cable()
    modelrun.create_readme(user_parameters)
    modelrun.define_parameters(user_parameters)
    modelrun.IncrementYear(start_year,start_year)
    modelrun.RunSimulation()

    """

    def __init__(self,**kwargs)

        self.builder = build_model(**kwargs)

        self.nml_maker = cable_namelist(**kwargs)




def __init__(self,\
               nml_file=None,\
               out_dir=None,\
               nml_file_template=None,\
               logger=None,\
               user_parameters={}):

        self.dirs            = dirs
        self.first_year      = year
        self.end_year        = last_year
        self.year            = self.first_year
        self.ncpus           = 8
        self.numyears        = self.end_year - self.first_year + 1

        if not namelist_template:
            namelist_template = 'cable.nml'

        if self.numyears < 1:  sys.exit("Start year must preceed the end")      
        #use 'has a' instead of parent-child.  don't need to inherit just use the functions.
        self.builder = build_model(SourceDirectory=dirs['src'],\
                                  BuildDirectory=dirs['run'], \
                                  switches=build_switches)

        self.namelist = cable_namelist(namelist_file=namelist_template,\
                                      namelist_def_directory=os.path.join(dirs['aux'],'offline'),\
                                      namelist_out_directory=dirs['run'])

    def setup_rundir(self):

        atmo_forcing = os.path.join(self.dirs['run'],'gswp')
        surface_data = os.path.join(self.dirs['run'],'surface_data')

        if not os.path.isdir(self.dirs['run']):                                                            #does the run directory exist?
            chck = os.mkdir(self.dirs['run'])

        if not os.path.islink(self.dirs['run']+"/gswp"):
            subprocess.call(["ln","-s",self.dirs['met'],self.dirs['run']+"/gswp"])                           #create symbolic links to forcing data

        if not os.path.islink(self.dirs['run']+"/surface_data"):
            subprocess.call(["ln","-s",self.dirs['srf'],self.dirs['run']+"/surface_data"])                   ##to avoid duplicating it


    def increment_year(self,current_year,new_year):
        """ wrapper to cable_namelist.update_year """
        self.namelist.update_year(current_year,new_year)


    def compile_cable(self):
        """ wrapper to build_model.make_the_model """
        self.builder.make_the_model()   


    def create_readme(self,dirs,user_parameters,buildtime_switches):
        """
        Out put a text README file to the run directory that lists
        all of the uder defined parameters, directory names, and
        build flags/switches
        """

        if not os.path.isdir(self.dirs['run']):
            sys.exit('cannot create readme.  run directory doesnt exist')

        outfil=os.path.join(self.dirs['run'],'README')

        #get svn info and diff

        subprocess.call(["svn","info",self.dirs['build']+" > .svn.info"])                   ##to avoid duplicating it
        subprocess.call(["svn","diff",self.dirs['build']+" > .svn.diff"])                   ##to avoid duplicating it

        with open(outfil,'w') as output_file:
              fo.write('preppending new information')

        #can merge into one dict
        #def combine_dicts(d1,d2):
        #    return {k:v for d in (d1,d2) for k, v in d.iteritems()}
        #
        #merged_dicts = combine_dicts(combine_dicts(dirs,user_parameters),buildtime_switches)

        output_file.write('\n')
        output_file.write('\n')
        output_file.write('The directories chosen for this model run are as follows:\n')

        for p_name,p_value in dirs.items():
            output_file.write(str(p_name)+'    =  '+str(p_value)+'\n')

        output_file.write('\n')
        output_file.write('\n')
        output_file.write('The parameters chosen for this model run are as follows:\n')
      
        for p_name,p_value in user_parameters.items():
            output_file.write(str(p_name)+' = '+str(p_value)+'\n')  

        output_file.write('\n')
        output_file.write('\n')
        output_file.write('The build switches chosen for this model run are as follows:\n')
      
        for p_name,p_value in buildtime_switches.items():
            output_file.write(str(p_name)+' = '+str(p_value)+'\n')                

        output_file.close()



    def run_simulation(self):
        """
        Use subprocess to run the simulation.  If build_model.switches['mpi']
        is true then run with mpi using self.ncpus.
        """

        os.chdir(self.dirs['run'])
        if self.builder.switches['mpi']:
            try:
                subprocess.call(['mpirun','-n',self.ncpus,'./'+self.builder.Target])
            except:
                sys.exit('Failed to run the simulation for '+str(self.year))
        else:
            try:
                subprocess.call(['./'+self.builder.Target])
            except:
                sys.exit('Failed to run the simulation for '+str(self.year))


    def store_output(self,out_dir):
        """
        Copy the model output to out_dir.  The model output is invariant when the simulation
        covers the same year more than once so moving the output to a new directory
        prevents the data from being overwritten
        """

        os.chdir(self.dirs['run'])                                        #ensure we are in correct dir

        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)

        for output_file in os.listdir(self.dirs['run']):
            if output_file.endswith(".nc") or output_file.endswith(".txt"): #copy netcdf output and txt logs
                shutil.copy(output_file,out_dir)



if __name__ == '__main__':

    dirs = {}  #empty dict to hold key/value pairs of directories
    start_year  = 1986
    end_year    = 1995
    dirs['run'] = "/srv/ccrc/data32/z3362708/CABLE_runs/GSWP_control_test_auto"#Aust_GW_test_09
    dirs['src'] = "/srv/ccrc/data32/z3362708/CABLE/CABLE-ssgw-trunk"
    #dirs['met'] ="/srv/ccrc/data10/z3362708/CABLE_Forcing/0.25deg/gldas"# "/srv/ccrc/data32/z3362708/CABLE_GSWP" #alt_forcing parameter?
    dirs['met'] ="/srv/ccrc/data10/z3362708/GSWP"
    dirs['srf'] = "/srv/ccrc/data10/z3362708/CABLE_surfacedata"
    dirs['aux'] = "/srv/ccrc/data32/z3362708/CABLE/CABLE_AUX-dev"

    number_runs = 1

    #define a dict holding build/run switches and their values
    buildtime_switches = {'mpi': True,'clean_build': False}

    #change these to reading a text file.
    #define the user_parameters dict
    #this holds key value pairs where
    #key - name of the namelist option we wish to set
    #value - what we are setting the namelist option to

    user_parameters = {}

    user_parameters['spinup']                 = ".true."
    user_parameters['output%averaging']       = "'all'"
    user_parameters['cable_user%alt_forcing'] = ".true."

    user_parameters['gw_params%MaxHorzDrainRate']  = 2.0#0.005
    user_parameters['gw_params%EfoldHorzDrainRate']= 2.0
    user_parameters['gw_params%EfoldMaxSatFrac']   = 1.0# 0.01
    user_parameters['gw_params%MaxSatFraction']    = 0.4# 0.6
    user_parameters['cable_user%GW_MODEL']         = ".false."
    #user_parameters['cable_user%TwoD_GW']          = ".true."

    user_parameters['filename%type'] ="'surface_data/gridinfo_CSIRO_1x1.nc'"
    user_parameters['filename%veg']  ="'surface_data/def_veg_params.txt'"
    user_parameters['filename%soil'] ="'surface_data/def_soil_params.txt'"

    namelist_template_file = 'gswp_cable.nml'# 'cable_gldas_aust.nml'

    modelrun = runinfo(dirs,start_year,end_year,buildtime_switches,namelist_template_file)

    modelrun.setup_rundir()   
    #make surface data if needed?
    #below will add pfts using the namelist pft_regrid_namelist.nml
    #ifort -mcmodel=medium -I/$NETCDF/include -L/$NETCDF/lib regrid_LIS_binary_LandCover_output_Perent_PFTs_netcdf.f90 -lnetcdff

    modelrun.compile_cable()

    modelrun.create_readme(dirs,user_parameters,buildtime_switches)

    #can put a loop here for multiple runs with varying params.  would be nice if each launched own process?
    modelrun.namelist.set_parameters(**user_parameters)

    #to spinup run the model n times over the m year period
    for irun in range(number_runs):

        if irun > 0:
            modelrun.increment_year(modelrun.end_year,start_year)   #use 1995 restart for ic
        else:
            modelrun.increment_year(start_year,start_year)         #init first year by calling with same year 2x

        for year_loop in range(modelrun.first_year,modelrun.end_year+1):

            #run the model
            modelrun.run_simulation()

            if year_loop < modelrun.end_year:
                modelrun.increment_year(year_loop,year_loop+1)

        model_output_directory = "spin_number_"+str(irun)
        modelrun.store_output(model_output_directory)




#process output

#transfer the output somewhere



