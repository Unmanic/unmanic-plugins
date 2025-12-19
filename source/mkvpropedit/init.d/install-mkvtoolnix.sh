#!/usr/bin/env bash

# Script is executed by the Unmanic container on startup to auto-install dependencies

if ! command -v mkvpropedit &> /dev/null ; then
    echo "**** Installing mkvtoolnix ****"
    /usr/bin/apt-get update
    /usr/bin/apt-get install -y mkvtoolnix
else
  echo "**** mkvtoolnix already installed ****"
fi
