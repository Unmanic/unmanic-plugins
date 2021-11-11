#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.tmp.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     21 Sep 2021, (7:02 PM)

    Copyright:
        Copyright (C) 2021 Josh Sunnex

        This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
        Public License as published by the Free Software Foundation, version 3.

        This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
        implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
        for more details.

        You should have received a copy of the GNU General Public License along with this program.
        If not, see <https://www.gnu.org/licenses/>.

"""
import hashlib
import logging
import mimetypes
import os
import stat
from configparser import NoSectionError, NoOptionError

from unmanic.libs.unplugins.settings import PluginSettings
from unmanic.libs.directoryinfo import UnmanicDirectoryInfo

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.comskip")


class Settings(PluginSettings):
    settings = {
        'limit_to_extensions': False,
        "allowed_extensions":  'ts',
        'config':              '',
        'enable_comchap':      False,
        'enable_comcut':       False,
    }

    def __init__(self):
        self.form_settings = {
            "limit_to_extensions": {
                "label": "Only run when the original source file matches specified extensions",
            },
            "allowed_extensions":  self.__set_allowed_extensions_form_settings(),
            "config":              {
                "label":      "Comskip configuration",
                "input_type": "textarea",
            },
            "enable_comchap":      self.__set_enable_comchap_form_settings(),
            "enable_comcut":       self.__set_enable_comcut_form_settings(),
        }

    def __set_allowed_extensions_form_settings(self):
        values = {
            "label": "Comma separated list of file extensions",
        }
        if not self.get_setting('limit_to_extensions'):
            values["display"] = 'hidden'
        return values

    def __set_enable_comchap_form_settings(self):
        values = {
            "label": "Generate chapter information in file metadata (Comchap)",
        }
        # Comchap always takes priority over Comcut if they are somehow accidentally both selected
        # This prevents both settings from being hidden if something goes wrong.
        if self.get_setting('enable_comcut') and not self.get_setting('enable_comchap'):
            values["display"] = 'hidden'
        return values

    def __set_enable_comcut_form_settings(self):
        values = {
            "label": "Remove detected commercials from file (Comcut)",
        }
        if self.get_setting('enable_comchap'):
            values["display"] = 'hidden'
        return values


def file_ends_in_allowed_extensions(path, allowed_extensions):
    """
    Check if the file is in the allowed search extensions

    :return:
    """
    # Get the file extension
    file_extension = os.path.splitext(path)[-1][1:]

    # Ensure the file's extension is lowercase
    file_extension = file_extension.lower()

    # If the config is empty (not yet configured) ignore everything
    if not allowed_extensions:
        logger.debug("Plugin has not yet been configured with a list of file extensions to allow. Blocking everything.")
        return False

    # Check if it ends with one of the allowed search extensions
    if file_extension in allowed_extensions:
        return True

    logger.debug("File '{}' does not end in the specified file extensions '{}'.".format(path, allowed_extensions))
    return False


def test_valid_mimetype(file_path):
    """
    Test the given file path for its mimetype.
    If the mimetype cannot be detected, it will fail this test.
    If the detected mimetype is not in the configured 'allowed_mimetypes'
        class variable, it will fail this test.

    :param file_path:
    :return:
    """
    # Only run this check against video/audio/image MIME types
    mimetypes.init()
    file_type = mimetypes.guess_type(file_path)[0]

    # If the file has no MIME type then it cannot be tested
    if file_type is None:
        logger.debug("Unable to fetch file MIME type - '{}'".format(file_path))
        return False

    # Make sure the MIME type is either audio, video or image
    file_type_category = file_type.split('/')[0]
    if file_type_category not in ['video']:
        logger.debug("File MIME type not 'video' - '{}'".format(file_path))
        return False

    return True


def file_already_processed(path):
    directory_info = UnmanicDirectoryInfo(os.path.dirname(path))

    try:
        processed = directory_info.get('comskip', os.path.basename(path))
    except NoSectionError as e:
        processed = ''
    except NoOptionError as e:
        processed = ''
    except Exception as e:
        logger.debug("Unknown exception {}.".format(e))
        processed = ''

    # Check for txt file with the same name as the video file
    file_dirname = os.path.dirname(path)
    file_sans_ext = os.path.splitext(os.path.basename(path))[0]
    comskip_file_out = "{}.txt".format(file_sans_ext)
    comskip_edl_file_out = "{}.edl".format(file_sans_ext)

    if processed in ['comchap', 'comcut']:
        logger.debug("File was previously processed with {}.".format(processed))
        # This stream already has been processed
        return True
    elif os.path.exists(os.path.join(file_dirname, comskip_file_out)):
        logger.debug("File has previously processed with comskip to make an .txt file")
        # This stream already has been processed
        return True
    elif os.path.exists(os.path.join(file_dirname, comskip_edl_file_out)):
        logger.debug("File has previously processed with comskip to make an .edl file")
        # This stream already has been processed
        return True

    # Default to...
    return False


def comskip_config_file():
    # Set config file path
    settings = Settings()
    profile_directory = settings.get_profile_directory()

    # Set the output file
    config = settings.get_setting('config')
    if not config:
        logger.error("Plugin not configured.")

    # Write comskip settings file
    comskip_config_file = os.path.join(profile_directory, 'comskip.ini')
    with open(comskip_config_file, "w") as f:
        f.write(config)
        # Ensure the end of the file has a linebreak
        f.write("\n\n")

    return comskip_config_file


def build_comskip_args(abspath):
    config_file = comskip_config_file()
    file_dirname = os.path.dirname(abspath)
    file_sans_ext = os.path.splitext(os.path.basename(abspath))[0]
    return [
        'comskip',
        '--ini={}'.format(config_file),
        '--output={}'.format(file_dirname),
        '--output-filename={}'.format(file_sans_ext),
        abspath
    ]


def build_comchap_args(abspath, file_out):
    config_file = comskip_config_file()
    comchap_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'comchap', 'comchap'))
    # Ensure comchap is executable
    st = os.stat(comchap_path)
    os.chmod(comchap_path, st.st_mode | stat.S_IEXEC)
    args = [
        comchap_path,
        '--comskip-ini={}'.format(config_file),
        '--keep-edl',
        '--keep-meta',
        '--verbose',
        abspath,
        file_out,
    ]
    return args


def build_comcut_args(abspath, file_out):
    config_file = comskip_config_file()
    comcut_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'comchap', 'comcut'))
    # Ensure comcut is executable
    st = os.stat(comcut_path)
    os.chmod(comcut_path, st.st_mode | stat.S_IEXEC)
    args = [
        comcut_path,
        '--comskip-ini={}'.format(config_file),
        '--keep-edl',
        '--keep-meta',
        abspath,
        file_out,
    ]
    return args


def on_library_management_file_test(data):
    """
    Runner function - enables additional actions during the library management file tests.

    The 'data' object argument includes:
        path                            - String containing the full path to the file being tested.
        issues                          - List of currently found issues for not processing the file.
        add_file_to_pending_tasks       - Boolean, is the file currently marked to be added to the queue for processing.

    :param data:
    :return:

    """
    # Get the path to the file
    abspath = data.get('path')

    # Ensure this is a video file
    if not test_valid_mimetype(abspath):
        return data

    # Limit to configured file extensions
    settings = Settings()
    if settings.get_setting('limit_to_extensions'):
        allowed_extensions = settings.get_setting('allowed_extensions')
        if not file_ends_in_allowed_extensions(abspath, allowed_extensions):
            return data

    if not file_already_processed(abspath):
        # Mark this file to be added to the pending tasks
        data['add_file_to_pending_tasks'] = True
        logger.debug("File has not been processed previously '{}'. It should be added to task list.".format(abspath))

    return data


def on_worker_process(data):
    """
    Runner function - enables additional configured processing jobs during the worker stages of a task.

    The 'data' object argument includes:
        exec_command            - A command that Unmanic should execute. Can be empty.
        command_progress_parser - A function that Unmanic can use to parse the STDOUT of the command to collect progress stats. Can be empty.
        file_in                 - The source file to be processed by the command.
        file_out                - The destination that the command should output (may be the same as the file_in if necessary).
        original_file_path      - The absolute path to the original file.
        repeat                  - Boolean, should this runner be executed again once completed with the same variables.

    :param data:
    :return:
    
    """
    # Default to no FFMPEG command required. This prevents the FFMPEG command from running if it is not required
    data['exec_command'] = []
    data['repeat'] = False

    # Get the file paths
    file_in = data.get('file_in')
    file_out = data.get('file_out')
    original_file_path = data.get('original_file_path')

    # Ensure this is a video file
    if not test_valid_mimetype(file_in):
        return data

    # Limit to configured file extensions
    # Unlike other plugins, this is checked against the original file path, not what is currently cached
    settings = Settings()
    if settings.get_setting('limit_to_extensions'):
        allowed_extensions = settings.get_setting('allowed_extensions')
        if not file_ends_in_allowed_extensions(original_file_path, allowed_extensions):
            return data

    if not file_already_processed(original_file_path):
        # Check what we are running...
        settings = Settings()
        if settings.get_setting('enable_comchap'):
            # Build args
            args = build_comchap_args(file_in, data.get('file_out'))
        elif settings.get_setting('enable_comcut'):
            # Build args
            args = build_comcut_args(file_in, data.get('file_out'))
        else:
            # Build args
            # This will create the file in the source file directory
            args = build_comskip_args(file_in)

        # Generate command
        data['exec_command'] = args

        # Mark file as being processed for post-processor
        src_file_hash = hashlib.md5(original_file_path.encode('utf8')).hexdigest()
        profile_directory = settings.get_profile_directory()
        plugin_file_lockfile = os.path.join(profile_directory, '{}.lock'.format(src_file_hash))
        with open(plugin_file_lockfile, 'w') as f:
            pass

    return data


def on_postprocessor_task_results(data):
    """
    Runner function - provides a means for additional postprocessor functions based on the task success.

    The 'data' object argument includes:
        task_processing_success         - Boolean, did all task processes complete successfully.
        file_move_processes_success     - Boolean, did all postprocessor movement tasks complete successfully.
        destination_files               - List containing all file paths created by postprocessor file movements.
        source_data                     - Dictionary containing data pertaining to the original source file.

    :param data:
    :return:

    """
    # We only care that the task completed successfully.
    # If a worker processing task was unsuccessful, dont mark the file as being processed
    if not data.get('task_processing_success'):
        return data

    # Was the processed file one of the ones we worked on...
    settings = Settings()
    original_source_path = data.get('source_data', {}).get('abspath', '_')
    src_file_hash = hashlib.md5(original_source_path.encode('utf8')).hexdigest()
    profile_directory = settings.get_profile_directory()
    plugin_file_lockfile = os.path.join(profile_directory, '{}.lock'.format(src_file_hash))
    if not os.path.exists(plugin_file_lockfile):
        return data
    os.remove(plugin_file_lockfile)

    # Loop over the destination_files list and update the directory info file for each one
    settings = Settings()
    for destination_file in data.get('destination_files'):
        directory_info = UnmanicDirectoryInfo(os.path.dirname(destination_file))
        if settings.get_setting('enable_comchap'):
            directory_info.set('comskip', os.path.basename(destination_file), 'comchap')
        elif settings.get_setting('enable_comcut'):
            directory_info.set('comskip', os.path.basename(destination_file), 'comcut')
        else:
            directory_info.set('comskip', os.path.basename(destination_file), 'comskip')
        directory_info.save()
        logger.debug("Comskip info written for '{}'.".format(destination_file))

    return data
