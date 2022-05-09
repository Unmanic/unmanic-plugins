#!/bin/bash
# -
# File: install-nodejs.sh
# Project: plugins
# File Created: 04 May 2022, 8:03 AM
# Author: josh5
# -----
# Last Modified: 04 May 2022, 8:03 AM
# Modified By: josh5
# -

# Script is executed by the Unmanic container on startup to auto-install dependencies

jhead_dl_url="https://www.sentex.ca/~mwandel/jhead/jhead"

if ! command -v jhead &> /dev/null; then
    echo "**** Installing Exif Jpeg ****"
    curl -kSL -o /usr/bin/jhead "${jhead_dl_url}"
    chmod +x /usr/bin/jhead
else
    echo "**** Exif Jpeg already installed ****"
fi
if ! command -v jpegtran &> /dev/null; then
    echo "**** Installing jpegtran ****"
    [[ "${__apt_updated:-false}" == 'false' ]] && apt-get update && __apt_updated=true
    apt-get install -y libjpeg-progs
else
    echo "**** jpegtran already installed ****"
fi
if ! command -v exiftran &> /dev/null; then
    echo "**** Installing ExifTool ****"
    [[ "${__apt_updated:-false}" == 'false' ]] && apt-get update && __apt_updated=true
    apt-get install -y exiftran
else
    echo "**** Exiftran already installed ****"
fi
