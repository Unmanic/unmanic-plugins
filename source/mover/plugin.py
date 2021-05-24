#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from unmanic.libs.unplugins.settings import PluginSettings

class Settings(PluginSettings):
    settings = {
        "destination directory": "/library",
    }
def on_postprocessor_file_movement(data):
    """
    Runner function - configures additional postprocessor file movements during the postprocessor stage of a task.
    The 'data' object argument includes:
        source_data             - Dictionary containing data pertaining to the original source file.
        remove_source_file      - Boolean, should Unmanic remove the original source file after all copy operations are complete.
        copy_file               - Boolean, should Unmanic run a copy operation with the returned data variables.
        file_in                 - The converted cache file to be copied by the postprocessor.
        file_out                - The destination file that the file will be copied to.
    :param data:
    :return:
    """
    settings = Settings()
    destdir = settings.get_setting('destination directory')
    path = data['source_data'].get('abspath') 
    # Keep source file
    data['remove_source_file'] = False
    
    # Get the base name of the source file
    basename = os.path.basename(path)
    
    # Get the parent directory of the file
    dirname = os.path.dirname(path)

    # get the base name of that directory path
    subdir = os.path.basename(dirname)

    # Make subfolder in destination directory
    if not os.path.exists(os.path.join(destdir, subdir)):
        os.mkdir(os.path.join(destdir, subdir))
    
    #get the basenout of the output file
    b_out = os.path.basename(data['file_out'])
    
    #output the file
    data['file_out'] = os.path.join(destdir, subdir, b_out)
    
    # get the file in extension
    extension = os.path.splitext(data['file_in'])[1]

    # set the file out extension to the correct extension
    data['file_out'] = "{}{}".format(os.path.splitext(data['file_out'])[0], extension)
    print(destdir)
    print(path)
    print(basename)
    print(dirname)
    print(subdir)
    print(b_out)
    print(data)

    return data
   
   
   



    

    
