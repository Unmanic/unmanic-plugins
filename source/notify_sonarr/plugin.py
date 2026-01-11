#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic-plugins.plugin.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     27 Feb 2022, (12:22 PM)

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
import logging
import os
import pprint
import time
import json
import re

import humanfriendly
from simpleeval import simple_eval
from pyarr import SonarrAPI
from pyarr.exceptions import (
    PyarrAccessRestricted,
    PyarrBadGateway,
    PyarrConnectionError,
    PyarrResourceNotFound,
    PyarrUnauthorizedError,
)
from unmanic.libs.unplugins.settings import PluginSettings
from unmanic.libs.library import Library
from unmanic.webserver.helpers import pending_tasks

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.notify_sonarr")


class Settings(PluginSettings):
    settings = {
        'host_url':                  'http://localhost:8989',
        'api_key':                   '',
        'mode':                      'update_mode',
        'rename_files':              False,
        'limit_import_on_file_size': True,
        'minimum_file_size':         '100MB',
        'webhook_section_header':    '',
        'enable_webhook':            False,
        'webhook_admonition_note':   '',
    }

    def __init__(self, *args, **kwargs):
        # Populate defaults for 10 rules
        for i in range(1, 11):
            self.settings[f'link_subheader_{i}'] = ''
            self.settings[f'rule_query_{i}'] = ''
            self.settings[f'library_id_{i}'] = ''
            self.settings[f'trigger_test_path_{i}'] = True
            self.settings[f'create_task_{i}'] = False

        super(Settings, self).__init__(*args, **kwargs)

    def get_form_settings(self):
        self.form_settings = self.__build_form_settings()
        return self.form_settings

    def __build_form_settings(self):
        form_settings = {
            "host_url":                  {
                "label": "Sonarr LAN IP Address",
            },
            "api_key":                   {
                "label": "Sonarr API Key",
            },
            "mode":                      {
                "label":          "Mode",
                "input_type":     "select",
                "select_options": [
                    {
                        'value': "update_mode",
                        'label': "Trigger series refresh on task complete",
                    },
                    {
                        'value': "import_mode",
                        'label': "Import episode on task complete",
                    },
                ],
            },
            "rename_files":              self.__set_rename_files(),
            "limit_import_on_file_size": self.__set_limit_import_on_file_size(),
            "minimum_file_size":         self.__set_minimum_file_size(),
            "webhook_section_header":    self.__set_webhook_section_header(),
            "enable_webhook":            self.__set_enable_webhook(),
            "webhook_admonition_note":   self.__set_webhook_admonition_note(),
        }

        # Add dynamic fields (Global Only)
        libraries = Library.get_all_libraries()
        library_options = [{'value': '', 'label': 'Select Library...'}]
        for lib in libraries:
            library_options.append({'value': str(lib.get('id')), 'label': lib.get('name')})

        # Determine visibility for webhook section
        webhook_enabled = not self.library_id and self.get_setting('enable_webhook') and self.get_setting('api_key')

        for i in range(1, 11):
            index = str(i)
            # Logic: Show if webhook enabled AND (first item OR previous item has a query)
            show_item = webhook_enabled and (i == 1 or self.get_setting(f'rule_query_{i-1}'))

            display = "visible" if show_item else "hidden"

            subheader_settings = {
                "label": f"Webhook Library Link #{index}",
                "input_type": "section_subheader",
                "display": display,
            }
            rule_settings = {
                "label": "Rule Query",
                "description": "Query to match Sonarr attributes (e.g. quality_profile == 'HD' and 'tag' in tags)",
                "display": display,
                "sub_setting": True,
            }
            library_settings = {
                "label": "Target Library",
                "input_type": "select",
                "select_options": library_options,
                "display": display,
                "sub_setting": True,
            }
            trigger_settings = {
                "label": "Trigger Library File Test",
                "description": "Run the file through the library's file tests to check if it needs processing.",
                "display": display,
                "sub_setting": True,
            }

            # Show create_task only if trigger_test_path is enabled
            create_task_display = display
            if not self.get_setting(f'trigger_test_path_{index}'):
                create_task_display = "hidden"

            create_task_settings = {
                "label": "Create Pending Task If Needed",
                "description": "If the file test determines the file needs processing, add it to the pending task queue.",
                "display": create_task_display,
                "sub_setting": True,
            }

            if i > 1:
                subheader_settings["req_lev"] = 2
                rule_settings["req_lev"] = 2
                library_settings["req_lev"] = 2
                trigger_settings["req_lev"] = 2
                create_task_settings["req_lev"] = 2

            form_settings[f'link_subheader_{index}'] = subheader_settings
            form_settings[f'rule_query_{index}'] = rule_settings
            form_settings[f'library_id_{index}'] = library_settings
            form_settings[f'trigger_test_path_{index}'] = trigger_settings
            form_settings[f'create_task_{index}'] = create_task_settings

        # Hide dynamic fields if they exist in settings but we are in library mode
        # (This handles the case where they are in self.settings but shouldn't be shown)
        if self.library_id:
            for key in self.settings:
                if key.startswith('rule_query_') or key.startswith('library_id_') or key.startswith('link_subheader_') or key.startswith('trigger_test_path_') or key.startswith('create_task_'):
                    if key not in form_settings:
                        form_settings[key] = {"display": "hidden"}

        return form_settings

    def __set_rename_files(self):
        values = {
            "label": "Trigger Sonarr file renaming",
        }
        if self.get_setting('mode') != 'update_mode':
            values["display"] = 'hidden'
        return values

    def __set_limit_import_on_file_size(self):
        values = {
            "label": "Limit file import size",
        }
        if self.get_setting('mode') != 'import_mode':
            values["display"] = 'hidden'
        return values

    def __set_minimum_file_size(self):
        values = {
            "label": "Minimum file size",
        }
        if self.get_setting('mode') != 'import_mode':
            values["display"] = 'hidden'
        if not self.get_setting('limit_import_on_file_size'):
            values["display"] = 'hidden'
        return values

    def __set_webhook_admonition_note(self):
        description = (
            "Configure rules to link incoming webhooks to specific Unmanic libraries.<br>"
            "Rules are python expressions evaluated against the webhook payload.<br>"
            "Available variables:<br>"
            "<ul>"
            "<li><code>event_type</code>: The type of event (e.g. 'Grab', 'Download', 'Rename')</li>"
            "<li><code>series_title</code>: The title of the series</li>"
            "<li><code>series_id</code>: The internal ID of the series</li>"
            "<li><code>tvdb_id</code>: The TVDB ID of the series</li>"
            "<li><code>root_path</code>: The root folder path for the series</li>"
            "<li><code>tags</code>: A list of tag labels applied to the series</li>"
            "<li><code>quality</code>: The quality profile name of the episode file (e.g. 'WEBDL-1080p')</li>"
            "<li><code>path</code>: The absolute path to the episode file</li>"
            "</ul>"
            "Examples:<br>"
            "<ul>"
            "<li><code>quality_profile == 'Ultra-HD' and '4k' in tags</code></li>"
            "<li><code>root_path.startswith('/tv/anime')</code></li>"
            "<li><code>'Archive' in root_path</code></li>"
            "<li><code>'Animation' in tags</code></li>"
            "</ul>"
        )
        values = {
            "label": "Note",
            "description": description,
            "input_type": "section_admonition",
        }
        if self.library_id or not self.get_setting('api_key') or not self.get_setting('enable_webhook'):
            values["display"] = 'hidden'
        return values

    def __set_webhook_section_header(self):
        values = {
            "label": "Webhooks",
            "input_type": "section_header",
        }
        if self.library_id or not self.get_setting('api_key'):
            values["display"] = 'hidden'
        return values

    def __set_enable_webhook(self):
        values = {
            "label": "Enable Webhook Processing",
            "description": "Allow this plugin to receive webhooks from Sonarr to trigger tasks.",
        }
        if self.library_id or not self.get_setting('api_key'):
            values["display"] = 'hidden'
        return values


def check_file_size_under_max_file_size(path, minimum_file_size):
    file_stats = os.stat(os.path.join(path))
    if int(humanfriendly.parse_size(minimum_file_size)) < int(file_stats.st_size):
        return False
    return True


def update_mode(api, dest_path, rename_files):
    basename = os.path.basename(dest_path)

    # Fetch episode data. Try with full path first, then basename if that fails or returns nothing useful.
    episode_data = api.get_parsed_title(dest_path)
    if not episode_data or not episode_data.get('series'):
        logger.debug("Failed to parse series info from full path '%s'. Trying with basename '%s'", dest_path, basename)
        episode_data = api.get_parsed_title(basename)

    # Fetch a series ID from Sonarr
    series_title = episode_data.get('series', {}).get('title') if episode_data else None
    series_id = episode_data.get('series', {}).get('id') if episode_data else None

    if not series_id:
        logger.error("Missing series ID. Failed to queue refresh of series for file: '%s'", dest_path)
        return

    try:
        # Run API command for RescanSeries
        #   - RescanSeries with a series ID
        result = api.post_command('RescanSeries', seriesId=series_id)
        if result.get('message'):
            logger.error("Failed to queue refresh of series ID '%s' for file: '%s'", series_id, dest_path)
            logger.error("Response from sonarr: %s", result['message'])
            return
        else:
            logger.info("Successfully queued refresh of the Series '%s' (ID: %s) for file: '%s'",
                        series_title, series_id, dest_path)
    except (PyarrUnauthorizedError, PyarrAccessRestricted, PyarrResourceNotFound, PyarrBadGateway, PyarrConnectionError) as err:
        logger.error("Failed to queue refresh of series ID '%s' for file: '%s'. Error: %s",
                     series_id, dest_path, str(err))
        return
    except Exception as err:
        logger.error("An unexpected error occurred while queuing refresh for series ID '%s': %s", series_id, str(err))
        return

    if rename_files:
        logger.info("Waiting 10 seconds before triggering rename for series '%s'...", series_title)
        time.sleep(10)  # Must give time (more than Radarr) for the refresh to complete before we run the rename.
        try:
            rename_list = api.get_episode_files_by_series_id(series_id)
            file_ids = [episode['id'] for episode in rename_list]
            if not file_ids:
                logger.warning("No episode files found to rename for series '%s' (ID: %s)", series_title, series_id)
                return
            result = api.post_command('RenameFiles', seriesId=series_id, files=file_ids)
            if isinstance(result, dict):
                logger.info("Successfully triggered rename of series '%s' for file: '%s'", series_title, dest_path)
            else:
                logger.error("Failed to trigger rename of series ID '%s' for file: '%s'. Result: %s",
                             series_id, dest_path, str(result))
        except (PyarrUnauthorizedError, PyarrAccessRestricted, PyarrResourceNotFound, PyarrBadGateway, PyarrConnectionError) as err:
            logger.error("Failed to trigger rename of series '%s' for file: '%s'. Error: %s",
                         series_title, dest_path, str(err))
        except Exception as err:
            logger.error("Failed to trigger rename of series ID '%s' for file: '%s'\nError received: %s",
                         series_id, dest_path, str(err))


def import_mode(api, source_path, dest_path):
    source_basename = os.path.basename(source_path)
    abspath_string = os.path.abspath(dest_path)

    download_id = None
    episode_title = None

    try:
        queue = api.get_queue()
        message = pprint.pformat(queue, indent=1)
        logger.debug("Current Sonarr queue: \n%s", message)
        for item in queue.get('records', []):
            item_output_basename = os.path.basename(item.get('outputPath', ''))
            if item_output_basename == source_basename:
                download_id = item.get('downloadId')
                episode_title = item.get('title')
                break
    except Exception as err:
        logger.error("Failed to fetch Sonarr queue: %s", str(err))
        # Proceed anyway, we might still be able to trigger import by path

    # Run import
    try:
        if download_id:
            # Run API command for DownloadedEpisodesScan
            #   - DownloadedEpisodesScan with a path and downloadClientId
            logger.info("Queued import episode '%s' using downloadClientId: '%s' for path '%s'",
                        episode_title, download_id, abspath_string)
            result = api.post_command('DownloadedEpisodesScan', path=abspath_string, downloadClientId=download_id)
        else:
            # Run API command for DownloadedEpisodesScan without passing a downloadClientId
            #   - DownloadedEpisodesScan with a path and downloadClientId
            logger.info("Queued import using just the file path '%s'", abspath_string)
            result = api.post_command('DownloadedEpisodesScan', path=abspath_string)

        # Log results
        if isinstance(result, dict) and result.get('message'):
            logger.error("Failed to queue import of file: '%s'. Sonarr message: %s", dest_path, result['message'])
            return

        logger.info("Successfully queued import of file in Sonarr: '%s'", dest_path)
        logger.debug("Queued import result: %s", pprint.pformat(result, indent=1))
    except Exception as err:
        logger.error("Failed to queue import of file '%s' in Sonarr: %s", dest_path, str(err))


def process_files(settings, source_file, destination_files, host_url, api_key):
    api = SonarrAPI(host_url, api_key)

    mode = settings.get_setting('mode')
    rename_files = settings.get_setting('rename_files')

    # Get the basename of the file
    for dest_file in destination_files:
        if mode == 'update_mode':
            update_mode(api, dest_file, rename_files)
        elif mode == 'import_mode':
            minimum_file_size = settings.get_setting('minimum_file_size')
            if check_file_size_under_max_file_size(dest_file, minimum_file_size):
                # Ignore this file
                logger.info("Ignoring file as it is under configured minimum size file: '%s'", dest_file)
                continue
            import_mode(api, source_file, dest_file)


def on_postprocessor_task_results(data):
    """
    Runner function - provides a means for additional postprocessor functions based on the task success.

    The 'data' object argument includes:
        library_id                      - The library that the current task is associated with
        task_processing_success         - Boolean, did all task processes complete successfully.
        file_move_processes_success     - Boolean, did all postprocessor movement tasks complete successfully.
        destination_files               - List containing all file paths created by postprocessor file movements.
        source_data                     - Dictionary containing data pertaining to the original source file.

    :param data:
    :return:

    """
    # Configure settings object (maintain compatibility with v1 plugins)
    if data.get('library_id'):
        settings = Settings(library_id=data.get('library_id'))
    else:
        settings = Settings()

    # Do nothing if the task was not successful
    if not data.get('task_processing_success'):
        logger.debug("Skipping notify_sonarr as the task was not successful.")
        return
    if not data.get('file_move_processes_success'):
        logger.debug("Skipping notify_sonarr as the file move processes were not successful.")
        return

    # Fetch destination and source files
    source_file = data.get('source_data', {}).get('abspath')
    destination_files = data.get('destination_files', [])

    # Setup API
    host_url = settings.get_setting('host_url')
    api_key = settings.get_setting('api_key')

    if not api_key:
        logger.error("Sonarr API Key is not configured. Skipping notification.")
        return

    process_files(settings, source_file, destination_files, host_url, api_key)


def render_plugin_api(data):
    """
    Runner function - provides an endpoint for the plugin to handle API requests.

    The 'data' object argument includes:
        content_type                    - (string) The response content type (default: application/json)
        content                         - (dict/string) The response content
        status                          - (int) The response status code (default: 200)
        method                          - (string) The request method (e.g. POST, GET)
        path                            - (string) The request path
        uri                             - (string) The request uri
        query                           - (string) The request query
        arguments                       - (dict) The request arguments
        body                            - (bytes) The request body
        plugin_id                       - (string) The ID of the plugin

    :param data:
    :return:
    """
    try:
        settings = Settings()

        if not settings.get_setting('enable_webhook') or not settings.get_setting('api_key'):
            # Webhook disabled
            data['status'] = 404
            data['content'] = {"error": "Webhook disabled"}
            return

        if data.get('method') != 'POST':
            data['status'] = 405
            data['content'] = {"error": "Method not allowed"}
            return

        try:
            body = data.get('body', b'').decode('utf-8')
            payload = json.loads(body)
        except Exception as e:
            logger.error("Failed to parse webhook JSON: %s", str(e))
            data['status'] = 400
            data['content'] = {"error": "Invalid JSON"}
            return

        logger.debug("Received Sonarr webhook: %s", pprint.pformat(payload))

        # Common Sonarr payload fields: eventType, series, episodes, episodeFile/episodeFiles
        event_type = payload.get('eventType')

        if isinstance(event_type, str) and event_type.strip().lower() == 'test':
            logger.info("Received Test webhook from Sonarr. Connection successful.")
            data['status'] = 200
            data['content'] = {"success": True, "message": "Test successful"}
            return
        if event_type != 'Download':
            logger.info("Ignoring Sonarr webhook event type '%s'", event_type)
            data['content'] = {"success": True, "message": "Ignored webhook event type"}
            return

        series = payload.get('series', {})
        root_path = series.get('path')

        episode_files = []
        if isinstance(payload.get('episodeFile'), dict):
            episode_files = [payload['episodeFile']]
        elif isinstance(payload.get('episodeFiles'), list):
            episode_files = payload['episodeFiles']

        if not episode_files:
            logger.info("Ignoring Sonarr webhook without episode file details (event type '%s')", event_type)
            data['content'] = {"success": True, "message": "Ignored webhook without episode file details"}
            return

        # Base data for rule evaluation
        flat_data_base = {
            'event_type': event_type,
            'series_title': series.get('title'),
            'series_id': series.get('id'),
            'tvdb_id': series.get('tvdbId'),
            'root_path': root_path,
            'tags': series.get('tags', []),
            'quality_profile': None,
            'quality': None,
            'quality_version': None,
            'relative_path': None,
            'path': None,
        }

        # Fetch extra info from Sonarr API if needed (e.g. tags are often IDs in webhooks or missing)
        # Ideally we should fetch series info to get textual tags
        try:
            host_url = settings.get_setting('host_url')
            api_key = settings.get_setting('api_key')
            api = SonarrAPI(host_url, api_key)

            # If we have a series ID, fetch series to get tags
            if flat_data_base.get('series_id'):
                series_info = api.get_series(flat_data_base['series_id'])

                # series_info has 'tags' which are IDs. Need to resolve them?
                # pyarr might return IDs.
                # We also need to fetch all tags to map IDs to names.
                tag_ids = series_info.get('tags', [])
                if tag_ids:
                    all_tags = api.get_tag()
                    tag_names = [t['label'] for t in all_tags if t['id'] in tag_ids]
                    flat_data_base['tags'] = tag_names
                    logger.debug("Resolved tags: %s", tag_names)

                # Also get quality profile name
                quality_profile_id = series_info.get('qualityProfileId')
                if quality_profile_id:
                    profiles = api.get_quality_profile()
                    for prof in profiles:
                        if prof['id'] == quality_profile_id:
                            flat_data_base['quality_profile'] = prof['name']
                            break
        except Exception as e:
            logger.warning("Failed to fetch additional info from Sonarr: %s", str(e))
            # Proceed with what we have

        # Evaluate Rules per episode file
        configured = settings.get_setting()
        library_paths = {lib['id']: lib['path'] for lib in Library.get_all_libraries()}
        matched_rules = []

        for episode_file in episode_files:
            flat_data = dict(flat_data_base)
            flat_data['quality'] = episode_file.get('quality')
            flat_data['quality_version'] = episode_file.get('qualityVersion')
            flat_data['relative_path'] = episode_file.get('relativePath')
            flat_data['path'] = episode_file.get('path')

            # If file path is missing in payload, construct it
            file_path = flat_data.get('path')
            if not file_path and root_path and flat_data.get('relative_path'):
                file_path = os.path.join(root_path, flat_data.get('relative_path'))
                flat_data['path'] = file_path

            if not file_path:
                logger.error("Unable to determine absolute file path for webhook payload")
                continue

            if root_path and not os.path.normpath(file_path).startswith(os.path.normpath(root_path)):
                logger.info("Ignoring webhook for file outside series root: '%s'", file_path)
                continue

            logger.debug("Evaluated data for rules: %s", pprint.pformat(flat_data))

            for key in configured:
                if key.startswith('rule_query_'):
                    query = configured.get(key)
                    if not query:
                        continue

                    index = key.split('_')[-1]
                    library_id = configured.get(f'library_id_{index}')
                    if not library_id:
                        continue

                    # Evaluate query against flat_data
                    try:
                        # Replace 'AND'/'OR' with 'and'/'or' for python syntax
                        safe_query = query.replace('AND', 'and').replace('OR', 'or')
                        match = simple_eval(safe_query, names=flat_data)
                        if match:
                            library_id = int(library_id)
                            library_path = library_paths.get(library_id)
                            if not library_path:
                                logger.error("No library path found for Library ID %s", library_id)
                                continue

                            sonarr_root_dir = os.path.dirname(os.path.normpath(root_path)) if root_path else None
                            if not sonarr_root_dir:
                                logger.error("Unable to determine Sonarr root directory for file '%s'", file_path)
                                continue

                            if not os.path.normpath(file_path).startswith(sonarr_root_dir):
                                logger.error("File path '%s' is outside Sonarr root '%s'", file_path, sonarr_root_dir)
                                continue

                            relative_path = os.path.relpath(file_path, sonarr_root_dir)
                            unmanic_path = os.path.normpath(os.path.join(library_path, relative_path))

                            logger.info("Rule '%s' matched. Associated with Library ID %s", query, library_id)
                            matched_rules.append({'library_id': library_id, 'index': index, 'path': unmanic_path})
                    except Exception as e:
                        logger.error("Error evaluating rule '%s': %s", query, str(e))

        # Trigger Actions
        triggered_actions = []
        if matched_rules:
            for rule in matched_rules:
                lib_id = rule['library_id']
                index = rule['index']
                file_path = rule['path']

                trigger_test = settings.get_setting(f'trigger_test_path_{index}')
                create_task = settings.get_setting(f'create_task_{index}')

                if trigger_test:
                    logger.info("Triggering test for path '%s' in library %s (Rule %s)", file_path, lib_id, index)
                    result = pending_tasks.test_path_for_pending_task(file_path, library_id=lib_id)

                    if create_task:
                        logger.info("File '%s' needs processing. Creating pending task in library %s", file_path, lib_id)
                        if result and result.get('add_file_to_pending_tasks'):
                            pending_tasks.create_task(file_path, library_id=lib_id,
                                                      priority_score=result.get('priority_score', 0))
                        triggered_actions.append({'library_id': lib_id, 'action': 'create_task', 'rule_index': index})
                    else:
                        triggered_actions.append({'library_id': lib_id, 'action': 'test_only', 'rule_index': index})
                else:
                    logger.info("Skipping test for path '%s' in library %s (Rule %s) - Action disabled",
                                file_path, lib_id, index)

            data['content'] = {"success": True, "triggered_actions": triggered_actions}
        else:
            logger.error("No matching library found for webhook payload")
            data['content'] = {"success": False, "message": "No rules matched for webhook payload"}

    except Exception as e:
        import traceback
        logger.error("Exception in render_plugin_api: %s\n%s", str(e), traceback.format_exc())
        data['status'] = 500
        data['content'] = {"error": "Internal Server Error"}
