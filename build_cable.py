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

#Code to build CABLE using a Makefile.
#can be run from anywhere as long as the source_dir of the CABLE code is provided
import copy
import os
import sys
import subprocess
import shutil
import errno
import time
from collections import OrderedDict
#if build clean then need to
# rm -fr .mpitmp
class build_model(object):
    def __init__(self,**kwargs):
                 #libraries=None,\
                 #source_dir=None,\
                 #build_directory=None,\
                 #compile_flags=None, \
                 #switches=None):
        #choose reasonable defaults if the required info isn't passed to constructor

        switches = {}
        user_args={}
        if kwargs is not None:
           for key,val in kwargs.iteritems():
              user_args[key.lower()] = val

        build_libs = user_args.get('libraries',['/share/apps/intel/Composer/lib/intel64'])
        self.build_libs = ''.join(build_libs)

        for switch_key in ['mpi','clean','debug']:  
           switches[switch_key] = user_args.get(switch_key,False)

        self.source_dir  = user_args.get('source_dir','.')
        self.build_dir   = user_args.get('build_dir',self.source_dir)

        compile_flags  = user_args.get('fcflags','-O2 -fp-model precise'.split(' '))
        self.build_flags   = [' '+flg for flg in compile_flags]

        self.compiler = user_args.get('compiler','ifort')

        self.all_source_dirs = [os.path.join(self.source_dir,direct) for direct in ['core/biogeophys','offline','core/biogeochem']]
        
        self.excluded_params = user_args.get('skipped_params','cable_runtime')
        self.master_namelist='master_cable.nml'

        if switches['mpi']:                                                            #define mpi/serial vairables
            self.compiler  = 'mpif90'
            self.make_file = 'Makefile_mpi'
            self.target    = 'cable-mpi'
            self.makefile_target    = 'cable-mpi'
            self.tmp_build_dir = '.mpi'
        else:
            self.make_file = 'Makefile_offline' 
            self.target    = 'cable'
            self.makefile_target    = 'cable'
            self.tmp_build_dir = '.tmp'

        if switches['debug']:
           compile_flags = ' -O0 -g -traceback -check all -debug all' 
           self.build_flags   = [' '+flg for flg in compile_flags.split(' ')]
           self.tmp_build_dir = self.tmp_build_dir+'_debug'
           self.target += '-debug'

        try:                                                                                    #read NETCDF_DIR to get the netcdf directory
            netcdf_dir = os.environ['NETCDF']
        except:
            netcdf_dir = '/usr/local'
            print ("""NETCDF environmental variable is not set. 
                     Assuming netcdf resides in /usr/local""")

        self.netcdf_inc = os.path.join(netcdf_dir,'include')
        self.netcdf_lib = os.path.join(netcdf_dir,'lib')

        if not os.path.isdir(self.build_dir): 
            try:
                os.mkdir(self.build_dir)
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise
                pass


        self.tmp_build_dir = os.path.join(self.build_dir,self.tmp_build_dir)

        if os.path.isdir(self.tmp_build_dir):
            if switches['clean']:
                subprocess.call(["rm","-rf",self.tmp_build_dir])
 

        if not os.path.isdir(self.tmp_build_dir): 
            try:
                os.mkdir(self.tmp_build_dir)
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise
                pass

    def gen_svn_info(self,cmd):

        tmp_file = '.tmp_file'
        subprocess.call('svn '+cmd+' > '+tmp_file,shell=True)#,'>'+self.svn_diff_file])
    
        f=open(tmp_file,'r')

        svndata=f.read().split('\n')
        f.close()
            
        if bool(self.svn_info):
           self.svn_info=[]

        if not bool(self.svn_info[cmd]):
           del self.svn_info[cmd]

        self.svn_info[cmd]={}

        for l in svndata:
           l=l.strip()
           if ':' in l:
              a=l[0:l.index(':')]
              b=l[l.index(':')+2:]
                  
              a=a.replace(' ','_')
              b=b.replace(' ','_')
              try:
                self.svn_info[cmd][a]=b
              except:
                pass

        if not bool(self.svn_info[cmd]):
           os.rmfile(self.tmp_file)
        else:
           print(' DID NOT YEILD ANY INFORMATION'.format(cmd))
    
                

    def make_the_model(self):
        #build everything in .mpitmp/  then use mv .mpitmp . to move to current directory
        #basic routine for building with mpi
        #Move everything to the temporary build directory
        #Must be a better way than doing this three times......
        src_path_files = []
        #below searches for all F90 files.  Copies them all to the temporary directory
        #note this copies mpi files even when we don't build with mpi

        source_files = []
        for direct in self.all_source_dirs:
            for tmp_files in os.listdir(direct):
                if tmp_files.endswith(".F90"):
                    source_files.append(tmp_files)
                    src_path_files.append(os.path.join(direct,tmp_files))
            
        for n,x in enumerate(src_path_files):
            if os.path.isfile(x):
                if not os.path.isfile(os.path.join(self.tmp_build_dir,source_files[n])):
                    shutil.copy2(x, self.tmp_build_dir)

        #need to set a bunch of environmental variables
        os.environ['NCDIR'] = self.netcdf_lib#'/share/apps/netcdf/intel/4.1.3/lib'
        os.environ['NCMOD'] = self.netcdf_inc#'/share/apps/netcdf/intel/4.1.3/include'
        os.environ['FC'] = self.compiler#'mpif90'
        os.environ['CFLAGS'] = ''.join(self.build_flags)

        os.environ['LD'] = '-lnetcdf -lnetcdff'
        os.environ['LDFLAGS'] = '-L'+self.build_libs+' -L'+self.netcdf_lib+' '.join(self.build_flags)
        #                       '-L/share/apps/intel/Composer/lib/intel64 -L/share/apps/netcdf/intel/4.1.3/lib  -O2'

        os.chdir(self.source_dir)
        timestr = time.strftime("%Y%m%d%H%M%S")
        self.svn_diff_file = 'svn.diff'
        self.svn_info_file = 'svn.info'
        self.readme= "readme"

        #subprocess.call(['svn diff > '+self.source_dir,shell=True])#,'>'+self.svn_diff_file])
        subprocess.call('svn diff > '+self.svn_diff_file,shell=True)#,'>'+self.svn_diff_file])
        

        store_target = self.target+'_'+timestr

        os.chdir(self.tmp_build_dir)
        for src_dir in self.all_source_dirs:
           fils = os.listdir(src_dir)
           for fil in fils:
              if fil.endswith("90") or fil.startswith("Make"):
                 shutil.copy2(os.path.join(src_dir,fil),os.path.join(self.tmp_build_dir,fil))

        #
        subprocess.call(['make','-f',self.make_file])
        shutil.move(self.makefile_target,self.target)

        shutil.copy(self.target,os.path.join(self.source_dir,store_target))
        shutil.copy(self.target,os.path.join(self.build_dir,self.target))


if __name__ == '__main__':

    my_args = {}
    my_args['source_dir']='/srv/ccrc/data22/z3362708/CABLE/CMIP6-GM2_dev_testing_tiles'
    my_args['debug']=True
    my_args['mpi']=True

    CABLE = build_model(**my_args)
    CABLE.build_parameter_list()
    






