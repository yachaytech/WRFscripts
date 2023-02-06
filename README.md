This project gives the code and scripts needed to run WRF/ARW on an automated basis and was used to generate the input WRF data used in the "eto_climate" project. Essentially, once everything is configured correctly, just two programs, "getdata_gfs.py" and "run_wrf", are needed to generate the WRF data. 

It is a work in progress.

The top directory holds the needed scripts to run WRF.

It should look like:

bin         gfs_0.25  lib  output    README.md          run_wrf_configure  sector_geos  share  WPS_GEOG     
Dockerfile  include   log  packages  run_wps_configure  scripts            sectors      WPS    WRF

Most directories have a README.txt for guidance.

Briefly:

First, install the needed packages from the "packages" directory and this will populate the bin,lib, include, and share directories.

Next, install WPS/WRF programs from UCAR, and these go into the WPS and WRF directories.
Use the "run_wps_configure" and "run_wrf_configure" to install WPS/WRF.

The "sector_geos" script can be used to populate each sector defined with the static geographical data.

A docker container file is included as a guide to the install necessary packages.

This project is not turn-key, as it requires modifications for local implementation.

It is necessary to review and edit the scripts, if needed. Large data directories, like "gfs_0.25", "WPS_GEOG", and "output" can be linked to disks that can accomodate the data.





