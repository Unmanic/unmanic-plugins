#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.database.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     26 Aug 2021, (9:06 AM)

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

from peewee import *
from playhouse.shortcuts import model_to_dict
import os

db = DatabaseProxy()  # Create a proxy for our db.


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


class Database(object):

    def __init__(self, settings, logger):
        self.settings = settings
        self.logger = logger

    @staticmethod
    def select_database(db_file):
        # use SqliteQueueDatabase
        database = SqliteDatabase(
            db_file,
            pragmas=(
                ('foreign_keys', 1),
                ('journal_mode', 'wal'),
            )
        )
        db.initialize(database)
        return db

    @staticmethod
    def close():
        if not db.is_closed():
            db.close()

    @staticmethod
    def db():
        return db

    def get_legacy_db_file(self):
        profile_directory = self.settings.get_plugin_directory()
        return os.path.abspath(os.path.join(profile_directory, '..', '..', 'config', 'unmanic.db'))

    def get_db_file(self):
        profile_directory = self.settings.get_profile_directory()
        return os.path.abspath(os.path.join(profile_directory, 'history.db'))

    def create_db_schema(self):
        new_db_file = self.get_db_file()
        # Create required tables in new DB
        db_connection = Database.select_database(new_db_file)
        db_connection.connect()
        db_connection.create_tables([HistoricTasks, HistoricTaskProbe], safe=True)
        db_connection.close()

    def migrate_data(self):
        historic_tasks_to_migrate = []
        new_db_file = self.get_db_file()
        legacy_db_file = self.get_legacy_db_file()

        if os.path.exists(new_db_file):
            # Dont migrate data. The database already exists
            return

        # Create required tables in new DB
        self.create_db_schema()

        # Fetch data from old database (if data exists)
        db_connection = Database.select_database(legacy_db_file)
        try:
            query = (
                HistoricTasks.select(
                    HistoricTasks.id,
                    HistoricTasks.task_label,
                    HistoricTasks.task_success,
                    HistoricTasks.start_time,
                    HistoricTasks.finish_time,
                    HistoricTaskProbe.type,
                    HistoricTaskProbe.abspath,
                    HistoricTaskProbe.basename,
                    HistoricTaskProbe.size
                )
            )
            predicate = (
                    (HistoricTaskProbe.historictask_id == HistoricTasks.id) &
                    (
                            ((HistoricTasks.task_success == True) & (HistoricTaskProbe.type == "destination"))
                            |
                            ((HistoricTasks.task_success == True) & (HistoricTaskProbe.type == "source"))
                    )
            )
            results = query.join(HistoricTaskProbe, on=predicate)

            # Loop over results and add them to the historic_tasks_to_migrate list
            for record in results:
                historic_tasks_to_migrate.append(record)
            # Close connection
            db_connection.close()
        except Exception:
            # No historic entries exist yet
            self.logger.exception("Failed to import old historic data.")
            # Close connection
            db_connection.close()
            return

        # Add old data to new DB
        db_connection = Database.select_database(new_db_file)
        try:
            for record in historic_tasks_to_migrate:
                # Add historic record to new DB
                historic_task, created = HistoricTasks.get_or_create(id=record.id)
                historic_task.task_label = record.task_label
                historic_task.task_success = record.task_success
                historic_task.start_time = datetime.datetime.fromtimestamp(record.start_time)
                historic_task.finish_time = datetime.datetime.fromtimestamp(record.finish_time)
                historic_task.save()

                # Create probe entries
                historic_task_probe, created = HistoricTaskProbe.get_or_create(
                    historictask_id=record.id,
                    type=record.historictaskprobe.type
                )
                historic_task_probe.abspath = record.historictaskprobe.abspath
                historic_task_probe.basename = record.historictaskprobe.basename
                historic_task_probe.size = record.historictaskprobe.size
                historic_task_probe.save()

            db_connection.close()
        except Exception:
            # No historic entries exist yet
            self.logger.exception("Failed to migrate old historic data.")
            # Close connection
            db_connection.close()
