#! /usr/bin/env /usr/bin/python3

#  eto_FAO.py
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

eto_FAO_copyright = 'eto_FAO.py Copyright (c) 2018-2020 Scott L. Williams ' + \
                'released under GNU GPL V3.0'
import os
import sys
import glob
import math
import struct
import getopt
import datetime

import numpy as np
from osgeo import gdal  # uses gdal to read WRF netCDF4 file
                        # NOTE: GDC and SME packages use netCDF4 module
                        # instead of gdal
## @file      eto.py
## @brief     Calculate, according to UNs' Food and Agriculture Organization
##            (FAO), standard evapotranspiration (ETo) using Weather, 
##            Research, and  Forecasting (WRF) model data as input, accumulated
##            hourly for a day. 
## @author    Scott L. Williams
## @copyright Copyright (c) 2018-2020 Scott L. Williams. All Rights Reserved.
## @license   Released under GNU General Public License V3.0
## @results   Numpy file with ETo values.

# While WRF provides SFCEVP output variables, the approach here
# is to adhere to the recommended calculations given by the 
# FAO for standard evapotranspiration, allowing for specific control over
# variable implementation.

# In effect, the program covers the WRF domains with short green grass
# giving ETo.
# Local crop coefficients can be applied to adjust the ETo to get ETc.

# How-to-use:

# - Use data from generic WRF run over an area of interest
# - Install osgeo, numpy Python3 modules
#   eg.
#     > pip3 numpy
#     > pip3 osgeo

# - The main program section is geared toward a web server 
#   data directory structure. You can use the main section as a guide 
#   to implement your own separate main entrance design, eg. MyEto.py, 
#   and importing this eto class.

# print functions to reduce clutter and to flush output
def eprint( *args ):
    print( *args, file=sys.stderr, flush=True)

def oprint( *args ):
    print( *args, file=sys.stdout, flush=True)

## Class to calculate standard reference evaporation, ETo,
## from WRF netCDF4 data
class eto():

    ## The constructor
    ## @param report - flag to report daily vars
    ## @param infile - WRF netCDF4 output file
    ## @param outdir - output directory
    ## @param rundate - data run date (simulation target date)
    def __init__( self, report, infile, outdir, rundate ):

        self.report = report
        self.rundate = rundate # not used in this version
        
        # tag output numpy file with input data name
        bname = os.path.basename( infile ) 
        self.outfile_path = outdir + '/ETo_FAO_' + bname + '.npy'
        self.daily_vars_path = outdir + '/DailyVars_' + bname + '.npy'
        self.infile = infile

        gdal.PushErrorHandler( 'CPLQuietErrorHandler' ) # suppress warning

    ## Calculate mean hourly net radiation
    ## @param Rsd - mean hourly downward shortwave radiation
    ## @param Rld - mean hourly downward longwave radiation
    ## @param albedo - short wave reflection coefficient
    def calc_Rn( self, Rsd, Rld, tsk, emiss, albedo ):

        # Calculate net radiation
           
        # we start with naive net radiation, Rn = Rsd*(1-a) + Rld - Rlu
        # later enhancements may include additional components
        # see chp. 3 of FAO paper 56 on deriving Rlu from air temp, Ea, and
        # cloudiness. Eq. 39
 
        # NOTE: use cumulus physics option in wrf namelist.input file
        #       to reduce radiation due to cloud cover. 

        # use this operationally: net_rad = (sw_in-sw_out) + (lw_in-lw_out)
        # eg. Rn = Rsd*(1-a) + Rld - Rlu

        # calculate upward long wave radiation using Stefan-Boltzmann equation
        # with given "skin" surface temperature and emissivity values

        sigma = 5.67*10**(-8)  # SI stephan-boltzmann equation constant

        # lotta questions here:
        #   - use grass or soil emissivity?
        #   - use grass or soil skin temp?
        #   - pretending to have grass grow in sub-zero?
        #     - does penman account for dead grass? just soil evap?
        #   - use our emissivity instead of WRF emiss?
        #   - use WRF albedo or green grass?
        #   - tsk should assume soil is wet,
        #   - tsk should assume green grass cover

        # stephan-boltzmann
        # appears to have too much/little upward longwave and is
        # probably due to skin temperature not accounting for sufficient
        # moisture, and green grass cover.

        # this value is critical and is not general like the atmospheric loads
        # as skin temperature should be based on hypotetical cover and moisture.
        Rlu = emiss*sigma*(tsk**4)      # NOTE: emiss start values, time=0,
                                        #       are not consistent with
                                        #       following ones
                                        # FIXME: implement spinup time
                                        
        # also note that WRF emiss values presumably considers
        # vegetation/soil and not our specific plant (green grass)
        Rn = Rsd*(1.0 - albedo) + Rld - Rlu  # radiation toward surface is +
                                             # radiation away from surface is -

        # convert (J/s)/m^2 to  (MJ/(m^2 * hr)
        return Rn/(10**6) * 3600.0

    ## Calculate slope of saturation vapor curve, D
    ## @param Thc - Temperature array C
    def calc_D( self, Thc ):
        
        # Eq. 13 FAO paper 56
        num = 4098.0*(0.6108*np.exp(17.27*Thc/(Thc+237.3)))
        denom = (Thc+237.3)**2

        return num/denom

    ## Calculate psychrometric constant, g
    ## @param P - pressure array in Pascals
    def calc_g( self, P ):
        
        # P is in Pascals
        # Eq. 8 FAO paper 56
        return 0.000665*P/1000.0 # return kPa/C

    ## Calculate saturation pressure at some temperature C
    ## @param Thc - Temperature array C
    def calc_es( self, Thc ):
        
        # Eq. 11 FAO paper 56
        return 0.6108*np.exp(17.27*Thc/(Thc+237.3))
 
    # Calculate relative humidity
    # gives same values as below
    def calc_Rh1( self, Q2, T2, PSFC ):

    #https://archive.eol.ucar.edu/projects/ceop/dm/documents/refdata_report/eqns.html

        TC = T2 - 273.16    # make celsius; per FAO 273.16, not 273.15
        press = 0.01*PSFC   # make millibar

        es = 611.2 * np.exp( (17.67*TC)/(TC + 243.5 ) )
        ea = (Q2*PSFC) / (Q2+0.622 )
        
        Rh = ea/es
        
        return Rh
        
    ## Calculate relative humidity
    ## @param q2 - specific humidity (mixing ratio kg/kg)
    ## @param t2 - temperature at 2m height (K)
    ## @param psfc - surface pressure (Pascal)
    def calc_Rh( self, q2, t2, psfc ):
        # NOTE: can't seem to find or generate relative humidity from WRF!
        #       see README notes for source
        #       update: see above
        # calculate RH
        pq0 = 379.90516
        a2 = 17.2693882
        a3 = 273.16
        a4 = 35.86

        f_rh2 = q2 / ( (pq0 / psfc) * np.exp(a2 * (t2 - a3) / (t2 - a4)) )
        f_rh2 = np.clip( f_rh2, 0.0, 1.0 )

        return f_rh2

    ## Convert wind speed from given height to 2 meters
    def convert_wind( self, w, h ):
        factor = 4.87/math.log(67.8*h - 5.42)  # Eq. 47 FAO paper No.56
        return w*factor
    
    ## Calculate wind speed magnitude from given height to 2 meters
    def calc_ws2( self, u, v, h ):
        u2 = self.convert_wind( u, h )
        v2 = self.convert_wind( v, h )

        mag = np.sqrt(u2*u2 + v2*v2)  # wind speed (magnitude)
        return mag

    ## Prepare a data array for calculating eto
    def prep_eto( self, source, hour ):

        # check data type
        if source.dtype != np.float32:
            eprint( 'wrong data type, should be float32' )
            sys.exit( 2 )

        albedo = 0.23    # for short green grass FIXME: make variable
        numy,numx,nbands = source.shape # get dimensions

        # input bands (0,1 indicate first and second bookends for
        #              a time slice)
        # TSK_0        surface skin temperature (K)                band 0
        # TSK_1                                                    band 1
        # EMISS_0      surface emissivity                          band 2
        # EMISS_1                                                  band 3
        # SWDOWN_0     downward shortwave at ground (W/m^2)        band 4
        # SWDOWN_1                                                 band 5
        # GLW_0        downward longwave at ground (W/m^2)         band 6
        # GLW_1                                                    band 7
        # GRDFLX_0     ground heat flux (W/m^2)                    band 8
        # GRDFLX_1                                                 band 9
        # T2_0         temp at 2m (K)                              band 10
        # T2_1                                                     band 11
        # PSFC_0       surface pressure (Pa)                       band 12
        # PSFC_1                                                   band 13
        # Q2_0         QV (water vapor mixing ratio) at 2m (kg/kg) band 14
        # Q2_1                                                     band 15
        # U10_0        wind speed U at 10m (m/s)                   band 16
        # U10_1                                                    band 17
        # V10_0        wind speed V at 10m (m/s)                   band 18
        # V10_1                                                    band 19     
        # XLAT                                                     band 20
        # XLONG                                                    band 21
        
        # sample wrf_source input string for 10:00-11:00hrs :
        # TSK:10,TSK:11,EMISS:10,EMISS:11,SWDOWN:10,SWDOWN:11,GLW:10,GLW:11,GRDFLX:10,GRDFLX:11,T2:10,T2:11,PSFC:10,PSFC:11,Q2:10,Q2:11,U10:10,U10:11,V10:10,V10:11,XLAT:0,XLONG:0
        if nbands != 22:  
            eprint('source wrong band size, should be 22 got: ', nbands)
            return

        # allocate output space; include lat and long
        sink = np.empty( (numy,numx,11), dtype=np.float32 )

        # average skin temperatures and emissivities
        tsk = (source[:,:,0] + source[:,:,1])/2.0
        emiss = (source[:,:,2] + source[:,:,3])/2.0
        
        # average the short and long radiation time slice endpoints, W/m^2
        Rsd = (source[:,:,4] + source[:,:,5])/2.0
        Rld = (source[:,:,6] + source[:,:,7])/2.0

        # calculate mean hourly net radiation, returns MJ/(m^2*hr)
        sink[:,:,0] = self.calc_Rn( Rsd, Rld, tsk, emiss, albedo )

        # average the ground flux
        G = (source[:,:,8] + source[:,:,9])/2.0
        sink[:,:,1] = G/(10**6) * 3600  # convert (J/s)/m^2 to  MJ/(m^2*hr)
        
        # average the temps (K)
        Thk = (source[:,:,10] + source[:,:,11])/2.0
        sink[:,:,2] = Thk - 273.16 # make Celsius 

        # calculate D, saturation slope vapor pressure curve 
        sink[:,:,3] = self.calc_D( sink[:,:,2] )

        # average the surface pressure, (Pascal)
        P = (source[:,:,12] + source[:,:,13])/2.0

        # calculate g psychrometric, kPa/C, from surface pressure
        sink[:,:,4] = self.calc_g( P )

        # average the mixing ratio (specific humidity) (kg/kg)
        Q2 = (source[:,:,14] + source[:,:,15])/2.0

        # es, saturation vapor pressure at Thc
        sink[:,:,5] = self.calc_es( sink[:,:,2] )

        # calculate relative humidity
        sink[:,:,6] = self.calc_Rh( Q2, Thk, P )
            
        # ea, actual vapor pressure, ea = es*Rh
        sink[:,:,7] = sink[:,:,5] * sink[:,:,6]

        # calculate wind speed
        # average the 10m wind speeds
        # and convert to 2m speed; m/s

        '''
        # discriminate between day and night time to address
        # WRF nocturnal bias in urban areas
        if hour > 7 and hour < 19:
            U10 = (source[:,:,16] + source[:,:,17])/2.0
            V10 = (source[:,:,18] + source[:,:,19])/2.0
            sink[:,:,8] = self.calc_ws2( U10, V10, 10.0 )
        else:
            sink[:,:,8] = 1.2
        '''

        # above condition is a hueristic fix for a deficiency in
        # the current WRF wind speed expressions. The WRF model tends
        # to increase significantly the nocturnal wind speeds rather
        # than decreasing them. If this model bias is
        # persistent in future releases, consider a more accurate approach for
        # conciliation.

        '''
        # gives higher wind speeds than below
        U10 = (source[:,:,16] + source[:,:,17])/2.0
        V10 = (source[:,:,18] + source[:,:,19])/2.0
        sink[:,:,8] = self.calc_ws2( U10, V10, 10.0 )
        '''

        #'''
        # start wind time slice
        U2 = self.convert_wind( source[:,:,16], 10.0 )
        V2 = self.convert_wind( source[:,:,17], 10.0 )
        WS_start = np.sqrt( U2*U2 + V2*V2 )
        
        # end wind time slice
        U2 = self.convert_wind( source[:,:,18], 10.0 )
        V2 = self.convert_wind( source[:,:,19], 10.0 )
        WS_end = np.sqrt( U2*U2 + V2*V2 )

        sink[:,:,8] = (WS_start + WS_end)/2.0
        #'''
        
        # set output lat and log buffers
        sink[:,:,9] = source[:,:,20]
        sink[:,:,10] = source[:,:,21]

        return sink

    ## Calculate ETo using eq. 53 in Chapter 4 from FAO paper #56 hourly example
    ## http://www.fao.org/docrep/X0490E/x0490e08.htm
    ## @param Rn  - net radiation, MJ/(m**2*hr) eq.40
    ## @param G   - soil flux,MJ/(m**2*hr) eq.45,46
    ## @param Thc - mean hourly air temperature, C
    ## @param D   - saturation slope vapour pressure curve at Thc, kPa/C, eq. 13
    ## @param g   - psychrometric, kPa/C, eq.8
    ## @param es  - saturation vapor pressure at Thc,kPa,eq.11
    ## @param ea  - average hourly actual vapor pressure, kPa, eq.54
    ## @param w2  - average hourly wind speed at 2m, m/s
    def calc_et_ref( self, Rn, G, Thc, D, g, es, ea, w2 ): 

        # calculate numerator from eq.53 FAO
        num_a = 0.408*D*(Rn-G)
        num_b = g*(37.0/(Thc+273.16))
        num_c = w2*(es-ea)

        num = num_a + num_b*num_c

        # calculate denominator from eq.53
        denom = D + g*(1 + 0.34*w2)

        eto = num/denom                # get ETo values

        return( eto.clip( 0.0, None) ) # no negative values

        # FAO hourly method can give negative values. These likely
        # indicate surface dew. Experience (comparisons) indicates 
        # clipping negative values gives better alignment with daily
        # interval calculation

    ## Calculate ETo and put into data buffer
    def calc_eto( self, source ):
        
        # check data type
        if source.dtype != np.float32:
            eprint( 'wrong data type, should be float32')
            return

        numy,numx,nbands = source.shape # get dimensions

        # input bands:
        # Rn     hourly averaged net radiation flux,       MJ/(m**2*hr)
        # G      hourly averaged ground heat flux,         MJ/(m**2*hr)
        # Thc    hourly averaged temperature,              C
        # D      saturation slope vapor pressure curve,    kPa/C
        # g      psychrometric from mean surface pressure, kPa/C
        # es,    saturation vapor pressure at Thc,         kPa
        # Rh,    relative humidity                         %
        # ea,    actual vapor pressure,                    kPa
        # w2,    wind speed,                               m/s
        # lat    latitude,                                 decimal degrees
        # long   longitude,                                decimal degrees

        if nbands != 11:  
            eprint('wrong band size, should be 11, got:', nbands)
            sys.exit(2)

        # allocate output space; include lat and long
        sink = np.empty( (numy,numx,3), dtype=np.float32 )

        # calculate domain ETo (mm) and make it an output band
        sink[:,:,0 ] = self.calc_et_ref( source[:,:,0],
                                         source[:,:,1],
                                         source[:,:,2],
                                         source[:,:,3],
                                         source[:,:,4],
                                         source[:,:,5],    # Rh not needed
                                         source[:,:,7],
                                         source[:,:,8] )
        
        # set output lat and lon buffers
        sink[:,:,1] = source[:,:,9]
        sink[:,:,2] = source[:,:,10]

        return sink

    def str2list( self, s ): 

        bufs = []
        tbands = []               # time bands

        vars = s.split(',')          

        nbufs = len( vars )
 
        for x in vars:
            items = x.split(':')
            bufs.append( items[0] )
            tbands.append( int(items[1]) )

        return nbufs, bufs, tbands

    ## populate a numpy array from wrf output file
    ## according to bandstr
    def read_wrf( self, infile, bandstr ):

        # decode bandstr for band and time slices
        nbufs, bufs,tbands = self.str2list( bandstr )
        time_steps = 25

        # grab data from wrf output
        for i in range(0,nbufs):

            bufstr = 'NETCDF:"' + infile + '":' + bufs[i]
            try:
                ds = gdal.Open( bufstr )
            except:
                eprint('cannot get dataset:', bufs[i])
                return

            if tbands[i] < 0 or tbands[i] >= time_steps:
                # FIXME: raise exception
                eprint('bad time index:', tbands[i])
                return

            data = ds.ReadAsArray()[ tbands[i] ]
            
            # make output buffer for starters
            if i == 0:
                # save values to compare later
                numy = data.shape[0]
                numx = data.shape[1]
                dtype = data.dtype 

                sink = np.empty( (numy,numx,nbufs), dtype=dtype )

            sink[:,:,i] = data #  stash data in output array

        return sink 

    # calculate daily variable output values
    # for quality control and analysis
    def report_daily_vars( self, i, daily_vars, eto_vars ):
            
        # max and min hourly mean temps
        if i == 0:
            daily_vars[:,:,0] = eto_vars[:,:,2] # initialize max temp
            daily_vars[:,:,1] = eto_vars[:,:,2] # initialize min temp
        else:
            # compare element wise for max and mins
            daily_vars[:,:,0] = np.maximum( eto_vars[:,:,2],
                                            daily_vars[:,:,0] )
            daily_vars[:,:,1] = np.minimum( eto_vars[:,:,2],
                                            daily_vars[:,:,1] )

        # max and min hourly mean relative humidity
        if i == 0:
            daily_vars[:,:,2] = eto_vars[:,:,6] # initialize max Rh
            daily_vars[:,:,3] = eto_vars[:,:,6] # initialize min Rh
        else:
            # compare element wise for max and mins
            daily_vars[:,:,2] = np.maximum( eto_vars[:,:,6],
                                            daily_vars[:,:,2] )
            daily_vars[:,:,3] = np.minimum( eto_vars[:,:,6],
                                            daily_vars[:,:,3] )
                
        daily_vars[:,:,4] += eto_vars[:,:,8]/24 # accumulate averaged wind speed
        daily_vars[:,:,5] += eto_vars[:,:,0]    # accumulate net solar rad

    ## Read wrf buffers, generate timeslice parameters and process
    def read_and_run( self ):
        #print( 'eto working...' )

        # generate band input string to extract buffers from wrf netCDF output.
        # bookend entries i, i+1 is for mean hourly value calculation.
        for i in range(0,24):
            bandstr =  'TSK:'    + str(i)   + \
                      ',TSK:'    + str(i+1) + \
                      ',EMISS:'  + str(i)   + \
                      ',EMISS:'  + str(i+1) + \
                      ',SWDOWN:' + str(i)   + \
                      ',SWDOWN:' + str(i+1) + \
                      ',GLW:'    + str(i)   + \
                      ',GLW:'    + str(i+1) + \
                      ',GRDFLX:' + str(i)   + \
                      ',GRDFLX:' + str(i+1) + \
                      ',T2:'     + str(i)   + \
                      ',T2:'     + str(i+1) + \
                      ',PSFC:'   + str(i)   + \
                      ',PSFC:'   + str(i+1) + \
                      ',Q2:'     + str(i)   + \
                      ',Q2:'     + str(i+1) + \
                      ',U10:'    + str(i)   + \
                      ',U10:'    + str(i+1) + \
                      ',V10:'    + str(i)   + \
                      ',V10:'    + str(i+1) + \
                      ',XLAT:0,XLONG:0'

            source = self.read_wrf( self.infile, bandstr )
            if i == 0:
                # allocate output buffers now that we know dimensions
                numy = source.shape[0]
                numx = source.shape[1]
                eto = np.zeros( (numy,numx), dtype=np.float32 )
                if self.report:
                    daily_vars = np.zeros( (numy,numx,8), dtype=np.float32 )

            # source nows holds bandstr bookend 
            # values for i-th time slice            
            eto_vars = self.prep_eto( source, i ) # prepare variables
                                                  # for eto calculations.
            values = self.calc_eto( eto_vars )    # calculate ETo.
            
            # eto buffer accumulates every hour
            eto[:,:] += values[:,:,0]             # values band 0 holds.
                                                  # hourly ETo values.
            # report daily values.
            if self.report:
                self.report_daily_vars( i, daily_vars, eto_vars )         

        # end hourly for loop

        np.save( self.outfile_path, eto )
        
        if self.report:

            # report accumulated eto for daily vars also
            daily_vars[:,:,6] = eto[:,:]

            # report WRF accumulated potevp
            # first read the buffer
            bufstr = 'NETCDF:"' + self.infile + '":' + 'SFCEVP'
            ds = gdal.Open( bufstr )

            # get last hour value (accumulated) and convert to mm
            data = ds.ReadAsArray()[24]
            if type( data ) is not np.ndarray:
                eprint('cannot get dataset:', 'SFCEVP')
                return

            daily_vars[:,:,7] = data[:,:] # kg/m^3 = mm ?

            # SFCEVP units Kg/m^2. using cm^3=1e-6m^3 & 1kg water= 1000cm^3
            # 1000*1e-6m^3/m^2 = 0.001m; 1000mm=1m -> 0.001*1000=1

            np.save( self.daily_vars_path, daily_vars )
        
        #print( 'done.' )
    
# end class eto

# ---------------------------------------------------------------------------

#outdir = '/extra/SMVdata/archive'
outdir = '/students/agrineer/wrf/output'

# command line options
def usage():
    eprint('usage: eto_FAO.py -h -d -s sector <-r date> ')
    eprint('       eto_FAO.py --help --daily --sector=sector <--rundate=date>')
    eprint("       omitting rundate parameter defaults to yesterday's date")
  
# end usage

def read_args( argv ):

    report = False
    rundate = None
    sector = None

    try:                                
        opts, args = getopt.getopt( argv,
                                    'hds:r:', 
                                    ['help','daily','sector=','rundate='])
    except getopt.GetoptError: 
        eprint('unknown command arguments')
        usage()                          
        sys.exit(2)  
                   
    for opt, arg in opts:   
        if opt in ( '-h', '--help' ): 
            usage()                     
            sys.exit(0)
            
        elif opt in ( '-d', '--daily' ): 
            report = True
           
        elif opt in ( '-s', '--sector' ):
            sector = arg  

        elif opt in ( '-r', '--rundate' ):
            rundate = arg  

    if sector == None:
        usage()                     
        sys.exit( 2 )

    return report, rundate, sector

# end read_args

if __name__ == '__main__':  

    # get report daily flag, run date and domain sector
    report, rundate, sector = read_args( sys.argv[1:] ) 
    if rundate == None:
        
        # run with yesterday's data
        today = datetime.datetime.now() # local time
        yesterday = today - datetime.timedelta(days = 1)
        rundate = yesterday.strftime( "%Y%m%d" )

    # go to working directory
    indir = outdir + '/' + sector + '/' + rundate

    # check if working dir exists
    if not os.path.isdir( indir ):
        eprint('directory:', indir, 'does not exist')
        sys.exit(2) 

    # check directory permissions
    if not os.access( indir, os.W_OK ):
        eprint('cannot write to directory:', indir)
        sys.exit(2) 

    os.chdir( indir )

    # process all available domains in directory
    for f in glob.glob( 'wrfout_d*' ):
    
        eprint('calculating ETo for', f + '.') 
        oper = eto( report, f, '.', rundate )
        
        oper.read_and_run()                  

# end eto.py
