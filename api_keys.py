"""This module handles operations on API keys"""

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


import time
import uuid

def create(database, name, grant, deny):
    """Create a new API key"""
    permissions = {}
    for right in grant:
        permissions[right] = True
    for right in deny:
        permissions[right] = False

    account_id = str(uuid.uuid4())[:18]
    secret = str(uuid.uuid4())
    key_info = {
        "account_id": account_id,
        "api_key": secret,
        "permissions": permissions,
        "name": name,
        "timestamp": int(time.time())
        }

    database.api_keys[account_id] = key_info
    return key_info

def info(database, account_id):
    """Fetch info about an API key"""
    return database.api_keys[account_id]

def delete(database, account_id):
    """Delete an API key"""
    key_info = database.api_keys[account_id]
    if key_info is None:
        return False

    del database.api_keys[account_id]
    return True

def check_rights(database, account_id, api_key):
    """Check an API key and, if valid, return the set of rights associated with it"""
    key_info = database.api_keys[account_id]
    if key_info is None or key_info['api_key'] != api_key:
        return None
    return key_info['permissions']
