#!/usr/bin/python3

#  wrfGFS.py hindcast version
# 
#  Copyright (C) 2017-2022 Scott L. Williams
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

copyright = 'wrfGFS.py Copyright (c) 2016-2022 Scott L. Williams ' + \
            'released under GNU GPL V3.0'

# gfs wrf run 

import os
import sys
import glob
import time
import getopt
import datetime

# FIXME: consider making these arguments or env variables
domain_dir = '/students/agrineer/wrf/sectors' 
lock_dir = '/students/agrineer/wrf/log'
out_dir = '/students/agrineer/wrf/output'

#------------------------------------------------------------------

# print fuctions to reduce clutter and to flush
def eprint( *args ):
    print( *args, file=sys.stderr, flush=True)

def oprint( *args ):
    print( *args, file=sys.stdout, flush=True)

# print out exit message and clean up log file
def print_and_exit( outstr ):
    eprint( outstr )
    sys.exit(2)

# end print_exit

# command line options
def usage():
    eprint('usage: wrfGFS.py -h -b hour -s sectorname -d datapath <-r date> ')
    eprint('       wrfGFS.py --help --begin=hour --sector=sectorname --datadir=datapath <--rundate=date>')
    eprint('       omitting rundate defaults to yesterday data')
    eprint('       begin hour is in UTC')
  
# NOTE:  if -b hour is not 06, 12, 18, 00; 
#        ungrib.exe tries to interpolate input FILE:XXXXXXXX's but
#        appears to have a bug

def read_args( argv ):

    sector = None
    rundate = None
    begin = None
    datadir = None

    try:                                
        opts, args = getopt.getopt( argv,
                                    'hb:s:d:r:', 
                                    ['help','begin=','sector=','datadir=','rundate='])
    except getopt.GetoptError: 
        eprint('unkown command arguments')
        usage()                          
        sys.exit(2)  
                   
    for opt, arg in opts:   
        if opt in ( '-h', '--help' ): 
            usage()                     
            sys.exit( 2 )       
           
        elif opt in ( '-s', '--sector' ):
            sector = arg  

        elif opt in ( '-d', '--datadir' ):
            datadir = arg  

        elif opt in ( '-r', '--rundate' ):
            rundate = arg  

        elif opt in ( '-b', '--begin' ):
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
        eprint('must have input data directory')
        usage()                     
        sys.exit( 2 )

    return sector, rundate, begin, datadir

# return days to use from date
def get_days( date ):

    if date == None:

        # run wrf with yesterday's data
        today = datetime.datetime.now() # local time
        yesterday = today - datetime.timedelta(days = 1)

    else :

        ystdir = date
        yr = int( ystdir[:4] )
        mn = int( ystdir[4:6] )
        dy = int( ystdir[6:8] )
        yesterday = datetime.date(yr,mn,dy)
        today = yesterday + datetime.timedelta(days = 1)

    return yesterday, today

# check data files exists
def check_data_exists( gfs_dir, ystdir, tdydir):

    # yesterday's data
    dir = gfs_dir + '/' + ystdir
    if os.path.exists( dir ):
        if not os.path.isfile( dir + '/gfs.t00z.pgrb2.0p25.f000' ):
            print_and_exit( 'data missing for ' + 
                            dir + ': gfs.t00z.pgrb2.0p25.f000' )
        if not os.path.isfile( dir + '/gfs.t06z.pgrb2.0p25.f000' ):
            print_and_exit( 'data missing for ' + 
                            dir + ': gfs.t06z.pgrb2.0p25.f000' )
        if not os.path.isfile( dir + '/gfs.t12z.pgrb2.0p25.f000' ):
            print_and_exit( 'data missing for ' + 
                            dir + ': gfs.t12z.pgrb2.0p25.f000' )
        if not os.path.isfile( dir + '/gfs.t18z.pgrb2.0p25.f000' ):
            print_and_exit( 'data missing for ' + 
                            dir + ': gfs.t18z.pgrb2.0p25.f000' )
    else :
        print_and_exit( 'data directory missing for ' + dir )

    # today's data
    dir = gfs_dir + '/' + tdydir
    if os.path.exists( dir ):
        if not os.path.isfile( dir + '/gfs.t00z.pgrb2.0p25.f000' ):
            print_and_exit( 'data missing for ' + 
                            dir + ': gfs.t00z.pgrb2.0p25.f000' )
        if not os.path.isfile( dir + '/gfs.t06z.pgrb2.0p25.f000' ):
            print_and_exit( 'data missing for ' + 
                            dir + ': gfs.t06z.pgrb2.0p25.f000' )
    else :
        print_and_exit( 'data directory missing for '+ dir )

# remove old temp files
def clean_wps_dir( sector_dir ):

    # go to WPS dir
    os.chdir( sector_dir + '/wps')

    # must already be in WPS directory

    for f in glob.glob( 'GFS*' ):
        os.remove( f )
    for f in glob.glob( 'GRIBFILE*' ):
        os.remove( f )
    for f in glob.glob( 'FILE*' ):
        os.remove( f )
    for f in glob.glob( 'met_em.d0*' ):
        os.remove( f )

# create new namelist.wps file from ORG with this run's dates
def new_wps_namelist( yesterday, today, begin ):

    # must already be in WPS directory

    if os.path.isfile( 'namelist.wps.old' ):
        os.remove( 'namelist.wps.old' )

    if os.path.isfile( 'namelist.wps' ):
        os.rename( 'namelist.wps', 'namelist.wps.old' )

    fin = open( 'namelist.wps.org', 'r' )
    fout = open( 'namelist.wps', 'w' )

    format = '%Y-%m-%d_' + '%02d'%begin + ':00:00' # has to have colons for WRF
    sd = yesterday.strftime( format ) 
    ed = today.strftime( format )

    for line in fin :
        if line.find( 'start_date' ) != -1:
            fout.write( " start_date = '" + sd + "', '" + 
                        sd + "', '" + sd + "',\n")
        elif line.find( 'end_date' ) != -1:
            fout.write( " end_date   = '" + ed + "', '" + 
                        ed + "', '" + ed + "',\n")
        elif line.find( 'interval_seconds' ) != -1:
            fout.write( " interval_seconds = 21600,\n" ) # 6hr input data
        else:
            fout.write( line )

    fout.close()
    fin.close()

def ungrib():

    # assume geogrid.exe has been run

    # check for previous ungrib log
    if os.path.isfile( 'ungrib.log' ):
        os.remove( 'ungrib.log' )

    # ungrib and check results
    status = os.system( './ungrib.exe' )
    if status == 0:

        fin = open( 'ungrib.log', 'r' )
        for line in fin:
            if line.find( 'Successful completion of program ungrib.exe') != -1:
                eprint( line )        # found
                fin.close()
                return
        fin.close()

    # not found
    ostr='UNSuccessful completion of program ungrib.exe, check ungrib.log file'
    print_and_exit( ostr )

# run metgrid
def metgrid():

    # check for previous metgrid log
    if os.path.isfile( 'metgrid.log' ):
        os.remove( 'metgrid.log' )

    status = os.system( './metgrid.exe' )
    if status == 0:
        fin = open( 'metgrid.log', 'r' )
        for line in fin:
            if line.find('Successful completion of program metgrid.exe' ) != -1:
                eprint( line )
                fin.close()
                return
        fin.close()

    # not found
    ostr = 'UNSuccessful completion of program metgrid.exe, check metgrid.log file'
    print_and_exit( ostr )

# create namelist from ORG with this run's dates
def new_namelist( yesterday, today, begin ):

    # edit namelist.input.ORG
    syr = yesterday.strftime( '%Y, ' )
    smn = yesterday.strftime( '%m, ' )
    sdy = yesterday.strftime( '%d, ' )
    shr = '%02d'%begin + ', '

    eyr = today.strftime( '%Y, ' )
    emn = today.strftime( '%m, ' )
    edy = today.strftime( '%d, ' )
    ehr = shr

    if os.path.isfile( 'namelist.input.old' ) :
        os.remove( 'namelist.input.old' )

    if os.path.isfile( 'namelist.input' ) :
        os.rename( 'namelist.input','namelist.input.old' )

    fin = open( 'namelist.input.org', 'r' )
    fout = open( 'namelist.input', 'w' )

    #FIXME: depends on num of sectors
    for line in fin :
        if line.find( 'run_hours' ) != -1 :
            fout.write( ' run_hours = 24,\n' )
        elif line.find( 'start_year' ) != -1 :
            fout.write( ' start_year = ' + syr + syr + syr + '\n' )
        elif line.find( 'start_month' ) != -1 :
            fout.write( ' start_month = ' + smn + smn + smn + '\n' )
        elif line.find( 'start_day' ) != -1 :
            fout.write( ' start_day = ' + sdy + sdy + sdy + '\n' )
        elif line.find( 'start_hour' ) != -1 :
            fout.write( ' start_hour = ' + shr + shr + shr + '\n' )
        elif line.find( 'end_year' ) != -1 :
            fout.write( ' end_year = ' + eyr + eyr + eyr + '\n' )
        elif line.find( 'end_month' ) != -1 :
            fout.write( ' end_month = ' + emn + emn + emn + '\n' )
        elif line.find( 'end_day' ) != -1 :
            fout.write( ' end_day = ' + edy + edy + edy + '\n' )
        elif line.find( 'end_hour' ) != -1 :
            fout.write( ' end_hour = ' + ehr + ehr + ehr + '\n' )
        elif line.find( 'interval_seconds' ) != -1 :
            fout.write( ' interval_seconds = 21600\n' ) # 6hr input data
        #elif line.find( 'num_metgrid_levels' ) != -1 :
        #    fout.write( ' num_metgrid_levels                  = 27\n' )
        else :
            fout.write(line)

    fout.close()
    fin.close()

def clean_wrf_dir( sector_dir, rsl ):

    # go to WRF dir
    os.chdir( sector_dir + '/wrf')

    # remove old status files
    for f in glob.glob( 'rsl.out*' ):
        os.remove( f )

    if ( rsl ):
        for f in glob.glob( 'rsl.error.*' ):
            os.remove( f )

    # remove any old output files
    for f in glob.glob( 'wrfout_d0*' ):
        os.remove( f )

    for f in glob.glob( 'met_em.d0*' ):
        os.remove( f )

    for f in glob.glob( 'wrfbdy_d0*' ):
        os.remove( f )

    for f in glob.glob( 'wrfinput_d0*' ):
        os.remove( f )

    for f in glob.glob( '*rsl.log' ):
        os.remove( f )

def run_real():

    status = os.system( './real.exe' )
    if status == 0:
        fin = open( 'rsl.out.0000', 'r' )
        for line in fin :
            if line.find( 'SUCCESS COMPLETE REAL_EM' ) != -1:
                eprint( line )  # found
                fin.close()
                return

        fin.close()

    ostr = 'UNSuccessful completion of program real.exe, check rsl.error.0000'
    print_and_exit( ostr )
    
def run_wrf( ystdir ):

    nnodes = 2              # slurm implementation
    ntasks = 4
    ncores = nnodes*ntasks  # mpich implementation

    # now run wrf.exe
    #os.system( 'salloc -N %d --exclude=imbabura0086 --ntasks-per-node %d /usr/bin/mpiexec ./wrf.exe'%(nnodes,ntasks) )
    os.system( 'salloc -N %d --ntasks-per-node %d /usr/bin/mpiexec ./wrf.exe'%(nnodes,ntasks) )
    #os.system( '/usr/bin/mpiexec -hostfile /home/agrineer/mpd.hosts -n %d ./wrf.exe'%ncores )
    
    # gather success reports into file
    os.system( 'grep "SUCCESS COMPLETE WRF" rsl.error.* > '+ystdir+ 'rsl.log' )

    # should see SUCCESS from each core, just count
    fin = open( ystdir + 'rsl.log', 'r' )
 
    # check each line, ignore artifacts if any
    nfound = 0              # number of found successes
    for line in fin:
        if line.find( 'SUCCESS COMPLETE WRF' ) != -1:
            nfound += 1     # found a success
    fin.close()
 
    if nfound != ncores:
        ostr = 'UNsuccessful completion of program wrf.exe ' + \
               datetime.datetime.now().isoformat()
        print_and_exit( ostr )

    ostr = 'Successful completion of program wrf.exe ' + \
           datetime.datetime.now().isoformat()
    
    eprint( ostr )

#####################################################################

# Program start

# get domain sector, run date, begin hour, and input data dir
sector, rundate, begin, gfs_dir = read_args( sys.argv[1:] ) 
yesterday,today = get_days( rundate )     # parse dates from run date

# use these data directories
ystdir = yesterday.strftime( "%Y%m%d" )
tdydir = today.strftime( "%Y%m%d" )
sector_dir = domain_dir + '/' + sector

check_data_exists( gfs_dir, ystdir, tdydir ) # see if data is there

# if not already running wrf on this sector then set lock file

# check for previous run
lockpath = lock_dir + '/running_' + sector + '.lock'
if os.path.isfile( lockpath ) :
    print_and_exit('wrf already running or crashed.')
else :
    try:
        lockfile = open( lockpath,'w' )
    except:
        print_and_exit( 'unable to set lock file, exiting...' )

# do file housekeeping in case of earlier abort
clean_wps_dir( sector_dir )
clean_wrf_dir( sector_dir, True )

# start processing
ostr = 'Starting run at ' + datetime.datetime.now().isoformat()
eprint( ostr )

ostr = 'Using input data directory: ' + gfs_dir
eprint( ostr )

ostr = 'Running wps/wrf on ' + sector + ' for ' + ystdir + '.'
eprint( ostr )

ostr = ' Changing directory to: ' + sector_dir + '/wps'
eprint( ostr )

os.chdir( sector_dir + '/wps' )
new_wps_namelist( yesterday, today, begin )

ddir = gfs_dir + '/'
gdirs = ddir + ystdir + '/* ' + ddir + tdydir + '/* '
os.system( './link_grib.csh ' + gdirs ) # link gribfiles

# ready to run wps routines
eprint( 'running ungrib...' )
ungrib()

eprint( 'running metgrid...' )
metgrid()

ostr = 'Changing directory to: ' + sector_dir + '/wrf'
eprint( ostr )

os.chdir( '../wrf' )
os.system( 'ln -s ../wps/met_em.d0* .' ) 
new_namelist( yesterday, today, begin )

eprint( 'running real.exe...' )
run_real()

eprint( 'running wrf.exe...' )
run_wrf( ystdir )

# store output files 
out = out_dir + '/' + sector + '/' + ystdir 
if not os.path.exists( out ):
    os.makedirs( out )

os.system( 'mv wrfout_d0* ' + out )

# do file housekeeping
clean_wps_dir( sector_dir )
clean_wrf_dir( sector_dir, False ) # False retains rsl.error files
                                   # for later inspection
                                   
ostr = 'Run complete ' + datetime.datetime.now().isoformat()
eprint( ostr )

# remove lock file
lockfile.close()
os.remove( lockpath )
