#! /usr/bin/env /usr/bin/python3

'''
@run_filter.py
@author Scott L. Williams.
@package WRF
@brief filter WRF data sets for data size reduction
@LICENSE
# 
#  Copyright (C) 2023 Scott L. Williams.
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
#
'''


run_filter_copyright = 'run_filter.py Copyright (c) 2023 Scott L. Williams, released under GNU GPL V3.0'

import os
import sys
import glob
import getopt

# point to data directories
datapath = '/output/ecuador/ANDES_03/'  # point to WRF output data
outpath = '/output/ecuador/ANDES_03-filtered/'
filterpath = '/home/agrineer/wrf/scripts/filter.py'

# ----------------------------------------------------------------------------
# main

# check if input/output data directories exists
if not os.path.isdir( datapath ):
    print( 'run_filter:', datapath, ' does not exist...exiting',
           file=sys.stderr )
    sys.exit( 1 )
        
if not os.path.isdir( outpath ):
    os.mkdir( outpath )
    if not os.path.isdir( outpath ):
        print( 'run_filter:', outpath, ' cannot be made...exiting',
               file=sys.stderr )
        sys.exit( 1 )

os.chdir( outpath ) # work from here

prefix_size = len( datapath )

# run through all files in datapath with "tar.gz" suffix
tarfiles = glob.glob( datapath + '*.tar.gz' )
for f in tarfiles:

    # get the name of the date folder (YYYYMMD)
    folder = f[prefix_size:-7] 
    out_prefix = outpath + folder + '/'
    out_prefix_size = len( out_prefix )
        
    # check if folder already exists
    if os.path.isdir( outpath + folder ):        
        print( outpath+folder, ' already exists...exiting',
               file=sys.stderr )
        sys.exit( 1 )

    # untar the WRF file to the output directory
    print( 'untar\'ing ' + datapath + folder + '.tar.gz', 'to', outpath[:-1],
           file=sys.stderr )
    
    result = os.system( 'tar xzf ' + datapath + folder + '.tar.gz' )
    if result == 1:
        print( 'run_filter: cannot untar ' + f + ' exiting...',
               file=sys.stderr )
        sys.exit( 1 )
    
    wrffile = glob.glob( out_prefix + 'wrfout*' )[0] # returns array, use only first
    outfile = out_prefix + wrffile[out_prefix_size:] + '-filtered'

    # filter the WRF file
    #print( 'filtering:', outfile )
    
    result = os.system( filterpath + ' -i ' + wrffile + ' -o ' + outfile )
    if result == 1:
        print( 'run_filter: cannot filter ' + wrffile + ' exiting...',
               file=sys.stderr )
        sys.exit( 1 )

    # rename filtered file (clobbers unfiltered file)
    result = os.system( 'mv ' + outfile + ' ' + wrffile )
    if result == 1:
        print( 'run_filter: cannot rename ' + outfile + ' exiting...',
               file=sys.stderr )
        sys.exit( 1 )

    # tar renamed filtered file
    print( 'tar\'ing ./' + wrffile[-39:], file=sys.stderr )
    result = os.system( 'tar cfz ' + wrffile[-30:] + '.tar.gz ' + './' + wrffile[-39:] )
    if result == 1:
        print( 'run_filter: cannot tar ' + wrffile + ' exiting...',
               file=sys.stderr )
        sys.exit( 1 )

    # remove date directory
    for f in glob.glob( folder + '/*' ):
        os.remove( f )
    os.rmdir( folder  )
    print( '-----------------------------------------------------------\n' )
