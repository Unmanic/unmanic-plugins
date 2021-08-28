#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.history.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     25 Aug 2021, (8:51 PM)

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
import datetime
import os.path
from operator import attrgetter

from file_size_metrics.lib.database import Database, HistoricTasks, HistoricTaskProbe


class Data(object):

    def __init__(self, settings, logger):
        self.settings = settings
        self.logger = logger
        self.db = Database(settings, logger)
        self.create_db_connection()

    @staticmethod
    def close():
        Database.close()

    def create_db_connection(self):
        # First migrate old data if required
        self.db.migrate_data()
        # Create database schema
        self.db.create_db_schema()

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
            self.logger.warning("No historic tasks exist yet.")
            query = []

        return query.dicts()

    def get_history_probe_data(self, task_probe_id):
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

        return results

    def calculate_total_file_size_difference(self):
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

        return results

    def prepare_filtered_historic_tasks(self, request_dict):
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
        return return_data

    def save_source_item(self, abspath, size, task_success=False):
        basename = os.path.basename(abspath)
        task_label = basename
        start_time = datetime.datetime.now()
        finish_time = None

        db = Database.db()
        with db.atomic() as transaction:
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
                transaction.rollback()
                task_id = None
                self.logger.exception("Failed to save historic data to database.")
        return task_id

    def save_destination_item(self, task_id, abspath, size):
        basename = os.path.basename(abspath)
        db = Database.db()
        with db.atomic() as transaction:
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
                transaction.rollback()
                self.logger.exception("Failed to save historic data to database.")
                return False

        # Update the original entry
        with db.atomic() as transaction:
            try:
                historic_task, created = HistoricTasks.get_or_create(id=task_id)
                historic_task.finish_time = datetime.datetime.now()
                historic_task.task_success = True
                historic_task.save()
            except Exception:
                transaction.rollback()
                self.logger.exception("Failed to save historic data to database.")
                return False
        return True
