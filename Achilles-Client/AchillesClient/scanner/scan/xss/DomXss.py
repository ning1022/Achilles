#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       DomXss.py
Author:     Himyth
"""

from ...util.RequestUtilities import send_request
from ...util.UrlUtilities import UrlItem, get_url_join
from ...util.Constant import HTTP_GET, HTTP_EMPTY_POST, HTTP_STAT_UNKNOWN

import re
from logging import getLogger

__all__ = ['DomXss']
logger = getLogger(__name__)


class DomXss(object):

    def __init__(self, target, cookie):
        self.target, self.cookie = target, cookie

    def get_result(self):
        _ = _get_script_content(self.target, self.cookie)
        return _analyze_script_content(_)

# ################ This is static methods ################

__js_functions = ['document.write',
                  'document.writeln',
                  'document.execCommand',
                  'document.open',
                  'window.open',
                  'eval',
                  'window.execScript', ]
__user_controlled = ['document.URL',
                     'document.URLUnencoded',
                     'document.location',
                     'document.referrer',
                     'window.location',
                     'location.hash', ]

# Compile the regular expressions
__re_js_func_calls = [re.compile(js_f + ' *\((.*?)\)', re.DOTALL)
                      for js_f in __js_functions]
__re_script = re.compile('< *script[^>]*?>(.*?)</ *script *>',
                         re.IGNORECASE | re.DOTALL)
__re_script_src = re.compile('< *script[^>]*?src="(.*?)">[^<]*?</ *script *>',
                             re.IGNORECASE | re.DOTALL)


def _get_script_content(target, cookie):
    source = send_request(target, cookie)
    script_srcs = __re_script_src.findall(source)

    scripts = dict()
    scripts[target.url] = '\n'.join(__re_script.findall(source))

    for script_src in script_srcs:
        target_url = get_url_join(target.url, script_src)
        script_target = UrlItem(target_url, HTTP_GET, HTTP_EMPTY_POST, HTTP_STAT_UNKNOWN, 0)
        scripts[target_url] = send_request(script_target, cookie)

    return scripts


def _analyze_script_content(scripts):
    injectable = dict()
    for url in scripts:
        params = []
        for re_js_func_call in __re_js_func_calls:
            params.extend(re_js_func_call.findall(scripts[url]))
        param = '\n'.join(params)
        results = []
        for user_controlled in __user_controlled:
            if user_controlled in param:
                results.append(user_controlled)
        result = '|'.join(results)
        if result != '':
            injectable[url] = result
    return injectable
