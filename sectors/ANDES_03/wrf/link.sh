#!/bin/sh
# bourne shell to relink to WRF directory

rm CAM_ABS_DATA; ln -s ../../../WRF/run/CAM_ABS_DATA
rm CAM_AEROPT_DATA; ln -s ../../../WRF/run/CAM_AEROPT_DATA
rm ETAMPNEW_DATA; ln -s ../../../WRF/run/ETAMPNEW_DATA
rm ETAMPNEW_DATA.expanded_rain; ln -s ../../../WRF/run/ETAMPNEW_DATA.expanded_rain
rm GENPARM.TBL; ln -s ../../../WRF/run/GENPARM.TBL
rm grib2map.tbl; ln -s ../../../WRF/run/grib2map.tbl
rm gribmap.txt; ln -s ../../../WRF/run/gribmap.txt
rm LANDUSE.TBL; ln -s ../../../WRF/run/LANDUSE.TBL
rm MPTABLE.TBL; ln -s ../../../WRF/run/MPTABLE.TBL
rm ndown.exe; ln -s ../../../WRF/run/ndown.exe
rm ozone.formatted; ln -s ../../../WRF/run/ozone.formatted
rm ozone_lat.formatted; ln -s ../../../WRF/run/ozone_lat.formatted
rm ozone_plev.formatted; ln -s ../../../WRF/run/ozone_plev.formatted
rm real.exe; ln -s ../../../WRF/run/real.exe
rm RRTM_DATA; ln -s ../../../WRF/run/RRTM_DATA
rm RRTMG_LW_DATA; ln -s ../../../WRF/run/RRTMG_LW_DATA
rm RRTMG_SW_DATA; ln -s ../../../WRF/run/RRTMG_SW_DATA
rm SOILPARM.TBL; ln -s ../../../WRF/run/SOILPARM.TBL
rm tc.exe; ln -s ../../../WRF/run/tc.exe
rm URBPARM.TBL; ln -s ../../../WRF/run/URBPARM.TBL
rm URBPARM_UZE.TBL; ln -s ../../../WRF/run/URBPARM_UZE.TBL
rm VEGPARM.TBL; ln -s ../../../WRF/run/VEGPARM.TBL
rm wrf.exe; ln -s ../../../WRF/run/wrf.exe
