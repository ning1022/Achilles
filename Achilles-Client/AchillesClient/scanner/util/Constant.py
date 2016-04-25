#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       Constant.py
Author:     Himyth
"""

# http method
HTTP_GET = 0
HTTP_GET_Q = 1
HTTP_POST = 2

# http other
HTTP_STAT_UNKNOWN = 0
HTTP_EMPTY_POST = ''
HTTP_PARSE_FAIL = None

# result type
RESULT_UPDATE_URL = 0
RESULT_NEW_URL = 1
RESULT_LOGIN_FORM = 2
RESULT_SQL_INJECTION = 3
RESULT_DOM_XSS = 4
RESULT_REFLECT_XSS = 5

# task status
TASK_NOTHING_YET = 0
TASK_NO_MORE = None
TASK_MAX_SIZE = 0

# task type
TASK_URL = 0
TASK_LOGIN_FORM = 1
TASK_DOMAIN = 2
