# This file is part of the sURLy project
#
# The MIT License (MIT)
#
# Copyright (c) 2019-2020 Nicko van Someren
#               2020 Absolute Software
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# SPDX-License-Identifier: MIT


"""An abstract datastore presented as set of key/value dictionaries,
backed by a DynamoDB table, with optional simplistic local caching"""

import logging

import boto3

LOGGER = logging.getLogger(__name__)

# pylint: disable=too-few-public-methods
class DataStore:
    """An datastore handling multiple tables, backed by a single DynamoDB table, with
    simplistic local caching.
    """
    class _MapHelper:
        """Helper for maps"""
        def __init__(self, parent, subtable, cached=True):
            self._parent = parent
            self._subtable = subtable
            self._cache = {} if cached else None

        def __getitem__(self, key):
            if self._cache is not None and key in self._cache:
                return self._cache[key]
            return self._parent._fetch_item(self._subtable, key)

        def __contains__(self, key):
            if self._cache is not None and key in self._cache:
                return True
            return self._parent._fetch_item(self._subtable, key) is not None

        def __setitem__(self, key, value):
            self._parent._store_item(self._subtable, key, value)
            if self._cache is not None:
                self._cache[key] = value

        def __delitem__(self, key):
            self._parent._delete_item(self._subtable, key)

    def __init__(self, table_name, sub_stores, uncached=None):
        self._db_client = boto3.client('dynamodb')
        self._db = boto3.resource('dynamodb')

        self._table_name = table_name

        if not self._database_available():
            self._create_database_tables()

        self._table = self._db.Table(table_name) # pylint: disable=no-member

        if  uncached is None:
            uncached = []

        for store in sub_stores:
            setattr(self, store, self._MapHelper(self, store.upper(), store not in uncached))

    def _store_item(self, subtable, key, value):
        LOGGER.debug("Adding mapping from key %s to value %s", key, value)
        self._table.put_item(Item={
            'SUBTABLE': subtable,
            'KEY': key,
            'VALUE': value,
        })

    def _fetch_item(self, subtable, key):
        result = self._table.get_item(Key={'SUBTABLE':subtable, 'KEY':key})
        item = result.get('Item', None)
        return item['VALUE'] if item else None

    def _delete_item(self, subtable, key):
        self._table.delete_item(Key={'SUBTABLE':subtable, 'KEY':key})

    def _database_available(self):
        client = self._db_client
        try:
            client.describe_table(TableName=self._table_name)
            return True
        except client.exceptions.ResourceNotFoundException:
            return False

    def _create_database_tables(self):
        client = self._db_client
        try:
            client.create_table(
                TableName=self._table_name,
                AttributeDefinitions=[
                    {'AttributeName': 'SUBTABLE', 'AttributeType': 'S'},
                    {'AttributeName': 'KEY', 'AttributeType': 'S'},
                ],
                KeySchema=[
                    {'AttributeName': 'SUBTABLE', 'KeyType': 'HASH'},
                    {'AttributeName': 'KEY', 'KeyType': 'RANGE'},
                ],
                BillingMode='PAY_PER_REQUEST',
            )
        except client.exceptions.ResourceInUseException:
            # The table seems to already exist; we must have raced someone for it
            pass
