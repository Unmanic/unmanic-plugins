#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Written by:               Josh.5 <jsunnex@gmail.com>, gwlsn
    Date:                     2 December 2025, (7:09 PM)

    Copyright:
        Copyright (C) 2025 Josh Sunnex

        This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
        Public License as published by the Free Software Foundation, version 3.

        This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
        implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
        for more details.

        You should have received a copy of the GNU General Public License along with this program.
        If not, see <https://www.gnu.org/licenses/>.

"""
import json
import os
import uuid
import datetime
from operator import attrgetter

from peewee import *
from playhouse.shortcuts import model_to_dict
from playhouse.sqliteq import SqliteQueueDatabase

from unmanic.libs.logs import UnmanicLogging
from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = UnmanicLogging.get_logger(name='Unmanic.Plugin.file_size_metrics')


class Settings(PluginSettings):
    settings = {}


settings = Settings()
profile_directory = settings.get_profile_directory()
db_file = os.path.abspath(os.path.join(profile_directory, 'history.db'))
db = SqliteQueueDatabase(
    db_file,
    use_gevent=False,
    autostart=False,
    queue_max_size=None,
    results_timeout=15.0,
    pragmas=(
        ('foreign_keys', 1),
        ('journal_mode', 'wal'),
    )
)


class BaseModel(Model):
    """
    BaseModel

    Generic configuration and methods used across all Model classes
    """

    class Meta:
        database = db

    def model_to_dict(self):
        """
        Retrieve all related objects recursively and
        then converts the resulting objects to a dictionary.

        :return:
        """
        return model_to_dict(self, backrefs=True)


class HistoricTasks(BaseModel):
    """
    HistoricTasks
    """
    task_label = TextField(null=False, default='UNKNOWN')
    task_success = BooleanField(null=False, default='UNKNOWN')
    start_time = DateTimeField(null=False, default=datetime.datetime.now)
    finish_time = DateTimeField(null=True)


class HistoricTaskProbe(BaseModel):
    """
    HistoricTaskMetrics
    """
    historictask_id = ForeignKeyField(HistoricTasks)
    type = TextField(null=False, default='source')
    abspath = TextField(null=True, default='UNKNOWN')
    basename = TextField(null=True, default='UNKNOWN')
    size = TextField(null=False, default='0')


class Data(object):

    def __init__(self):
        self.create_db_schema()

    def db_start(self):
        db.start()
        db.connect()

    def db_stop(self):
        db.close()
        # db.stop()

    def clear_all_data(self):
        """
        Clear all historical data from the database.
        Returns True if successful, False otherwise.
        """
        self.db_start()
        try:
            # Delete all probe data first (foreign key constraint)
            HistoricTaskProbe.delete().execute()
            # Then delete all task records
            HistoricTasks.delete().execute()
            logger.info("All file size metrics data has been cleared.")
            success = True
        except Exception:
            logger.exception("Failed to clear historical data from database.")
            success = False
        self.db_stop()
        return success

    def create_db_schema(self):
        # Create required tables in new DB
        self.db_start()
        logger.debug("Ensuring history database schema exists")
        db.create_tables([HistoricTasks, HistoricTaskProbe], safe=True)
        self.db_stop()

    def get_total_historic_task_list_count(self):
        query = HistoricTasks.select().order_by(HistoricTasks.id.desc())
        return query.count()

    def get_historic_task_list_filtered_and_sorted(self, order=None, start=0, length=None, search_value=None, ):
        try:
            query = (
                HistoricTaskProbe.select(
                    HistoricTaskProbe.id,
                    HistoricTaskProbe.type,
                    HistoricTaskProbe.abspath,
                    HistoricTaskProbe.basename,
                    HistoricTasks.task_success,
                    HistoricTasks.start_time,
                    HistoricTasks.finish_time
                )
            )

            if search_value:
                query = query.where(HistoricTasks.task_label.contains(search_value))

            predicate = (
                    (HistoricTaskProbe.historictask_id == HistoricTasks.id) &
                    (
                        (HistoricTaskProbe.type == "destination")
                    )
            )

            query = query.join(HistoricTasks, on=predicate)

            # Get order by
            if order:
                sort_table = HistoricTasks
                if order.get("column") in ['basename']:
                    sort_table = HistoricTaskProbe

                if order.get("dir") == "asc":
                    order_by = attrgetter(order.get("column"))(sort_table).asc()
                else:
                    order_by = attrgetter(order.get("column"))(sort_table).desc()

                if length:
                    query = query.order_by(order_by).limit(length).offset(start)

        except HistoricTasks.DoesNotExist:
            # No historic entries exist yet
            logger.warning("No historic tasks exist yet.")
            query = []

        return query.dicts()

    def get_history_probe_data(self, task_probe_id):
        self.db_start()

        historictask = HistoricTaskProbe.select(HistoricTaskProbe.historictask_id).where(
            HistoricTaskProbe.id == task_probe_id).get()

        historictask_id = historictask.historictask_id

        query = HistoricTaskProbe.select(
            HistoricTaskProbe.id,
            HistoricTaskProbe.type,
            HistoricTaskProbe.abspath,
            HistoricTaskProbe.basename,
            HistoricTaskProbe.size,
        )

        # query = query.where(HistoricTaskProbe.abspath.in_([abspath]))
        query = query.where(
            ((HistoricTaskProbe.historictask_id == historictask_id) & (HistoricTaskProbe.type == 'source'))
            |
            (HistoricTaskProbe.id == task_probe_id)
        )

        # Iterate over historical tasks and append them to the task data
        results = []
        for task in query:
            # Set params as required in template
            item = {
                'id':       task.id,
                'type':     task.type,
                'abspath':  task.abspath,
                'basename': task.basename,
                'size':     task.size,
            }
            results.append(item)

        self.db_stop()
        return results

    def calculate_total_file_size_difference(self):
        self.db_start()

        # Only show results for successful records
        results = {}
        from peewee import fn

        # Get all source files
        source_query = HistoricTaskProbe.select(
            fn.SUM(HistoricTaskProbe.size).alias('total')
        )
        source_query = source_query.where(
            (HistoricTaskProbe.type == 'source') & (HistoricTasks.task_success)
        )
        predicate = (
                HistoricTaskProbe.historictask_id == HistoricTasks.id
        )
        source_query = source_query.join(HistoricTasks, on=predicate)

        # Get all destination files
        destination_query = HistoricTaskProbe.select(
            fn.SUM(HistoricTaskProbe.size).alias('total')
        )
        destination_query = destination_query.where(
            (HistoricTaskProbe.type == 'destination') & (HistoricTasks.task_success)
        )
        predicate = (
                HistoricTaskProbe.historictask_id == HistoricTasks.id
        )
        destination_query = destination_query.join(HistoricTasks, on=predicate)

        for r in source_query:
            results['source'] = r.total
        for r in destination_query:
            results['destination'] = r.total

        self.db_stop()
        return results

    def prepare_filtered_historic_tasks(self, request_dict):
        self.db_start()

        # Generate filters for query
        draw = request_dict.get('draw')
        start = request_dict.get('start')
        length = request_dict.get('length')

        search = request_dict.get('search')
        search_value = search.get("value")

        # Get sort order
        filter_order = request_dict.get('order')[0]
        order_direction = filter_order.get('dir', 'desc')
        columns = request_dict.get('columns')
        order_column_name = columns[filter_order.get('column')].get('name', 'finish_time')
        order = {
            "column": order_column_name,
            "dir":    order_direction,
        }

        # Get total count
        records_total_count = self.get_total_historic_task_list_count()

        # Get quantity after filters (without pagination)
        records_filtered_count = self.get_historic_task_list_filtered_and_sorted(order=order, start=0, length=0,
                                                                                 search_value=search_value).count()

        # Get filtered/sorted results
        task_results = self.get_historic_task_list_filtered_and_sorted(order=order, start=start, length=length,
                                                                       search_value=search_value)

        # Build return data
        return_data = {
            "draw":            draw,
            "recordsTotal":    records_total_count,
            "recordsFiltered": records_filtered_count,
            "successCount":    0,
            "failedCount":     0,
            "data":            []
        }

        # Iterate over historical tasks and append them to the task data
        for task in task_results:
            start_time = ''
            if task.get('start_time'):
                start_time = task.get('start_time').strftime('%Y-%m-%d %H:%M:%S')
            finish_time = ''
            if task.get('finish_time'):
                finish_time = task.get('finish_time').strftime('%Y-%m-%d %H:%M:%S')
            # Set params as required in template
            item = {
                'id':           task.get('id'),
                'basename':     task.get('basename'),
                'abspath':      task.get('abspath'),
                'task_success': task.get('task_success'),
                'start_time':   start_time,
                'finish_time':  finish_time,
            }
            # Increment counters
            if item['task_success']:
                return_data["successCount"] += 1
            else:
                return_data["failedCount"] += 1
            return_data["data"].append(item)

        # Return results
        self.db_stop()
        return return_data

    def save_source_item(self, abspath, size, start_time=None, task_success=False):
        self.db_start()

        basename = os.path.basename(abspath)
        task_label = basename
        start_time = start_time if start_time is not None else datetime.datetime.now()
        finish_time = None
        try:
            new_historic_task = HistoricTasks.create(
                task_label=task_label,
                task_success=task_success,
                start_time=start_time,
                finish_time=finish_time
            )
            # Create probe entry for source item
            HistoricTaskProbe.create(
                historictask_id=new_historic_task,
                type='source',
                abspath=abspath,
                basename=basename,
                size=size
            )
            task_id = new_historic_task.id
        except Exception:
            task_id = None
            logger.exception("Failed to save historic data to database.")
        self.db_stop()
        return task_id

    def save_destination_item(self, task_id, abspath, size, finish_time):
        self.db_start()

        basename = os.path.basename(abspath)
        try:
            # Create probe entry for source item
            HistoricTaskProbe.create(
                historictask_id=task_id,
                type='destination',
                abspath=abspath,
                basename=basename,
                size=size
            )
        except Exception:
            logger.exception("Failed to save historic data to database.")
            self.db_stop()
            return False

        # Update the original entry
        try:
            historic_task, created = HistoricTasks.get_or_create(id=task_id)
            historic_task.finish_time = finish_time
            historic_task.task_success = True
            historic_task.save()
        except Exception:
            logger.exception("Failed to save historic data to database.")
            self.db_stop()
            return False

        self.db_stop()
        return True


def get_historical_data(data):
    results = []
    arguments = data.get('arguments')
    request_body = arguments.get('data', [])
    if request_body:
        request_dict = json.loads(request_body[0])
        # Return a list of historical tasks based on the request JSON body
        data = Data()
        results = data.prepare_filtered_historic_tasks(request_dict)

    return json.dumps(results, indent=2)


def get_historical_data_details(data):
    results = []
    arguments = data.get('arguments')
    task_id = arguments.get('task_id', [])
    if task_id:
        # Return a list of historical tasks based on the request JSON body
        data = Data()
        results = data.get_history_probe_data(task_id)

    return json.dumps(results, indent=2)


def get_total_size_change_data_details(data):
    # Return a list of historical tasks based on the request JSON body
    data = Data()
    results = data.calculate_total_file_size_difference()

    return json.dumps(results, indent=2)


def reset_all_metrics(data):
    """
    Reset all metrics data by clearing the database.
    Returns JSON with success status.
    """
    data_handler = Data()
    success = data_handler.clear_all_data()
    results = {
        'success': success,
        'message': 'All metrics have been reset.' if success else 'Failed to reset metrics.'
    }
    return json.dumps(results, indent=2)


def save_source_details(abspath, size, start_time=None):
    # Return a list of historical tasks based on the request JSON body
    data = Data()
    task_id = data.save_source_item(abspath, size, start_time=start_time)

    return task_id


def save_destination_size(task_id, abspath, size, finish_time):
    # Return a list of historical tasks based on the request JSON body
    data = Data()
    success = data.save_destination_item(task_id, abspath, size, finish_time)

    return success


def emit_task_scheduled(data, store):
    """
    Runner function - emit data when a task is scheduled for execution on a worker.

    The 'data' object argument includes:
        library_id                - Integer, the ID of the library.
        task_id                   - Integer, unique identifier of the task.
        task_type                 - String, "local" or "remote". Indicates how this task is going to be processed.
        task_schedule_type        - String, either "local" or "remote". Where are we scheduling this task?
        remote_installation_info  - Dict, for remote tasks contains:
                                      - uuid:    String, the installation UUID.
                                      - address: String, the remote worker address.
                                    Empty dict for local tasks.
        source_data               - Dict, details of the task being scheduled:
                                      - abspath: String, absolute path to the file.
                                      - basename: String, file name.

    :param store:
    :param data:
    :return:

    """
    if data.get("task_type") == "remote":
        # This plugin will only run for tasks on the main installation. Remote tasks are duplicates created on remote installations.
        return

    # Get the path to the file
    abspath = data.get('source_data', {})["abspath"]
    source_size = os.path.getsize(abspath)

    # Store this data in the shared state
    store.set_runner_value("source_size", source_size)


def on_postprocessor_task_results(data, store):
    """
    Runner function - provides a means for additional postprocessor functions based on the task success.

    The 'data' object argument includes:
        library_id                      - The library that the current task is associated with.
        task_id                         - Integer, unique identifier of the task.
        task_type                       - String, "local" or "remote".
        final_cache_path                - The path to the final cache file that was then used as the source for all destination files.
        task_processing_success         - Boolean, did all task processes complete successfully.
        file_move_processes_success     - Boolean, did all postprocessor movement tasks complete successfully.
        destination_files               - List containing all file paths created by postprocessor file movements.
        source_data                     - Dictionary containing data pertaining to the original source file.
        start_time                      - Float, UNIX timestamp when the task began.
        finish_time                     - Float, UNIX timestamp when the task completed.

    :param store:
    :param data:
    :return:

    """
    # Only run this for successfully processed tasks
    if not data.get('task_processing_success', False):
        logger.info("Ignoring recording task results for task as it did not succeed.")
        return

    # Get the original file's absolute path
    original_source_path = data.get('source_data', {}).get('abspath')
    if not original_source_path:
        logger.error("Provided 'source_data' is missing the source file abspath data.")
        return

    # Read start/finish times from provided data
    unix_start_time = data.get('start_time')
    if not unix_start_time:
        logger.error("The 'start_time' is missing the data.")
        return
    start_time = datetime.datetime.fromtimestamp(unix_start_time)
    unix_finish_time = data.get('finish_time')
    if not unix_finish_time:
        logger.error("The 'finish_time' is missing the data.")
        return
    finish_time = datetime.datetime.fromtimestamp(unix_finish_time)

    # Read source_size from data store
    source_size = store.get_runner_value("source_size", runner="emit_task_scheduled")
    if source_size is None:
        # Something is going wrong here. The data is no longer in the store.
        logger.error("The 'source_size' is missing from the task data store.")

    # For each of the destination files, write a file size metric entry
    dest_abspath = None
    dest_size = None
    for dest_file in data.get('destination_files', []):
        dest_abspath = os.path.abspath(dest_file)
        # Add a destination file entry if the file actually exists
        if os.path.exists(dest_abspath):
            dest_size = os.path.getsize(dest_abspath)
        else:
            logger.info("Skipping file '{}' as it does not exist.".format(dest_abspath))

    if dest_abspath is None or dest_size is None:
        logger.error("Failed to get the file size of the destination file.")
        return

    size_difference = dest_size - source_size
    processing_duration = unix_finish_time - unix_start_time
    data_search_key = f"{data.get('task_id')} | {data.get('library_id')} | {original_source_path}"
    UnmanicLogging.data("file_size_metrics",
                        data_search_key=data_search_key,
                        source_abspath=original_source_path,
                        dest_abspath=dest_abspath,
                        source_size=source_size,
                        dest_size=dest_size,
                        size_difference=size_difference,
                        start_time=start_time,
                        finish_time=finish_time,
                        processing_duration=processing_duration)

    task_id = save_source_details(original_source_path, source_size, start_time)
    if task_id is None:
        logger.error("Failed to create source size entry for this file")
    save_destination_size(task_id, dest_abspath, dest_size, finish_time)


def render_frontend_panel(data):
    if data.get('path') in ['list', '/list', '/list/']:
        data['content_type'] = 'application/json'
        data['content'] = get_historical_data(data)
        return

    if data.get('path') in ['conversionDetails', '/conversionDetails', '/conversionDetails/']:
        data['content_type'] = 'application/json'
        data['content'] = get_historical_data_details(data)
        return

    if data.get('path') in ['totalSizeChange', '/totalSizeChange', '/totalSizeChange/']:
        data['content_type'] = 'application/json'
        data['content'] = get_total_size_change_data_details(data)
        return

    if data.get('path') in ['resetMetrics', '/resetMetrics', '/resetMetrics/']:
        data['content_type'] = 'application/json'
        data['content'] = reset_all_metrics(data)
        return

    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'index.html'))) as f:
        content = f.read()
        data['content'] = content.replace("{cache_buster}", str(uuid.uuid4()))

    return data
