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


"""A command-line tool for managing API keys for the surly URL shortener"""

import os
import json

import click

from datastore import DataStore
import api_keys

def get_datastore():
    """Get the shared datastore in DyanmoDB"""
    datastore_table_name = os.environ.get('DATASTORE_TABLE_NAME', 'url_shortener_table')
    datastore = DataStore(datastore_table_name,
                          ['shortcodes', 'api_keys', 'config'],
                          uncached=['api_keys'])
    return datastore

@click.group()
@click.pass_context
def cli(ctx):
    """Manage API keys for the surly URL shortener"""
    ctx.ensure_object(dict)
    ctx.obj['DATABASE'] = get_datastore()

@cli.command()
@click.option('--name', '-n', required=True, type=str)
@click.option('--grant', '-g', required=True, type=str, multiple=True)
@click.option('--deny', '-d', type=str, multiple=True)
@click.pass_context
def create(ctx, name, grant, deny):
    """Create a new API key"""
    database = ctx.obj['DATABASE']

    key_info = api_keys.create(database, name, grant, deny)

    print(key_info)

@cli.command()
@click.option('--account-id', '-I', required=True, type=str)
@click.pass_context
def info(ctx, account_id):
    """Display info about an API key"""
    database = ctx.obj['DATABASE']
    key_info = api_keys.info(database, account_id)
    if key_info is None:
        print("API Key {} not found".format(account_id))
    else:
        print(json.dumps(key_info, indent=2))

@cli.command()
@click.option('--account-id', '-I', required=True, type=str)
@click.pass_context
def delete(ctx, account_id):
    """Delete an API key"""
    database = ctx.obj['DATABASE']
    if api_keys.delete(database, account_id):
        print("API Key for account {} deleted".format(account_id))
    else:
        print("API Key account {} not found".format(account_id))

if __name__ == "__main__":
    cli() # pylint: disable=no-value-for-parameter
