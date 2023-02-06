#!/usr/bin/python3

#  run_wrfgfs.py                                                             
#                                                                               
#  Copyright (C) 2016-2022 Scott L. Williams                                   
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

copyright = 'run_wrfgfs.py Copyright (c) 2016-2022 Scott L. Williams ' + \
            'released under GNU GPL V3.0'
import os
import sys
import glob
import time
import getopt
import shutil
import datetime

# set dirs  
# FIXME: implement environment variable?
outdir = '/students/agrineer/wrf/output/'
script_dir = '/students/agrineer/wrf/scripts/'

# print fuctions to reduce clutter and to flush
def eprint( *args ):
    print( *args, file=sys.stderr, flush=True)

def oprint( *args ):
    print( *args, file=sys.stdout, flush=True)

# command line options
def usage():
    eprint('usage: run_wrfgfs.py -h -b hour -s sector -d datapath <-r date>')
    eprint('       run_wrfgfs.py --help --begin=hour --sector=sector --datadir=datapath <--rundate=date>')
    eprint('       omitting rundate defaults to yesterday data')
    eprint('       begin hour is in UTC')

# end usage

def read_args( argv ):

    sector = None
    rundate = None
    begin = None
    datadir = None

    try:                                
        opts, args = getopt.getopt( argv, 'hb:s:d:r:', 
                                    ['help','begin=','sector=','datadir=',
                                     'rundate='] )
    except getopt.GetoptError: 
        eprint('unkown command arguments')
        usage()                          
        sys.exit(2)  
                   
    for opt, arg in opts:   
        if opt in ( '-h', '--help' ): 
            usage()                     
            sys.exit(0)       
           
        elif opt in ( '-s', '--sector' ):
            sector = arg  

        elif opt in ( '-d', '--datadir' ):
            datadir = arg  

        elif opt in ( '-r', '--rundate' ):
            rundate = arg  

        elif opt in ( '-b', '--begin' ):   # REVIEW: this is not general enough
                                           #         only works for 00,06,12,18
            begin = int(arg)
            if begin < 0 or begin > 23:
                eprint('begin hour must be [00-23],')
                usage()                     
                sys.exit( 2 )

    if sector == None:
        eprint('must have sector name.')
        usage()                     
        sys.exit( 2 )

    if begin == None:
        eprint('must have start hour (UTC).')
        usage()                     
        sys.exit( 2 )

    if datadir == None:
        eprint('must have input data directory.')
        usage()                     
        sys.exit( 2 )

    return sector, rundate, begin, datadir

# end read_args

if __name__ == '__main__':  

    # get run date and domain sector
    sector, rundate, begin, datadir = read_args( sys.argv[1:] ) 

    # NOTE: begin time does not work below (still true?)
    
    # run wrf and data extraction

    eprint('running wrfGFS on', sector + '.')

    if rundate == None:
    
        # figure out yesterday's date
        today = datetime.datetime.now() # local time
        yesterday = today - datetime.timedelta(days = 1)
        rundate = yesterday.strftime( "%Y%m%d" )

    # run the WRF script
    status = os.system( script_dir + 'wrfGFS.py -s ' + 
                        sector + ' -b ' + '%02d'%begin +
                        ' -d ' + datadir + ' -r ' + rundate )
    # check return status
    if status != 0:
        eprint('wrfGFS failed.')
        sys.exit(2)

    eprint('wrfGFS completed.')

    # post-processing

    # go to working directory
    wdir = outdir + sector + '/' + rundate
    os.chdir( wdir )

    for f in glob.glob( 'wrfout_d*' ):
    
        newfile = f.replace( ':', '-' ) # replace ':' with '-' 
                                        # because gdal cannot 
                                        # parse netcdf filenames
                                        # containing ':'
        os.rename( f, newfile )

    ''' DISABLED for git release
    # run ETo calculations for this sector
    eprint('running ETo script on', sector,'for date', rundate + '.')

    status = os.system( script_dir + 'eto_FAO.py -s ' + sector +
                        ' -r ' + rundate )
    if status != 0:
        eprint('ETo failed.')
        sys.exit(2)
    eprint('ETo script completed.')

    eprint('running ETo WRF merge script on', sector, 
          'for date', rundate + '.')

    status = os.system( script_dir + 'merge.py -s ' + sector +
                        ' -r ' + rundate )
    if status != 0:
        eprint('merge failed.')
        sys.exit(2)
    eprint('merge completed.')

    # remove ETo*.npy files
    os.chdir( wdir )
    for f in glob.glob( 'ETo*.npy' ):
        os.remove( f )

    '''
    # should move these files offline, but can be too expensive to store
    # depending WRF Registry variable output.
    # for now zap domains 1 and 2, keep domain 3 (3.3km) for future analysis 
    for f in glob.glob( 'wrfout_d0[1-2]*' ):
        os.remove( f )

    ''' DISABLED for git release
    # upload to web server
    status = os.system( script_dir + 'upload.sh -s ' + sector +
                        ' -r ' + rundate )
    if status != 0:
        eprint('upload failed.')
        sys.exit(2)

    eprint('upload completed.')
    '''
    
    os.chdir( outdir + sector )
    time.sleep(5)    # attempt to make tar more robust; 
                     # tar seems to fail occasionally; crontab connected?
    eprint( "tar'ing output files" )
    status = os.system( 'tar cvfz ' + rundate + '.tar.gz ' + rundate )
    if status != 0:
        eprint('tarball failed.')
        sys.exit(2)
    eprint('tarball completed.')

    try:
        shutil.rmtree( rundate )
    except OSError as e:
        eprint('could not remove:',rundate)
        sys.exit( 2 )

    eprint('RUN COMPLETED SUCCESSFULLY for sector:', sector + ',', 
          'rundate:', rundate + '.')

# end run_wrfgfs.py
