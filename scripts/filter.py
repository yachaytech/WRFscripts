#! /usr/bin/env /usr/bin/python3

#  filter.py
# 
#  Copyright (c) 2023 Scott L. Williams
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
filter_copyright = 'filter.py Copyright (c) 2023 Scott L. Williams ' + \
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

## @file      filter.py
## @brief     Selectively read WRF meta data variables and write to file
##            Make reprojectable by keeping GMT (general mapping tool ) format.
## @author    Scott L. Williams
## @copyright Copyright (c) 2018-2023 Scott L. Williams. All Rights Reserved.
## @license   Released under GNU General Public License V3.0
## @results   outputs file with selected WRF variables

##            You can use "nccopy -v TSK in7.nc out.nc" (from netCDF4)
##            but you have to first
##            convert it the input file by using "nccopy -7 in.nc in7.nc",
##            which takes a long time. Also the nccopy script will keep all 25
##            buffers of XLAT,XLONG which is unnecessary.

# print functions to reduce clutter and to flush output
def eprint( *args ):
    print( *args, file=sys.stderr, flush=True)

def oprint( *args ):
    print( *args, file=sys.stdout, flush=True)

class filterWRF():
    
    def __init__( self, inpath, outpath ):

        # hard code WRF variables to use, later implement command line string
        self.WRF_VARS = [ 'TSK','EMISS','SWDOWN','GLW','GRDFLX',
                          'T2','PSFC','Q2','U10','V10']

        # check if file names have same wrf_out_XXX_YYYY-MM-DD_VV_ZZ
        wrf_filename = os.path.basename( inpath )

        # open netcdf files
        self.wrf_ds = Dataset( inpath, 'r' )
        self.out_ds = Dataset( outpath, 'w', format='NETCDF3_CLASSIC' )

        # our attributes to have
        self.attr = [ 'TITLE',
                      'SIMULATION_START_DATE',
                      'WEST-EAST_GRID_DIMENSION',
                      'SOUTH-NORTH_GRID_DIMENSION',
                      'DX',
                      'DY',
                      'GRIDTYPE',
                      'DIFF_OPT',                
                      'KM_OPT',                
                      'GRID_FDDA',             
                      'GFDDA_INTERVAL_M',      
                      'GFDDA_END_H',           
                      'GRID_SFDDA',            
                      'SGFDDA_INTERVAL_M',     
                      'SGFDDA_END_H',          
                      'HYPSOMETRIC_OPT',       
                      'USE_THETA_M',           
                      'SMOOTH_OPTION',         
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
        self.dims = [ 'Time',
                      'DateStrLen',
                      'south_north',
                      'west_east' ]
        
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

    # out file preamble
    def initialize( self ):

        self.out_ds.description = 'Filtered WRF file. For research and educational purposes only.'
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
                                           'Filtered WRF file, processed on ' +
                                           host + '.' )

                    continue
                
                self.out_ds.setncattr( attr, self.wrf_ds.getncattr(attr) )

    # notch out unwanted dimensions from WRF output and write out
    def sift_dims( self ):

        # create dimensions
        for dim in self.wrf_ds.dimensions:
            if dim in self.dims:
                size = len( self.wrf_ds.dimensions[dim] )
                self.out_ds.createDimension( dim, size )

    # check and copy lat longs
    def copy_coord( self, var ):
        try:
            wvar = self.wrf_ds.variables[var]
        except:
            raise IOError( var + ' variable is not in WRF file' )
        
        dtype = wvar.dtype

        # 2D array
        if var=='Times':
            ds_var = self.out_ds.createVariable( var, dtype,
                                                 ('Time','DateStrLen') )
        else:
            ds_var = self.out_ds.createVariable( var, dtype,
                                           ('south_north', 'west_east') )
        # copy over variable attributes
        for ncattr in wvar.ncattrs():

            value = wvar.getncattr(ncattr)
            ds_var.setncattr( ncattr, value )

        if var=='Times':
            self.out_ds.variables[var][:,:] = wvar[:,:]
        else:
            # just one buffer, not the 25 that are present
            self.out_ds.variables[var][:,:] = wvar[0][:,:]

    # clone a netcdf variable's attributes and data
    def clone_var( self, var ):

        try:
            wvar = self.wrf_ds.variables[var]
        except:
            raise IOError( var + ' variable is not in WRF file' )
        
        dtype = wvar.dtype

        # 3-D array
        ds_var = self.out_ds.createVariable( var, dtype,
                                           ('Time','south_north', 'west_east') )
        # copy over variable attributes
        for ncattr in wvar.ncattrs():

            value = wvar.getncattr(ncattr)
            ds_var.setncattr( ncattr, value )
        
        self.out_ds.variables[var][:,:,:] = wvar[:,:,:]
                      
    # make it so
    def run( self ):

        self.initialize()

        # report WRF meta and variable data
        #self.wrf_info( self.wrf_ds, verb=False)

        # sift through input globals for attrs,dims of interests
        self.sift_attrs()
        self.sift_dims()

        # mandatory XLAT, XLONG buffers 
        self.copy_coord('XLAT')
        self.copy_coord('XLONG')
        self.copy_coord('Times')
 
        for var in self.WRF_VARS:
            
            self.clone_var( var )
            #print( self.out_ds.variables[var])
        
        # report output data
        #self.wrf_info( self.out_ds, verb=True ) 
        self.out_ds.close()
        
# end class merge    

# --------------------------------------------------------------------

# command line options
def usage():
    eprint('usage: filter.py -h -i infile -o outfile')
    eprint('       filter.py --help --in=infile --out=outfile')
  
def read_args( argv ):

    infile = None
    outfile = None
    
    try:                                
        opts, args = getopt.getopt( argv,
                                    'hi:o:', 
                                    ['help','in=','out='] )
    except getopt.GetoptError: 
        eprint('unknown command arguments')
        usage()                          
        sys.exit(2)  
                   
    for opt, arg in opts:   
        if opt in ( '-h', '--help' ): 
            usage()                     
            sys.exit(0)       
           
        elif opt in ( '-i', '--in' ):
            infile = arg  

        elif opt in ( '-o', '--out' ):
            outfile = arg  

        else:
            usage()                     
            sys.exit(0)       

    if infile == None:
        eprint( 'must specify input WRF file' )
        usage()                     
        sys.exit( 2 )
        
    if outfile == None:
        eprint( 'must specify output WRF file' )
        usage()                     
        sys.exit( 2 )

    return infile, outfile

if __name__ == '__main__':  

    infile, outfile= read_args( sys.argv[1:] ) # get input and output files

    eprint( 'Filtering', infile, 'and outputing to', outfile )
    oper = filterWRF( infile, outfile )
    oper.run() 

# end filter.py
