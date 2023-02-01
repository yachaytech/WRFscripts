#! /usr/bin/env /usr/bin/python3

#  merge.py
# 
#  Copyright (c) 2018-2020 Scott L. Williams
# 
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#  or visit https://www.gnu.org/licenses/gpl-3.0-standalone.html
# 
merge_copyright = 'merge.py Copyright (c) 2018-2020 Scott L. Williams ' + \
                 'released under GNU GPL V3.0'

import os
import sys
import glob
import time
import getopt
import socket
import datetime

import numpy as np
from netCDF4 import Dataset

## @file      merge.py
## @brief     Selectively read WRF output meta and data variables 
##            (lat, long, min max temp, daily accumulated rain) used for ETo
##            calculation then merge the output ETo data.
##            Make reprojectable by keeping GMT (general mapping tool ) format.
## @author    Scott L. Williams
## @copyright Copyright (c) 2018-2020 Scott L. Williams. All Rights Reserved.
## @license   Released under GNU General Public License V3.0
## @results   netCDF4 file w/TMAX,TMIN,ETo,SFCEVP bands

# print functions to reduce clutter and to flush output
def eprint( *args ):
    print( *args, file=sys.stderr, flush=True)

def oprint( *args ):
    print( *args, file=sys.stdout, flush=True)

class merge():

    def __init__( self, wrf_path, eto_path, out_path, latlongs ):

        # check if file names have same wrf_out_XXX_YYYY-MM-DD_VV_ZZ
        wrf_filename = os.path.basename( wrf_path )
        if wrf_filename in eto_path:
            self.eto_path = eto_path
        else:
            raise IOError( 'ETo filename must contain input WRF filename' )

        # include latlongs?
        self.latlongs = latlongs

        # open netcdf files
        self.wrf_ds = Dataset( wrf_path, 'r' )
        self.out_ds = Dataset( out_path, 'w', format='NETCDF3_CLASSIC' )

        # our attributes, per WRF
        self.attr = [ 'TITLE',
                      'SIMULATION_START_DATE',
                      'WEST-EAST_GRID_DIMENSION',
                      'SOUTH-NORTH_GRID_DIMENSION',
                      'DX',
                      'DY',
                      'GRIDTYPE',
#                      'DIFF_OPT',                
#                      'KM_OPT',                
#                      'GRID_FDDA',             
#                      'GFDDA_INTERVAL_M',      
#                      'GFDDA_END_H',           
#                      'GRID_SFDDA',            
#                      'SGFDDA_INTERVAL_M',     
#                      'SGFDDA_END_H',          
#                      'HYPSOMETRIC_OPT',       
#                      'USE_THETA_M',           
#                      'SMOOTH_OPTION',         
                      'WEST-EAST_PATCH_START_UNSTAG',
                      'WEST-EAST_PATCH_END_UNSTAG',
                      'WEST-EAST_PATCH_START_STAG',
                      'WEST-EAST_PATCH_END_STAG',
                      'SOUTH-NORTH_PATCH_START_UNSTAG',
                      'SOUTH-NORTH_PATCH_END_UNSTAG',
                      'SOUTH-NORTH_PATCH_START_STAG',
                      'SOUTH-NORTH_PATCH_END_STAG',
                      'CEN_LAT',
                      'CEN_LON',
                      'TRUELAT1',
                      'TRUELAT2',
                      'MOAD_CEN_LAT',
                      'STAND_LON',
                      'POLE_LAT',
                      'POLE_LON',
                      'GMT',
                      'JULYR',
                      'JULDAY',
                      'MAP_PROJ',
                      'MAP_PROJ_CHAR' ]

        # our dimensions, per WRF
        self.dims = [ 'west_east',
                      'south_north',
                      'west_east_stag',
                      'south_north_stag' ]

    def print_ncattr( self, key, nc_fid ):

        try:
            eprint('\t\ttype:', repr(nc_fid.variables[key].dtype))

            for ncattr in nc_fid.variables[key].ncattrs():
                eprint('\t\t%s:' % ncattr,
                      repr( nc_fid.variables[key].getncattr(ncattr) ))
        except KeyError:
            eprint("\t\tWARNING: %s does not contain variable attributes" % key)

    def wrf_info( self, nc_fid, verb=True ):
        # derived from code by Chris Slocum,NetCDF with Python

        # NetCDF global attributes
        nc_attrs = nc_fid.ncattrs()
        if verb:
            eprint("NetCDF Global Attributes:")
            for nc_attr in nc_attrs:
                eprint('\t%s:' % nc_attr, repr(nc_fid.getncattr(nc_attr)))

        nc_dims = [dim for dim in nc_fid.dimensions]  # list of nc dimensions

        # dimension shape information.
        if verb:
            eprint("NetCDF dimension information:")
            for dim in nc_dims:
                eprint("\tName:", dim)
                eprint("\t\tsize:", len(nc_fid.dimensions[dim]))
                self.print_ncattr( dim, nc_fid )

        # variable information.
        nc_vars = [var for var in nc_fid.variables]  # list of nc variables
        if verb:
            eprint("NetCDF variable information:")
            for var in nc_vars:
                if var not in nc_dims:
                    eprint('\tName:', var)
                    eprint("\t\tdimensions:", nc_fid.variables[var].dimensions)
                    eprint("\t\tsize:", nc_fid.variables[var].size)
                    self.print_ncattr( var, nc_fid )

        return nc_attrs, nc_dims, nc_vars

    # clone a netcdf variable
    def clone_var( self, outkey, inkey ):

        wvar = self.wrf_ds.variables[inkey]
        dtype = wvar.dtype 
        ds_var = self.out_ds.createVariable( outkey, dtype, 
                                             ('south_north', 'west_east') )
        # copy over variable attributes
        for ncattr in wvar.ncattrs():

            if ncattr == 'coordinates':
                ds_var.setncattr( ncattr, 'XLONG XLAT' ) # remove time dimension
            else:
                value = wvar.getncattr(ncattr)
                ds_var.setncattr( ncattr, value )
                        
        return ds_var

    # out file preamble
    def initialize( self ):

        self.out_ds.description = 'Calculated daily soil moisture variables (SMV) based on hourly samples from the WRF model.  For research and educational purposes only.'
        self.out_ds.history = 'File created on ' + time.ctime(time.time()) + '.'
        self.out_ds.source = 'Data courtesy of Yachay Tech University, Ecuador, and Agrineer.org. For research and educational purposes only.'

    # notch out unwanted global attributes from WRF output and write out
    def sift_attrs( self ):

        for attr in self.wrf_ds.ncattrs():
            if attr in self.attr:

                # intercept title
                if attr == 'TITLE':
                    host = socket.gethostname()
                    self.out_ds.setncattr( attr, 
                                           'Soil Moisture Variables (SMV) based on WRF V4.2, processed on ' +
                                           host + '.' )

                    continue
                    
                self.out_ds.setncattr( attr, 
                                       self.wrf_ds.getncattr(attr) )

    # end sift attrs

    # notch out unwanted dimensions from WRF output and write out
    def sift_dims( self ):

        # create dimensions
        for dim in self.wrf_ds.dimensions:
            if dim in self.dims:
                size = len( self.wrf_ds.dimensions[dim] )
                self.out_ds.createDimension( dim, size )

    # check and copy lat longs
    def copy_latlong( self ):

        wvars = self.wrf_ds.variables

        if 'XLAT' not in wvars:
            raise IOError( '"XLAT" variable is not in WRF file' )

        if 'XLONG' not in wvars:
            raise IOError( '"XLONG" variable is not in WRF file' )

        self.clone_var( 'XLAT','XLAT' )
        self.out_ds.variables['XLAT'][:] = wvars['XLAT'][0]

        self.clone_var( 'XLONG','XLONG' )
        self.out_ds.variables['XLONG'][:] = wvars['XLONG'][0]

    # make PRECIP variable
    def make_precip( self ):

        wvars = self.wrf_ds.variables

        if 'RAINC' not in wvars:
            raise IOError( '"RAINC" variable is not in WRF file' )

        if 'RAINNC' not in wvars:
            raise IOError( '"RAINNC" variable is not in WRF file' )

        # extract accumulated rains and add
        ac_rainc = wvars['RAINC'][24]          # 0-index
        ac_rainnc = wvars['RAINNC'][24]
        ac_rain = ac_rainc + ac_rainnc

        # TODO: factor snow precip with SNOWNC variable
        
        # make PRECIP variable
        precip = self.clone_var( 'PRECIP','RAINC' )
        precip.setncattr( 'description', 'DAILY PRECIPITATION, mm' )
        self.out_ds.variables['PRECIP'][:] = ac_rain

        return precip
        
    # make SFCEVP variable
    def make_sfcevp( self ):

        wvars = self.wrf_ds.variables

        if 'SFCEVP' not in wvars:
            raise IOError( '"SFCEVP" variable is not in the WRF file' )

        # extract accumulated surface evaporation
        ac_sfcevp = wvars['SFCEVP'][24]          # 0-index
      
        # make SFCEVP variable
        sfcevp = self.clone_var( 'SFCEVP','RAINC' )
        sfcevp.setncattr( 'description', 'ACCUMULATED SURFACE EVAPORATION, mm' )
        self.out_ds.variables['SFCEVP'][:] = ac_sfcevp

    # load standard evaporation data from numpy file
    def load_eto( self, shape ):

        etobuf = np.load( self.eto_path )         # load from file 

        # check compatibility
        if etobuf.shape != shape:
            eprint('ETo and WRF input files have incompatible shapes')
            eprint('ETo:', etobuf.shape, 'WRF:', precip.shape)
            raise IOError( 'bad shapes' )

        # make ETo variable
        eto = self.clone_var( 'STDEVP','RAINC' )
        eto.setncattr( 'description', 
                       'DAILY STANDARD REFERENCE EVAPORATION, mm' )

        # insert data value
        self.out_ds.variables['STDEVP'][:] = np.flipud( etobuf[:] )

    # make daily temperature min, max variables
    def make_temps( self ):

        wvars = self.wrf_ds.variables

        if 'T2' not in wvars:
            raise IOError( '"T2" variable is not in WRF file' )

        # allocate and initialize min, max buffers
        tmin = wvars['T2'][0]
        tmax = tmin

        # get hourly temps and compare
        for i in range(1,25):

            tmin = np.minimum( tmin, wvars['T2'][i] )
            tmax = np.maximum( tmax, wvars['T2'][i] )

        tmin -= 273.15
        tmax -= 273.15

        # make temp variables
        tmin_var = self.clone_var( 'TMIN','T2' )
        tmin_var.setncattr( 'description', 'DAILY MINIMUM TEMP at 2m, C' )
        tmin_var.setncattr( 'units', 'C' )
        self.out_ds.variables['TMIN'][:] = tmin

        tmax_var = self.clone_var( 'TMAX','T2' )
        tmax_var.setncattr( 'description', 'DAILY MAXIMUM TEMP at 2m, C' )
        tmax_var.setncattr( 'units', 'C' )
        self.out_ds.variables['TMAX'][:] = tmax

    # make it so
    def run( self ):

        self.initialize()

        # report WRF meta and variable data
        #self.wrf_info( self.wrf_ds, verb=False)

        # sift through input globals for attrs,dims of interests
        self.sift_attrs()
        self.sift_dims()

        # calculate total rain and make new variable PRECIP
        precip = self.make_precip()

        # load ETo data and make new variable STDEVP
        self.load_eto( precip.shape )

        # find daily temp mins and maxs, used to calulate growing degree days.
        self.make_temps()

        # merge the SFCEVP variable for comparisons
        self.make_sfcevp()
        
        # copy lat,long variables.
        # default is False.
        # since static geo files have the lat,long we ommit them
        # here to save space.
        if self.latlongs:
            self.copy_latlong()

        # report output data
        #self.wrf_info( self.out_ds, verb=True ) 
        self.out_ds.close()

# end class merge    

# --------------------------------------------------------------------

# command line options
def usage():
    eprint('usage: merge.py -h -s sectorname <-l True/False> <-r date>')
    eprint('       merge.py --help --sector=sectorname <--latlongs=True/False> <--rundate=date>')
    eprint('       omitting rundate defaults to yesterday data')
  
def read_args( argv ):

    rundate = None
    sector = None
    latlongs = False

    try:                                
        opts, args = getopt.getopt( argv,
                                    'hs:l:r:', 
                                    ['help','sector=','latlongs=','rundate='])
    except getopt.GetoptError: 
        eprint('unknown command arguments')
        usage()                          
        sys.exit(2)  
                   
    for opt, arg in opts:   
        if opt in ( '-h', '--help' ): 
            usage()                     
            sys.exit(0)       
           
        elif opt in ( '-s', '--sector' ):
            sector = arg  

        elif opt in ( '-l', '--latlongs' ):
            if arg in ['True','False']:
                latlongs = arg
            else:
                usage()                     
                sys.exit(0)       
           
        elif opt in ( '-r', '--rundate' ):
            rundate = arg  

    if sector == None:
        usage()                     
        sys.exit( 2 )

    return rundate, sector, latlongs

# return days to use from date
def get_days( date ):

    if date == None:

        # run with yesterday's data
        today = datetime.datetime.now() # local time
        yesterday = today - datetime.timedelta(days = 1)

    else:

        ystdir = date
        yr = int( ystdir[:4] )
        mn = int( ystdir[4:6] )
        dy = int( ystdir[6:8] )
        yesterday = datetime.date(yr,mn,dy)
        today = yesterday + datetime.timedelta(days = 1)

    return yesterday, today

if __name__ == '__main__':  

    outdir = '/students/agrineer/wrf/output'

    rundate, sector, l = read_args( sys.argv[1:] ) # get run date, domain sector
    yesterday,today = get_days( rundate )          # parse dates from run date

    # date data directory
    ystdir = yesterday.strftime( "%Y%m%d" )

    # go to working directory
    indir = outdir + '/' + sector + '/' + ystdir   # construct path

    # check if working dir exists
    if not os.path.isdir( indir ):
        eprint('directory:', indir, 'does not exist')
        sys.exit(2) 

    # check directory permissions
    if not os.access( indir, os.W_OK ):
        eprint('cannot write to directory:', indir)
        sys.exit(2) 

    os.chdir( indir )

    # process all domains
    for w in glob.glob( 'wrfout_d*' ):
    
        eprint('merging ETo data with', w)
        oper = merge( w, 'ETo_FAO_' + w + '.npy', sector + '_SMV' + w[6:] + '.nc',
                      l )
        oper.run() 

# end merge.py
