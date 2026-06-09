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
# NOTE:
# This plugin is intentionally kept as close as possible to the notify_sonarr plugin.
# If you add a feature here or fix a bug here, review notify_sonarr and decide whether
# the same change should be applied there as well. Keep Arr-specific differences grouped
# in the Arr-specific helper/constants section so the two files remain easy to diff.
import json
import logging
import os
import pprint
import re
import time
import traceback

import humanfriendly
from simpleeval import simple_eval

from pyarr import RadarrAPI
from pyarr.exceptions import (
    PyarrAccessRestricted,
    PyarrBadGateway,
    PyarrConnectionError,
    PyarrResourceNotFound,
    PyarrUnauthorizedError,
)

from unmanic.libs.library import Library
from unmanic.libs.unplugins.settings import PluginSettings
from unmanic.webserver.helpers import pending_tasks

ARR_NAME = "Radarr"
ARR_NAME_LOWER = "radarr"
ARR_API_CLASS = RadarrAPI
ARR_DEFAULT_HOST_URL = "http://localhost:7878"
ARR_ENTITY_LABEL = "movie"
ARR_ENTITY_LABEL_TITLE = "Movie"
ARR_ENTITY_LABEL_PLURAL = "movies"
ARR_FILE_LABEL = "movie file"
ARR_FILE_LABEL_PLURAL = "movie files"
ARR_LIBRARY_EXAMPLE_PATH = "/movies/anime"
ARR_TAGS_VARIABLE_LABEL = "movie"
ARR_QUALITY_EXAMPLE = "Bluray-1080p"
ARR_ID_FIELD = "movie_id"
ARR_TITLE_FIELD = "movie_title"
ARR_EXTERNAL_ID_FIELD = "tmdb_id"
ARR_EXTERNAL_ID_LABEL = "TMDb"
ARR_QUEUE_LOOKUP_KEY = "title"
ARR_QUEUE_COMMAND_NAME = "DownloadedMoviesScan"
ARR_REFRESH_COMMAND_NAME = "RefreshMovie"
ARR_RENAME_COMMAND_NAME = "RenameMovie"
ARR_TRIGGER_REFRESH_LABEL = "Trigger movie refresh on task complete"
ARR_IMPORT_LABEL = "Import movie on task complete"
ARR_TRIGGER_RENAME_LABEL = "Trigger Radarr file renaming"
ARR_LOGGER_NAME = "Unmanic.Plugin.notify_radarr"
ARR_WEBHOOK_TEST_MESSAGE = "Received Test webhook from Radarr. Connection successful."

# Configure plugin logger
logger = logging.getLogger(ARR_LOGGER_NAME)


class Settings(PluginSettings):
    settings = {
        'host_url':                  ARR_DEFAULT_HOST_URL,
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
                "label":   f"{ARR_NAME} LAN IP Address",
                "tooltip": "Ensure the address starts with 'http'",
            },
            "api_key":                   {
                "label": f"{ARR_NAME} API Key",
            },
            "mode":                      {
                "label":          "Mode",
                "input_type":     "select",
                "select_options": [
                    {
                        'value': "update_mode",
                        'label': ARR_TRIGGER_REFRESH_LABEL,
                    },
                    {
                        'value': "import_mode",
                        'label': ARR_IMPORT_LABEL,
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
            show_item = webhook_enabled and (i == 1 or self.get_setting(f'rule_query_{i - 1}'))

            display = "visible" if show_item else "hidden"

            form_settings[f'link_subheader_{index}'] = {
                "label":      f"Webhook Library Link #{index}",
                "input_type": "section_subheader",
                "display":    display,
            }
            form_settings[f'rule_query_{index}'] = {
                "label":       "Rule Query",
                "description": f"Query to match {ARR_NAME} attributes (e.g. quality_profile == 'HD' and 'tag' in tags)",
                "display":     display,
                "sub_setting": True,
            }
            form_settings[f'library_id_{index}'] = {
                "label":          "Target Library",
                "input_type":     "select",
                "select_options": library_options,
                "display":        display,
                "sub_setting":    True,
            }
            form_settings[f'trigger_test_path_{index}'] = {
                "label":       "Trigger Library File Test",
                "description": "Run the file through the library's file tests to check if it needs processing.",
                "display":     display,
                "sub_setting": True,
            }

            # Show create_task only if trigger_test_path is enabled
            create_task_display = display
            if not self.get_setting(f'trigger_test_path_{index}'):
                create_task_display = "hidden"

            form_settings[f'create_task_{index}'] = {
                "label":       "Create Pending Task",
                "description": "If the file test determines the file needs processing, add it to the pending task queue.",
                "display":     create_task_display,
                "sub_setting": True,
            }

            if i > 1:
                for key in (
                        f'link_subheader_{index}',
                        f'rule_query_{index}',
                        f'library_id_{index}',
                        f'trigger_test_path_{index}',
                        f'create_task_{index}',
                ):
                    form_settings[key]["req_lev"] = 2

        # Hide dynamic fields if they exist in settings but we are in library mode
        # (This handles the case where they are in self.settings but shouldn't be shown)
        if self.library_id:
            for key in self.settings:
                if (
                        key.startswith('rule_query_')
                        or key.startswith('library_id_')
                        or key.startswith('link_subheader_')
                        or key.startswith('trigger_test_path_')
                        or key.startswith('create_task_')
                ):
                    if key not in form_settings:
                        form_settings[key] = {"display": "hidden"}

        return form_settings

    def __set_rename_files(self):
        values = {
            "label":       ARR_TRIGGER_RENAME_LABEL,
            "tooltip":     f"Trigger {ARR_NAME} to re-name files according to the defined naming scheme",
            "sub_setting": True,
        }
        if self.get_setting('mode') != 'update_mode':
            values["display"] = 'hidden'
        return values

    def __set_limit_import_on_file_size(self):
        values = {
            "label":       "Limit file import size",
            "tooltip":     f"Enable limiting the {ARR_NAME} notification on items over a set file size",
            "sub_setting": True,
        }
        if self.get_setting('mode') != 'import_mode':
            values["display"] = 'hidden'
        return values

    def __set_minimum_file_size(self):
        values = {
            "label":       "Minimum file size",
            "description": "Specify the minimum file size of a file that would trigger a notification",
            "sub_setting": True,
        }
        if self.get_setting('mode') != 'import_mode':
            values["display"] = 'hidden'
        elif not self.get_setting('limit_import_on_file_size'):
            values["display"] = 'disabled'
        return values

    def __set_webhook_admonition_note(self):
        description = (
            "Configure rules to link incoming webhooks to specific Unmanic libraries.<br>"
            "Rules are python expressions evaluated against the webhook payload.<br>"
            "Available variables:<br>"
            "<ul>"
            "<li><code>event_type</code>: The type of event (e.g. 'Grab', 'Download', 'Rename')</li>"
            f"<li><code>{ARR_TITLE_FIELD}</code>: The title of the {ARR_ENTITY_LABEL}</li>"
            f"<li><code>{ARR_ID_FIELD}</code>: The internal ID of the {ARR_ENTITY_LABEL}</li>"
            f"<li><code>{ARR_EXTERNAL_ID_FIELD}</code>: The {ARR_EXTERNAL_ID_LABEL} ID of the {ARR_ENTITY_LABEL}</li>"
            f"<li><code>root_path</code>: The root folder path for the {ARR_ENTITY_LABEL}</li>"
            f"<li><code>tags</code>: A list of tag labels applied to the {ARR_ENTITY_LABEL}</li>"
            f"<li><code>quality</code>: The quality profile name of the {ARR_FILE_LABEL} (e.g. '{ARR_QUALITY_EXAMPLE}')</li>"
            f"<li><code>path</code>: The absolute path to the {ARR_FILE_LABEL}</li>"
            "</ul>"
            "Examples:<br>"
            "<ul>"
            "<li><code>quality_profile == 'Ultra-HD' and '4k' in tags</code></li>"
            f"<li><code>root_path.startswith('{ARR_LIBRARY_EXAMPLE_PATH}')</code></li>"
            "<li><code>'Archive' in root_path</code></li>"
            "<li><code>'Animation' in tags</code></li>"
            "</ul>"
        )
        values = {
            "label":       "Note",
            "description": description,
            "input_type":  "section_admonition",
        }
        if self.library_id or not self.get_setting('api_key') or not self.get_setting('enable_webhook'):
            values["display"] = 'hidden'
        return values

    def __set_webhook_section_header(self):
        values = {
            "label":      "Webhooks",
            "input_type": "section_header",
        }
        if self.library_id or not self.get_setting('api_key'):
            values["display"] = 'hidden'
        return values

    def __set_enable_webhook(self):
        values = {
            "label":       "Enable Webhook Processing",
            "description": f"Allow this plugin to receive webhooks from {ARR_NAME} to trigger tasks.",
        }
        if self.library_id or not self.get_setting('api_key'):
            values["display"] = 'hidden'
        return values


def check_file_size_under_max_file_size(path, minimum_file_size):
    file_stats = os.stat(os.path.join(path))
    if int(humanfriendly.parse_size(minimum_file_size)) < int(file_stats.st_size):
        return False
    return True


# Arr-specific behavior
def create_api(host_url, api_key):
    return ARR_API_CLASS(host_url, api_key)


def get_arr_entity_from_processed_file(api, dest_path):
    # Radarr identifies the movie from a basename search against its lookup endpoint.
    basename = os.path.basename(dest_path)
    lookup_results = api.lookup_movie(term=str(basename))
    logger.debug("Lookup results: %s", pprint.pformat(lookup_results, indent=1))

    entity_data = {}
    if lookup_results and isinstance(lookup_results, list):
        for result in lookup_results:
            if result.get('id'):
                entity_data = result
                break

    return entity_data.get('title'), entity_data.get('id')


def queue_refresh(api, entity_id):
    return api.post_command(ARR_REFRESH_COMMAND_NAME, movieIds=[entity_id])


def rename_entity_files(api, entity_id):
    return api.post_command(ARR_RENAME_COMMAND_NAME, movieIds=[entity_id])


def get_import_command_kwargs(dest_path, download_id):
    # Import commands always use the final output path. When a queue match exists we
    # include the download client ID so the Arr app can associate the import properly.
    kwargs = {'path': os.path.abspath(dest_path)}
    if download_id:
        kwargs['downloadClientId'] = download_id
    return kwargs


def get_webhook_entity(payload):
    return payload.get('movie', {})


def get_webhook_root_path(entity):
    return entity.get('folderPath') or entity.get('path')


def get_webhook_file_records(payload):
    if isinstance(payload.get('movieFile'), dict):
        return [payload['movieFile']]
    if isinstance(payload.get('movieFiles'), list):
        return payload['movieFiles']
    return []


def build_webhook_rule_base(entity, root_path, event_type):
    return {
        'event_type':      event_type,
        'movie_title':     entity.get('title'),
        'movie_id':        entity.get('id'),
        'tmdb_id':         entity.get('tmdbId'),
        'root_path':       root_path,
        'tags':            entity.get('tags', []),
        'quality_profile': None,
        'quality':         None,
        'quality_version': None,
        'relative_path':   None,
        'path':            None,
    }


def enrich_webhook_rule_base(api, flat_data_base):
    if not flat_data_base.get('movie_id'):
        return

    movie_info = api.get_movie(flat_data_base['movie_id'])
    tag_ids = movie_info.get('tags', [])
    if tag_ids:
        all_tags = api.get_tag()
        flat_data_base['tags'] = [tag['label'] for tag in all_tags if tag['id'] in tag_ids]
        logger.debug("Resolved tags: %s", flat_data_base['tags'])

    quality_profile_id = movie_info.get('qualityProfileId')
    if quality_profile_id:
        profiles = api.get_quality_profile()
        for profile in profiles:
            if profile['id'] == quality_profile_id:
                flat_data_base['quality_profile'] = profile['name']
                break


def apply_file_record_to_rule_data(flat_data, file_record):
    flat_data['quality'] = file_record.get('quality')
    flat_data['quality_version'] = file_record.get('qualityVersion')
    flat_data['relative_path'] = file_record.get('relativePath')
    flat_data['path'] = file_record.get('path')


def get_root_directory_for_rule_match(root_path):
    if not root_path:
        return None
    return os.path.dirname(os.path.normpath(root_path))


def update_mode(api, dest_path, rename_files):
    # Update mode tells Arr to refresh metadata for an already-managed item after
    # Unmanic has modified the file in place.
    entity_title, entity_id = get_arr_entity_from_processed_file(api, dest_path)

    if not entity_id:
        logger.error("Missing %s ID. Failed to queue refresh of %s for file: '%s'",
                     ARR_ENTITY_LABEL, ARR_ENTITY_LABEL, dest_path)
        return

    logger.debug("Detected %s title: '%s' (ID: %s)", ARR_ENTITY_LABEL, entity_title, entity_id)

    try:
        result = queue_refresh(api, entity_id)
        logger.debug("Received result:\n%s", pprint.pformat(result, indent=1))

        if isinstance(result, dict) and result.get('message'):
            logger.error("Failed to queue refresh of %s ID '%s' for file: '%s'. %s message: %s",
                         ARR_ENTITY_LABEL, entity_id, dest_path, ARR_NAME, result['message'])
            return

        logger.info("Successfully queued refresh of %s '%s' for file: '%s'",
                    ARR_ENTITY_LABEL, entity_title, dest_path)
    except (PyarrUnauthorizedError, PyarrAccessRestricted, PyarrResourceNotFound, PyarrBadGateway,
            PyarrConnectionError) as err:
        logger.error("Failed to queue refresh of %s '%s' for file: '%s'. Error: %s",
                     ARR_ENTITY_LABEL, entity_title, dest_path, str(err))
        return
    except Exception as err:
        logger.error("An unexpected error occurred while queuing refresh for %s ID '%s': %s",
                     ARR_ENTITY_LABEL, entity_id, str(err))
        return

    if not rename_files:
        return

    logger.info("Waiting 10 seconds before triggering rename for %s '%s'...", ARR_ENTITY_LABEL, entity_title)
    time.sleep(10)  # Must give time (more than Radarr) for the refresh to complete before we run the rename.

    try:
        result = rename_entity_files(api, entity_id)

        # Rename runs after the refresh so Arr sees the updated media details first.
        logger.debug("Received result for '%s' command:\n%s", ARR_RENAME_COMMAND_NAME, pprint.pformat(result, indent=1))
        if isinstance(result, dict):
            logger.info("Successfully triggered rename of %s '%s' for file: '%s'",
                        ARR_ENTITY_LABEL, entity_title, dest_path)
        else:
            logger.error("Failed to trigger rename of %s ID '%s' for file: '%s'. Result: %s",
                         ARR_ENTITY_LABEL, entity_id, dest_path, str(result))
    except (PyarrUnauthorizedError, PyarrAccessRestricted, PyarrResourceNotFound, PyarrBadGateway,
            PyarrConnectionError) as err:
        logger.error("Failed to trigger rename of %s '%s' for file: '%s'. Error: %s",
                     ARR_ENTITY_LABEL, entity_title, dest_path, str(err))
    except Exception as err:
        logger.error("Failed to trigger rename of %s ID '%s' for file: '%s'. Error: %s",
                     ARR_ENTITY_LABEL, entity_id, dest_path, str(err))


def import_mode(api, source_path, dest_path):
    # Import mode is used when Unmanic processes a file before Arr has imported it.
    # We try to match the Arr queue first so the import can be associated with the
    # original download, then fall back to a plain path-based import.
    source_basename = os.path.basename(source_path)
    import_path = os.path.abspath(dest_path)

    download_id = None
    queue_title = None

    try:
        queue = api.get_queue()
        logger.debug("Current %s queue:\n%s", ARR_NAME, pprint.pformat(queue, indent=1))
        for item in queue.get('records', []):
            item_output_basename = os.path.basename(item.get('outputPath', ''))
            if item_output_basename == source_basename:
                download_id = item.get('downloadId')
                queue_title = item.get(ARR_QUEUE_LOOKUP_KEY)
                break
    except Exception as err:
        logger.error("Failed to fetch %s queue: %s", ARR_NAME, str(err))

    try:
        command_kwargs = get_import_command_kwargs(dest_path, download_id)
        if download_id:
            logger.info("Queued import %s '%s' using downloadClientId: '%s' for path '%s'",
                        ARR_ENTITY_LABEL, queue_title, download_id, import_path)
        else:
            logger.info("Queued import using just the file path '%s'", import_path)

        result = api.post_command(ARR_QUEUE_COMMAND_NAME, **command_kwargs)
        if isinstance(result, dict) and result.get('message'):
            logger.error("Failed to queue import of file: '%s'. %s message: %s",
                         dest_path, ARR_NAME, result['message'])
            return

        logger.info("Successfully queued import of file in %s: '%s'", ARR_NAME, dest_path)
        logger.debug("Queued import result: %s", pprint.pformat(result, indent=1))
    except Exception as err:
        logger.error("Failed to queue import of file '%s' in %s: %s", dest_path, ARR_NAME, str(err))


def process_files(settings, source_file, destination_files, host_url, api_key):
    api = create_api(host_url, api_key)

    mode = settings.get_setting('mode')
    rename_files = settings.get_setting('rename_files')

    for dest_file in destination_files:
        if mode == 'update_mode':
            update_mode(api, dest_file, rename_files)
        elif mode == 'import_mode':
            if settings.get_setting('limit_import_on_file_size'):
                minimum_file_size = settings.get_setting('minimum_file_size')
                if check_file_size_under_max_file_size(dest_file, minimum_file_size):
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
    settings = Settings(library_id=data.get('library_id'))

    if not data.get('task_processing_success'):
        logger.debug("Skipping notify_%s as the task was not successful.", ARR_NAME_LOWER)
        return
    if not data.get('file_move_processes_success'):
        logger.debug("Skipping notify_%s as the file move processes were not successful.", ARR_NAME_LOWER)
        return

    # Fetch destination and source files
    source_file = data.get('source_data', {}).get('abspath')
    destination_files = data.get('destination_files', [])

    # Setup API
    host_url = settings.get_setting('host_url')
    api_key = settings.get_setting('api_key')

    if not api_key:
        logger.error("%s API Key is not configured. Skipping notification.", ARR_NAME)
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
            payload = json.loads(data.get('body', b'').decode('utf-8'))
        except Exception as err:
            logger.error("Failed to parse webhook JSON: %s", str(err))
            data['status'] = 400
            data['content'] = {"error": "Invalid JSON"}
            return

        logger.debug("Received %s webhook: %s", ARR_NAME, pprint.pformat(payload))

        # Only Download events are actionable. Test events are acknowledged so users
        # can verify connectivity from the Arr app UI.
        event_type = payload.get('eventType')
        if isinstance(event_type, str) and event_type.strip().lower() == 'test':
            logger.info(ARR_WEBHOOK_TEST_MESSAGE)
            data['status'] = 200
            data['content'] = {"success": True, "message": "Test successful"}
            return

        if event_type != 'Download':
            logger.info("Ignoring %s webhook event type '%s'", ARR_NAME, event_type)
            data['content'] = {"success": True, "message": "Ignored webhook event type"}
            return

        entity = get_webhook_entity(payload)
        root_path = get_webhook_root_path(entity)
        file_records = get_webhook_file_records(payload)

        if not file_records:
            logger.info("Ignoring %s webhook without %s details (event type '%s')",
                        ARR_NAME, ARR_FILE_LABEL, event_type)
            data['content'] = {"success": True, "message": f"Ignored webhook without {ARR_FILE_LABEL} details"}
            return

        flat_data_base = build_webhook_rule_base(entity, root_path, event_type)

        try:
            # Enrich the webhook payload with live Arr data so rule queries can use
            # resolved tag labels and quality profile names instead of raw IDs.
            api = create_api(settings.get_setting('host_url'), settings.get_setting('api_key'))
            enrich_webhook_rule_base(api, flat_data_base)
        except Exception as err:
            logger.warning("Failed to fetch additional info from %s: %s", ARR_NAME, str(err))

        configured = settings.get_setting()
        library_paths = {lib['id']: lib['path'] for lib in Library.get_all_libraries()}
        matched_rules = []

        for file_record in file_records:
            # Rules are evaluated per file record so a single webhook can match more
            # than one file when Arr includes multiple file objects in the payload.
            flat_data = dict(flat_data_base)
            apply_file_record_to_rule_data(flat_data, file_record)

            file_path = flat_data.get('path')
            if not file_path and root_path and flat_data.get('relative_path'):
                file_path = os.path.join(root_path, flat_data.get('relative_path'))
                flat_data['path'] = file_path

            if not file_path:
                logger.error("Unable to determine absolute file path for webhook payload")
                continue

            if root_path and not os.path.normpath(file_path).startswith(os.path.normpath(root_path)):
                logger.info("Ignoring webhook for file outside %s root: '%s'", ARR_ENTITY_LABEL, file_path)
                continue

            logger.debug("Evaluated data for rules: %s", pprint.pformat(flat_data))

            for key in configured:
                if not key.startswith('rule_query_'):
                    continue

                query = configured.get(key)
                if not query:
                    continue

                index = key.split('_')[-1]
                library_id = configured.get(f'library_id_{index}')
                if not library_id:
                    continue

                try:
                    safe_query = re.sub(r'\bAND\b', 'and', query)
                    safe_query = re.sub(r'\bOR\b', 'or', safe_query)
                    if not simple_eval(safe_query, names=flat_data):
                        continue

                    library_id = int(library_id)
                    library_path = library_paths.get(library_id)
                    if not library_path:
                        logger.error("No library path found for Library ID %s", library_id)
                        continue

                    arr_root_dir = get_root_directory_for_rule_match(root_path)
                    if not arr_root_dir:
                        logger.error("Unable to determine %s root directory for file '%s'", ARR_NAME, file_path)
                        continue

                    if not os.path.normpath(file_path).startswith(arr_root_dir):
                        logger.error("File path '%s' is outside %s root '%s'", file_path, ARR_NAME, arr_root_dir)
                        continue

                    relative_path = os.path.relpath(file_path, arr_root_dir)
                    unmanic_path = os.path.normpath(os.path.join(library_path, relative_path))

                    logger.info("Rule '%s' matched. Associated with Library ID %s", query, library_id)
                    matched_rules.append({'library_id': library_id, 'index': index, 'path': unmanic_path})
                except Exception as err:
                    logger.error("Error evaluating rule '%s': %s", query, str(err))

        triggered_actions = []
        if not matched_rules:
            logger.error("No matching library found for webhook payload")
            data['content'] = {"success": False, "message": "No rules matched for webhook payload"}
            return

        for rule in matched_rules:
            library_id = rule['library_id']
            index = rule['index']
            file_path = rule['path']

            # Matching a rule can either run a library file test only, or also create
            # a pending task when the file test says processing is needed.
            trigger_test = settings.get_setting(f'trigger_test_path_{index}')
            create_task = settings.get_setting(f'create_task_{index}')

            if trigger_test is None:
                trigger_test = True

            if not trigger_test:
                logger.info("Skipping test for path '%s' in library %s (Rule %s) - Action disabled",
                            file_path, library_id, index)
                continue

            logger.info("Triggering test for path '%s' in library %s (Rule %s)", file_path, library_id, index)
            result = pending_tasks.test_path_for_pending_task(file_path, library_id=library_id)

            if create_task and result and result.get('add_file_to_pending_tasks'):
                logger.info("File '%s' needs processing. Creating pending task in library %s", file_path, library_id)
                pending_tasks.create_task(
                    file_path,
                    library_id=library_id,
                    priority_score=result.get('priority_score', 0),
                )
                triggered_actions.append({'library_id': library_id, 'action': 'create_task', 'rule_index': index})
            else:
                triggered_actions.append({'library_id': library_id, 'action': 'test_only', 'rule_index': index})

        data['content'] = {"success": True, "triggered_actions": triggered_actions}
    except Exception as err:
        logger.error("Exception in render_plugin_api: %s\n%s", str(err), traceback.format_exc())
        data['status'] = 500
        data['content'] = {"error": "Internal Server Error"}
