#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    example_worker_process

    Docs: 
        https://docs.unmanic.app/docs/plugins/writing_plugins/plugin_runner_types#post-processor---file-movements

"""
import os
from unmanic.libs.unplugins.settings import PluginSettings
from unmanic.libs.system import System


# TODO: Add library scanner plugin to prevent adding files again

def add_path_to_unmanic_ignore_file(path):
    basename = os.path.basename(path)
    dirname = os.path.dirname(path)
    unmanic_ignore_file = os.path.join(dirname, '.unmanicignore')

    # If the file exists, check if the file basename is already in it
    exists_in_file = False
    if os.path.exists(unmanic_ignore_file):
        with open(unmanic_ignore_file) as f:
            for line in f:
                if basename in line:
                    exists_in_file = True

    # If the file does not yet exist or it does exists but the basename is not already appended:
    if not exists_in_file:
        # Append the basename to the file
        with open(unmanic_ignore_file, 'a') as outfile:
            outfile.write("{}\n".format(basename))


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

    # keep the original file. We are going to create a copy
    data['remove_source_file'] = False

    # Add 'UNMANIC to the end of the file'
    tmp_file_out = os.path.splitext(data['file_out'])
    data['file_out'] = "{}-{}{}".format(tmp_file_out[0], 'UNMANIC', tmp_file_out[1])

    # Add original file's name to '.unmanicignore' file to prevent this directory being added again.
    if data['file_out'].get('abspath'):
        add_path_to_unmanic_ignore_file(data['file_out'].get('abspath'))

    return data
