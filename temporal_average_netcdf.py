#system libraries
import os
import copy
#matplotlib libraries
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import rcParams
#numpy libraries
import numpy as np
import numpy.ma as ma
#ncl  python libraries
try:
  from PyNIO import Nio
except:
  import Nio


def temporal_average_netcdf(run_id,input_directory,output_directory,year_list):


    input_directory = os.path.join(input_directory,run_id)
    nyrs    = len(year_list)

    output_directory = os.path.join(input_directory,output_directory)
    output_file = os.path.join(output_directory,run_id+'.nc')

    year_str_list = [str(year) for year in year_list]


    file_list = []
    #return a list of the files matching a prefix for the given years
    for tmp_file in os.listdir(input_directory):
        if tmp_file.endswith(".nc") and tmp_file.startswith("cable"):
            if any([year in tmp_file for year in year_str_list]):
                file_list.append(os.path.join(input_directory,tmp_file))


    #must read a single file at a time.  loop over the files and put into a numpy.ma array

    #create a list of the nio object files
    #create a list of all variable objects and work with these rather than my old school thinking
    nc_files = []
    for ifile,ncfile in enumerate(file_list):

        #nc_files.append(Nio.open_file(ncfile,'r'))
        cdf_file = Nio.open_file(ncfile,"r")
  
        if ncfile == file_list[0]:

            var_list = cdf_file.variables.keys()
            dimensions = cdf_file.dimensions
            ntot_file = dimensions['time']
            ntotal    = ntot_file*len(file_list)
            ntot_avg  = 0#len(file_list)

            #determine which variables require temporal processing
            lvar_proc  = []
            lvar_nproc = []
            for var in var_list:
                if cdf_file.variables[var].dimensions[0] == 'time':
                    lvar_proc.append(var)
                else:
                    lvar_nproc.append(var)

            #write all of the dims non-prc vars to output file
            try:
                os.remove(output_file)
            except:
                pass
            cdf_out = Nio.open_file(output_file,'w')

            for kdim,vdim in dimensions.items():
                if kdim != 'time':
                    cdf_out.create_dimension(kdim,vdim)
                else:
                    cdf_out.create_dimension(kdim,None)  #make time unlimited

            #write the non-proccessed data to the file
            for var in lvar_nproc:
                tmp_var = cdf_file.variables[var]
                tmp_dims = tmp_var.dimensions
                var_out = cdf_out.create_variable(var,tmp_var.typecode(),tmp_dims)
                atts    = tmp_var.attributes
                for katts,vatts in atts.items():
                    try:
                        setattr(cdf_out.variables[var],katts,vatts)
                    except:
                        pass

                var_out.assign_value(tmp_var.get_value())

            #time dep data
            time_vars = []
            FillVal   = []
            for var in lvar_proc:
                tmp_var = cdf_file.variables[var]
 
                tmp_dims = list(tmp_var.dimensions)   #decided to keep dim names the same
                total_dims = [dimensions[dim] for dim in tmp_dims]
                del total_dims[0]
                total_dims.insert(0,ntotal)

                var_out = cdf_out.create_variable(var,tmp_var.typecode(),tuple(tmp_dims))
                atts    = tmp_var.attributes
                for katts,vatts in atts.items():
                    try:
                        setattr(cdf_out.variables[var],katts,vatts)
                    except:
                        pass
                    if katts == '_FillValue':
                        FillVal.append(vatts)

                var_type = tmp_var.typecode()
                time_vars.append(ma.zeros(tuple(total_dims),dtype=var_type))

            cdf_out.close()   #close the output file.  reopen when needed



        for ivar,var in enumerate(lvar_proc):
            out_inds = []

            current_time = ifile*ntot_file
            out_inds.append(slice(current_time,current_time+ntot_file))

            tmp_dims = list(cdf_file.variables[var].dimensions)

            for dim in tmp_dims[1:]:
                out_inds.append(slice(0,dimensions[dim]))
        
            time_vars[ivar][out_inds] = cdf_file.variables[var].get_value()



    #reopen output file
    cdf_out = Nio.open_file(output_file,'w')

    #now average the data over time and write to the output file
    avg_vars = []
    for ivar,var in enumerate(lvar_proc):

        try:
            time_vars[ivar] = ma.masked_equal(time_vars[ivar],FillVal[ivar])
        except:
            pass
        avg_vars.append(ma.average(time_vars[ivar],axis=0))

        varout = cdf_out.variables[var]
        varout.assign_value(avg_vars[ivar])


    #cdf_out.set_option('ExplicitFillValues',FillVal)

    cdf_out.close()
    return None


if __name__ == '__main__':
    #variables to be passed in to make this a function
    run_id          = 'GSWP_gw_auto_3'
    input_directory = '/data/research/CABLE_output'
    output_directory = 'annual_avg_output'
    year_list       = [1994]


    temporal_average_netcdf(run_id,input_directory,output_directory,year_list)
