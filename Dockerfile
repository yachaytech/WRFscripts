#  Dockerfile for Agrineer.org's WRF_container image
#  Copyright (C) 2018-2020 Scott L. Williams
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
#  or visit https://www.gnu.org/licenses/gpl-3.0-standalone.htm

# get base Mint image
FROM linuxmintd/mint20-amd64
MAINTAINER Scott L. Williams

# TODO: put build-essential, m4

# get preliminary goodies
RUN apt-get -y update \
    && apt-get -y dist-upgrade \
    && apt-get -y install \
       apt-utils \
       bash-completion \
       cron \
       curl \
       emacs \
       gawk \
       iputils-ping \
       net-tools \
       time \
       vim-common \
       vim-tiny \
       zip \
    && apt-get -y autoremove

# get WRF dependencies
RUN apt-get -y install \
    csh \
    gfortran \
    libpng-dev \
    mpich \
    ncview \
    python3-gdal \
    python3-netcdf4 \
    zlib1g-dev

# *** ADJUST TIME ZONE ***
# *** ENTER YOUR TIME ZONE HERE ***
RUN rm /etc/localtime && ln -s /usr/share/zoneinfo/America/Bogota /etc/localtime

# create user agrineer and start to populate directory
#RUN useradd -d /home/agrineer -m agrineer -s /bin/bash
#RUN rm -rf /home/agrineer
ADD agrineer /home/agrineer
#RUN chown -R agrineer.agrineer /home/agrineer
RUN chown -R root.root /home/agrineer

# become user agrineer
#USER agrineer

# install WRF external libraries
WORKDIR /home/agrineer/wrf/packages
RUN ./INSTALL_LIBS.sh

# make input and output directories
WORKDIR /home/agrineer/wrf
RUN mkdir gfs_0.25 log output 

# get UCAR-BSD License and place in /home/agrineer/wrf
RUN curl -SL https://ral.ucar.edu/sites/default/files/public/projects/ncar-docker-wrf/ucar-bsd-3-clause-license.pdf > UCAR-BSD-3-Clause-License.pdf

# get current WRF source
RUN git clone https://github.com/wrf-model/WRF

# get current WPS source
RUN git clone https://github.com/wrf-model/WPS

# it is necessary first to modify Registry files in order to reduce output data
# NOTE: should you want the default output (about 2.4GB/domain)
#       comment out the registry copy below
# NOTE: container agrineer/wrf/Registry does not match current version
#RUN cp -Rp Registry Registry.ORG && cp ../Registry/* Registry

# if small chenges, just fix registry directly
WORKDIR /home/agrineer/wrf/WRF/Registry
RUN ../../fix_registry

# set up environment variables and build WRF first
WORKDIR /home/agrineer/wrf/WRF
RUN ../run_wrf_configure

# next build WPS
WORKDIR /home/agrineer/wrf/WPS
RUN ../run_wps_configure

# get static geo files, WPS_GEOG (about 30-40 minutes)
# Note: there are work-arounds not to download static geo file
# everytime a container is being defined 
# involving persistent volumes and separate data installation. For now ...     
WORKDIR /home/agrineer/wrf
RUN curl -SLO http://www2.mmm.ucar.edu/wrf/src/wps_files/geog_high_res_mandatory.tar.gz \
   && tar xvfz geog_high_res_mandatory.tar.gz \
   && rm geog_high_res_mandatory.tar.gz

WORKDIR /home/agrineer/wrf/WPS_GEOG
RUN curl -SLO http://www2.mmm.ucar.edu/wrf/src/wps_files/topo_gmted2010_30s.tar.bz2 \
   && tar xvf topo_gmted2010_30s.tar.bz2 \
   && rm topo_gmted2010_30s.tar.bz2

RUN curl -SLO http://www2.mmm.ucar.edu/wrf/src/wps_files/modis_landuse_20class_30s.tar.bz2 \
   && tar xvf modis_landuse_20class_30s.tar.bz2 \
   && rm modis_landuse_20class_30s.tar.bz2

# populate sector geo directories
WORKDIR /home/agrineer/wrf
RUN ./sector_geos

# become root for login
USER root
WORKDIR /root
