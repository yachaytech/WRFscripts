This directory holds the high level scripts to run WRF.

It should look like this:
eto_FAO.py  getdata_gfs.py  merge.py  README.txt  run_wrf  run_wrfgfs.py  upload.sh  wrfGFS.py

----------------------------------------------------------------------------------------

to get daily GFS files use:
> ./getdata_gfs.py

or to specify a date use:
> ./getdata_gfs.py YYYYMMDD

to run WRF on a sector and date use:
> ./run_wrf SECTOR YYYYMMDD

NOTE: Be aware that the GFS repository only holds 10 days worth of data.
To get archived data you must use the rda.ucar.edu dataset ds084.1
For the re-analyzed data search for "f000", download the file and rename. (TODO: put howto here)

Put a link in your ~/bin to getdata_gfs.py and run_wrf for easy access.

NOTE: the scripts eto_FAO.py, upload.sh, and merge.py are disabled for the git release.
      these scripts are used to update a web server program, see yachay.openfabtech.org

Also, the script wrfGFS.py specifies the number of cores to use. There are two ways depending on platforms.

For automated daily runs use a cronfile:

35 04 * * * (export LD_LIBRARY_PATH=/usr/lib; /students/agrineer/wrf/scripts/getdata_gfs.py)

00 01  * * * ( /students/agrineer/bin/run_wrf ANDES_03 20220501 )
00 03  * * * ( /students/agrineer/bin/run_wrf ANDES_03 20220502 )
00 05  * * * ( /students/agrineer/bin/run_wrf ANDES_03 20220503 )
00 07  * * * ( /students/agrineer/bin/run_wrf ANDES_03 20220504 )
00 09  * * * ( /students/agrineer/bin/run_wrf ANDES_03 20220505 )
00 11  * * * ( /students/agrineer/bin/run_wrf ANDES_03 20220506 )
00 13  * * * ( /students/agrineer/bin/run_wrf ANDES_03 20220507	)
00 15  * * * ( /students/agrineer/bin/run_wrf ANDES_03 20220508 )
00 17  * * * ( /students/agrineer/bin/run_wrf ANDES_03 20220509 )
00 19  * * * ( /students/agrineer/bin/run_wrf ANDES_03 20220510 )
00 21  * * * ( /students/agrineer/bin/run_wrf ANDES_03 20220511 )
00 23  * * * ( /students/agrineer/bin/run_wrf ANDES_03 20220512 )

you will need to update the rundates daily.


