#!/bin/bash
# -
# File: install-comskip.sh
# Project: plugins
# File Created: 28 September 2021, 8:03 AM
# Author: josh5
# -----
# Last Modified: 28 September 2021, 8:03 AM
# Modified By: josh5
# -

# Script is executed by the Unmanic container on startup to auto-install dependencies

if ! command -v comskip &> /dev/null; then
    echo "**** Installing Comskip ****"
    apt-get update
    apt-get install -y comskip
else
    echo "**** Comskip already installed ****"
fi
