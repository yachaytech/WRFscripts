#!/usr/bin/python3

#  getdata_gfs.py                                                       
#                                                                               
#  Copyright (C) 2016-2020 Scott L. Williams
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

copyright = 'getdata_gfs.py Copyright (c) 2016-2020 Scott L. Williams ' + \
            'released under GNU GPL V3.0'   

import os
import sys
import time
import glob
import string
import datetime

gfshome = '/students/agrineer/wrf/gfs_0.25'

# print fuctions to reduce clutter and to flush
def eprint( *args ):
    print( *args, file=sys.stderr, flush=True)

def oprint( *args ):
    print( *args, file=sys.stdout, flush=True)

def get_analysis_data( datedir ):
	eprint("getting data for ", datedir)
	stat = os.system( 'wget -nv -nc  ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.' +
	       datedir + '/00/atmos/gfs.t00z.pgrb2.0p25.f000' )
	eprint(stat)
	stat = os.system( 'wget -nv -nc  ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.' +
	       datedir + '/06/atmos/gfs.t06z.pgrb2.0p25.f000' )
	eprint(stat)
	stat = os.system( 'wget -nv -nc  ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.' +
	       datedir + '/12/atmos/gfs.t12z.pgrb2.0p25.f000' )
	eprint(stat)
	stat = os.system( 'wget -nv -nc  ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.' +
	       datedir + '/18/atmos/gfs.t18z.pgrb2.0p25.f000' )
	eprint(stat)

########################################################
# set up date strings
ac = len(sys.argv)
if ac < 2:
	# run with current data
	today = datetime.datetime.now()
	yesterday = today - datetime.timedelta(days = 1)
else:
	# get rundate from command line
	ystdir = sys.argv[1]
	yr = int( ystdir[:4] )
	mn = int( ystdir[4:6] )
	dy = int( ystdir[6:8] )
	yesterday = datetime.date(yr,mn,dy)
	today = yesterday + datetime.timedelta(days = 1)

ystdir = yesterday.strftime( '%Y%m%d' )
tdydir = today.strftime( '%Y%m%d' )

# get yesterday's data
os.chdir( gfshome )
if os.path.exists(ystdir):
	os.chdir(ystdir) # cd into yesterday's dir
else:
	os.mkdir(ystdir)
	os.chdir(ystdir)

# get data for yesterday; overwrites previous first sets
get_analysis_data( ystdir )

# get today's data
os.chdir( gfshome )
if os.path.exists( tdydir ):
	os.chdir( tdydir ) # cd into today's dir
else:
	os.mkdir( tdydir )
	os.chdir( tdydir )

# get today's available data sets
get_analysis_data( tdydir )
