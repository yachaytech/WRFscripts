#!/bin/sh

echo "cleaning ../include"
rm -rf ../include
mkdir ../include

echo "cleaning ../lib"
rm -rf ../lib
mkdir ../lib

# Jasper is used when using GRIB2 output from WPS
# Download jasper-1.900.2.tar.gz from:
#    https://www.ece.uvic.ca/~frodo/jasper/software/jasper-1.900.2.zip
echo "installing jasper"
rm -rf jasper-1.900.2
tar xvfz jasper-1.900.2.tar.gz
cd jasper-1.900.2
./configure --prefix=/home/agrineer/wrf
make 2>&1 | tee build.txt
make install
cd ..

# Download HDF5 from the HDF5 download page.
# Go to https://www.hdfgroup.org/downloads/hdf5
# Scroll down  and click on "Specific release?"    
# download and put into the 1.10.6 tarball into wrf/packages
echo "installing HDF5"
rm -rf hdf5-1.10.6
tar xvf hdf5-1.10.6.tar.bz2
cd hdf5-1.10.6
# --disable-shared does not work for WRF compile
# has to do with jasper even if not using it.
./configure --enable-fortran --enable-hl --prefix=/home/agrineer/wrf
make 2>&1 | tee build.txt
make install
cd ..

# Download the netcdf C library from the NetCDF download page:
#    https://github.com/Unidata/netcdf-c/archive/v4.4.1.1.tar.gz
echo "installing NetCDF-4"
rm -rf netcdf-c-4.4.1.1
tar xvfz netcdf-c-4.4.1.1.tar.gz
cd netcdf-c-4.4.1.1
CPPFLAGS=-I/home/agrineer/wrf/include LDFLAGS=-L/home/agrineer/wrf/lib ./configure --disable-dap --enable-netcdf4 --prefix=/home/agrineer/wrf
make 2>&1 | tee build.txt
make install
cd ..

# Download the netcdf Fortran library from the NetCDF download page.
#    https://github.com/Unidata/netcdf-fortran/archive/v4.4.4.tar.gz
echo "installing NetCDF-4 Fortran"
rm -rf netcdf-fortran-4.4.4
tar xvfz netcdf-fortran-4.4.4.tar.gz
cd netcdf-fortran-4.4.4
LD_LIBRARY_PATH=/home/agrineer/wrf/lib CPPFLAGS=-I/home/agrineer/wrf/include LDFLAGS=-L/home/agrineer/wrf/lib FC=gfortran ./configure --prefix=/home/agrineer/wrf
make 2>&1 | tee build.txt
make install
cd ..

echo "installing libraries done."
