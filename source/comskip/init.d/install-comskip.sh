#!/bin/bash
# -
# File: install-comskip.sh
# Project: plugins
# File Created: 28 September 2021, 8:03 AM
# Author: josh5
# -----
# Last Modified: 04 December 2025, 6:15 PM
# Modified By: josh5
# -

# Script is executed by the Unmanic container on startup to auto-install dependencies

if ! command -v comskip &> /dev/null || [[ $(( $(comskip 2>&1 | head -1 | awk '{ print $2 }' | tr -d ',' | awk -F'.' '{print $2}') )) < 83 ]]; then
    echo "**** Installing Comskip ****"
    /usr/bin/apt-get update
    /usr/bin/apt-get install -y autoconf libtool pkg-config make libswscale-dev libavformat-dev libavcodec-dev libavutil-dev libargtable2-dev
    mkdir -p /tmp/comskip
    wget -P /tmp/comskip https://github.com/erikkaashoek/Comskip/archive/refs/heads/master.zip
    unzip -d /tmp/comskip /tmp/comskip/master.zip
    (cd /tmp/comskip/Comskip-master && ./autogen.sh && ./configure --disable-dependency-tracking && make)
    cp -a /tmp/comskip/Comskip-master/comskip /usr/local/bin/comskip
    rm -rf /tmp/comskip
else
  echo "**** Comskip already installed ****"
fi
