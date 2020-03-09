#!/usr/bin/env python

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
"""A command-line tool for managing API keys"""

import os
import json
import argparse

from datastore import DataStore
import api_keys

def _find_datastore():
    """Get the shared datastore in DyanmoDB"""
    datastore_table_name = os.environ.get('DATASTORE_TABLE_NAME', 'url_shortener_table')
    datastore = DataStore(datastore_table_name,
                          ['shortcodes', 'api_keys', 'config'],
                          uncached=['api_keys'])
    return datastore

def create(database, args):
    """Create a new API key"""
    key_info = api_keys.create(database, args.name, args.grant,
                               args.deny if args.deny is not None else [])
    print(key_info)

def info(database, args):
    """Display info about an API key"""
    account_id = args.account_id
    key_info = api_keys.info(database, account_id)
    if key_info is None:
        print("API Key {} not found".format(account_id))
    else:
        print(json.dumps(key_info, indent=2))

def delete(database, args):
    """Delete an API key"""
    account_id = args.account_id
    if api_keys.delete(database, account_id):
        print("API Key for account {} deleted".format(account_id))
    else:
        print("API Key account {} not found".format(account_id))

def main():
    """Parse command line options and call the relevant sub-command"""
    parser = argparse.ArgumentParser(description="Manage API keys")
    subparsers = parser.add_subparsers(title="Subcommands")

    create_parser = subparsers.add_parser('create', description="Create a new API key")
    create_parser.add_argument('--name', '-n', metavar='NAME', required=True, type=str)
    create_parser.add_argument('--grant', '-g', metavar='OPERATION',
                               required=True, action='append', type=str)
    create_parser.add_argument('--deny', '-d', metavar='OPERATION', action='append', type=str)
    create_parser.set_defaults(func=create)

    info_parser = subparsers.add_parser('info')
    info_parser.add_argument('--account-id', '-I', metavar='ID', required=True, type=str)
    info_parser.set_defaults(func=info)

    delete_parser = subparsers.add_parser('delete')
    delete_parser.add_argument('--account-id', '-I', metavar='ID', required=True, type=str)
    delete_parser.set_defaults(func=delete)

    args = parser.parse_args()
    args.func(_find_datastore(), args)

if __name__ == "__main__":
    main()
