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



"""A URL shortener service"""

import os
import logging
import time
import json

from decimal import Decimal
from functools import wraps

from flask import abort, Flask, request, redirect, jsonify
from werkzeug.routing import Rule

from datastore import DataStore
import api_keys

# Default length of shortcode
CODE_LENGTH = 20
# Number of attempts to find a unique code
NEW_CODE_TRIES = 5
# The number of bits in a base36 character
LOG_36_2 = 5.17

DATASTORE_TABLE_NAME = os.environ.get('DATASTORE_TABLE_NAME', 'url_shortener_table')

# Set up some basic logging
logging.basicConfig(level=logging.WARNING)
# Set up a logger of our own
LOGGER = logging.getLogger(__name__+"CORE")
try:
    LOGGER.setLevel(os.environ.get("LOG_LEVEL", "INFO").strip().upper())
except ValueError:
    LOGGER.setLevel(logging.INFO)

DATASTORE = DataStore(DATASTORE_TABLE_NAME,
                      ['shortcodes', 'api_keys', 'config'],
                      uncached=['api_keys'])

class DynamoEncoder(json.JSONEncoder):
    """A special JSON encoder that works with the decimals from DynamoDB"""
    def default(self, o): # pylint: disable=method-hidden
        if isinstance(o, Decimal):
            return int(o)
        return super().default(o)

CODE_CHAR_SET = 'abcdefghijklmnopqrstuvwxyz0123456789'
def generate_random_code(length):
    """Generate a random code with length base-36 characters"""
    # We make code_value a few bits longer than 36^length
    byte_length = -int(-length * LOG_36_2 // 8) + 1
    code_value = int.from_bytes(os.urandom(byte_length), 'little')
    code = ''
    for i in range(length):
        code += CODE_CHAR_SET[code_value % 36]
        code_value //= 36
    return '-'.join(code[i:i+5] for i in range(0, length, 5))

def _get_api_key():
    if hasattr(request, 'form') and 'api_key' in request.form and 'account_id' in request.form:
        return (request.form['account_id'], request.form['api_key'])
    if hasattr(request, 'args') and 'api_key' in request.args and 'account_id' in request.args:
        return (request.args['account_id'], request.args['api_key'])
    return (None, None)

# This is a decorator factory; a function that returns a decorator
# (which in turn is a function that returns a function).
def authorised(operations):
    """A decorator factory which ensures an API access is authorised"""
    def _bound_auth_decorator(endpoint_func):
        @wraps(endpoint_func)
        def _authorised_endpoint(*args, **kwargs):
            account_id, api_key = _get_api_key()
            if ((account_id is None) or
                    (not api_keys.check_permissions(DATASTORE, account_id, api_key, operations))):
                abort(401)
            return endpoint_func(*args, **kwargs)
        return _authorised_endpoint
    return _bound_auth_decorator

# Flask likes lower case but pylint does not
# pylint: disable=invalid-name
app = Flask(__name__)
app.json_encoder = DynamoEncoder


@app.route("/")
def hello():
    """Dummy root page for testing responses"""
    return "OK"

# We handle the routing of this one differently, since we want to support ALL methods
app.url_map.add(Rule("/<shortcode>", endpoint='expander'))
@app.endpoint('expander')
def expander(shortcode):
    """Perform a URL redirection"""
    code_info = DATASTORE.shortcodes[shortcode]
    if code_info is None:
        abort(404)
    return redirect(code_info['target'])

@app.route("/api/v1/shortcode", methods=['POST'])
@authorised("shortcode.create")
def create():
    """Register a new target URL and get back the short code"""
    # Generate a unique new code (looping until it's unique)

    form = request.form

    length = int(form['length']) if 'length' in form else CODE_LENGTH
    prefix = form['prefix'] if 'prefix' in form else None
    target = form['target']

    for _ in range(NEW_CODE_TRIES):
        shortcode = generate_random_code(length)
        if prefix is not None:
            shortcode = prefix + "-" + shortcode
        if DATASTORE.shortcodes[shortcode] is None:
            break
    else:
        # Each random value hit an existing value, likely because of too little entropy
        return jsonify({"error": "Failed to find a unique code. Increasing the length"}), 409

    # Create a record with the creater, time-stamp, target and code, keyed on the code
    info = {
        'target': target,
        'shortcode': shortcode,
        'creator': request.form['account_id'],
        'timestamp': int(time.time())
        }

    DATASTORE.shortcodes[shortcode] = info

    return info

@app.route("/api/v1/shortcode/<shortcode>", methods=['DELETE'])
@authorised("shortcode.delete")
def shortcode_delete(shortcode):
    """Delete an existing shortcode"""
    code_info = DATASTORE.shortcodes[shortcode]
    if code_info is None:
        abort(404)

    del  DATASTORE.shortcodes[shortcode]

    return "OK"

@app.route("/api/v1/shortcode/<shortcode>", methods=['GET'])
@authorised("shortcode.info")
def shortcode_info(shortcode):
    """Delete an existing shortcode"""
    # Create a record with the creater, time-stamp, target and code, keyed on the code

    code_info = DATASTORE.shortcodes[shortcode]

    if code_info is None:
        abort(404)

    return code_info
