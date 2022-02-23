#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     25 April 2021, (3:41 AM)

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
import json
import logging
import os
import uuid
import datetime
from operator import attrgetter

from peewee import *
from playhouse.shortcuts import model_to_dict
from playhouse.sqliteq import SqliteQueueDatabase

from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.file_size_metrics")


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
                start_time = task.get('start_time').isoformat()
            finish_time = ''
            if task.get('finish_time'):
                finish_time = task.get('finish_time').isoformat()
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

    def save_source_item(self, abspath, size, task_success=False):
        self.db_start()

        basename = os.path.basename(abspath)
        task_label = basename
        start_time = datetime.datetime.now()
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

    def save_destination_item(self, task_id, abspath, size):
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
            historic_task.finish_time = datetime.datetime.now()
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


def save_source_size(abspath, size):
    # Return a list of historical tasks based on the request JSON body
    data = Data()
    task_id = data.save_source_item(abspath, size)

    return task_id


def save_destination_size(task_id, abspath, size):
    # Return a list of historical tasks based on the request JSON body
    data = Data()
    success = data.save_destination_item(task_id, abspath, size)

    return success


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
    # Get the path to the file
    abspath = data.get('original_file_path')
    source_size = os.path.getsize(abspath)

    # Store size metric in file for now...
    # The DB should only be updated by a single thread. The workers are multi-threaded.
    profile_directory = settings.get_profile_directory()
    # Use the basename of the source path to create a unique file for storing the file_out data.
    # This can then be read and used by the on_postprocessor_task_results function below.
    src_file_hash = hashlib.md5(abspath.encode('utf8')).hexdigest()
    plugin_data_file = os.path.join(profile_directory, '{}.json'.format(src_file_hash))

    with open(plugin_data_file, 'w') as f:
        required_data = {
            'source_size': source_size,
        }
        json.dump(required_data, f, indent=4)

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
    # Get the original file's absolute path
    original_source_path = data.get('source_data', {}).get('abspath')
    if not original_source_path:
        logger.error("Provided 'source_data' is missing the source file abspath data.")
        return data

    # Read the data from the on_worker_process runner
    profile_directory = settings.get_profile_directory()

    # Get the file out and store (if it exists)
    src_file_hash = hashlib.md5(original_source_path.encode('utf8')).hexdigest()
    plugin_data_file = os.path.join(profile_directory, '{}.json'.format(src_file_hash))
    if os.path.exists(plugin_data_file):
        # The store exists
        with open(plugin_data_file) as infile:
            task_metadata = json.load(infile)
        source_size = task_metadata.get('source_size')
    else:
        # The store did not exist, resort to fetching the data from the original source file (hopefully unchanged)
        logger.warning("Plugin data file is missing. Fetching source size direct from source path.")
        source_size = os.path.getsize(data.get('source_data', {}).get('abspath'))

    if not source_size:
        logger.error("Plugin data file is missing 'source_size'.")
        return data
    task_id = save_source_size(original_source_path, source_size)
    if task_id is None:
        logger.error("Failed to create source size entry for this file")
        return data

    # For each of the destination files, write a file size metric entry
    for dest_file in data.get('destination_files', []):
        abspath = os.path.abspath(dest_file)
        # Add a destination file entry if the file actually exists
        if os.path.exists(abspath):
            size = os.path.getsize(abspath)
            save_destination_size(task_id, abspath, size)
        else:
            logger.info("Skipping file '{}' as it does not exist.".format(abspath))

    return data


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

    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'index.html'))) as f:
        content = f.read()
        data['content'] = content.replace("{cache_buster}", str(uuid.uuid4()))

    return data
