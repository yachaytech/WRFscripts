#!/bin/bash
#  upload.sh 
# 
#  Copyright (C) 2019-2020 Scott L. Williams
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

# this script uploads WRF generated netcdf files to our web server

# Contributor info; do not use commas or tabs
# make sure to match with server expectation
NAME=""  # DISABLED for git release
INST=""         
EMAIL=admin@example.org

# local
TIME=06-00-00                            # UTC Time from sector location
INDIR=/students/agrineer/wrf/output          # where the data are

#------------------------------------------------------------------------

# url encode spaces
NAME=`echo $NAME | sed -e 's/ /%20/g' `
INST=`echo $INST | sed -e 's/ /%20/g' `

usage() {                             
  echo "Usage: $0 [-h] -s SECTOR -r RUNDATE" 1>&2 
}

# grab the parameters
while getopts "hs:r:" options; do
                                
    case "${options}" in
	s) SECTOR=${OPTARG} ;;
	r) RUNDATE=${OPTARG} ;;
	h) usage
	   exit 0
	   ;;
	:)                                    
	    echo "Error: -${OPTARG} requires an argument."
	    usage
	    exit 1
	    ;;
	[?])
	    usage
	    exit 1
	    ;;
	*)                                 
	    usage
	    exit 1	
	    ;;
    esac
done

shift $((OPTIND-1))

# check parameter values
if [ -z "${SECTOR}" ] || [ -z "${RUNDATE}" ]; then
    usage
    exit 1
fi

WDIR=$INDIR/$SECTOR/$RUNDATE

# check if working directory exists
if [ -z "$(ls -A $WDIR/*.nc)" ]; then
    echo "$0: Bad directory given. Either sector or run date is bad or"
    echo "$0: there is no data."
    exit 1
fi

cd $WDIR

# Compress all netcdf files
ZIPFILE=$SECTOR\_$RUNDATE.zip
echo "Zipping to file: $ZIPFILE"
/usr/bin/zip $ZIPFILE *.nc

# POST the zip file to the server.
res=`/usr/bin/curl -s -F WRFfile="@$ZIPFILE" "http://www.yachay.openfabtech.org/upload/transfer.php?sector=$SECTOR&date=$RUNDATE&time=$TIME&email=$EMAIL&name=$NAME&inst=$INST"`

# remove zip file whether upload was successful or not
#rm -f $ZIPFILE

# gotta make it a string
res="$res"   
#echo "Result: $res"

# Parse the json result string for status and description.
key1=status
key2=detail
status=`echo $res | /usr/bin/gawk -F "[,:}]" '{for(i=1;i<=NF;i++){if($i~/'$key1'\042/){print $(i+1)}}}' | tr -d '"' | sed -n ${num}p`

detail=`echo $res | /usr/bin/gawk -F "[,:}]" '{for(i=1;i<=NF;i++){if($i~/'$key2'\042/){print $(i+1)}}}' | tr -d '"' | sed -n ${num}p`

echo "Job status: $status"
echo "Job detail: $detail"

# Exit depending on status.
if [ "$status" = "success" ]; then
	exit 0
else
	exit 1
fi


