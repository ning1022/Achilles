#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       RequestUtilities.py
Author:     Himyth
"""

from .Constant import HTTP_POST, HTTP_GET
from .UrlUtilities import get_split_query, UrlItem, replace_query, get_query

import requests

__all__ = ['send_payloads', 'send_request']


def send_request(target, cookie):
    """
    send a common request, retrieve the response
    :param target:  UrlItem
    :param cookie:  cookie
    :return:        page source
    """
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 '
                            '(KHTML, like Gecko) Chrome/50.0.2661.87 Safari/537.36',
              'Cookie': cookie}
    if target.method == HTTP_POST:
        header['Content-Type'] = 'application/x-www-form-urlencoded'
        response = __send_with_retry(requests.post,
                                     url=target.url,
                                     data=target.data,
                                     headers=header)
    else:
        response = __send_with_retry(requests.get,
                                     url=target.url,
                                     headers=header)
    return response


def __send_with_retry(send, **kwargs):
    for _ in xrange(3):
        try:
            r = send(**kwargs)
        except:
            continue
        return r.text
    return ''


def send_payloads(target, cookie, payloads, callback):
    injectable = []
    for payload in payloads:
        for _target, pos in __replace_params(target, payload):
            response = send_request(_target, cookie)
            if callback(response, payload):
                injectable.append((pos, payload))
    return injectable


def __replace_params(target, payload):
    if target.method == HTTP_GET:
        yield target, None
        return

    # deal with get parameters
    # [[name, value], ...]
    querys = get_split_query(get_query(target.url))
    _target = list(target)
    for i in xrange(len(querys)):
        old_value = querys[i][1]    # clone the old one
        querys[i][1] = payload

        _new_query = '&'.join(['='.join(_) for _ in querys])
        _target[0] = replace_query(target.url, _new_query)
        yield UrlItem(*_target), querys[i][0]

        querys[i][1] = old_value    # restore it

    # this time, post data
    if target.method == HTTP_POST:
        querys = get_split_query(target.data)
        _target = list(target)
        for i in xrange(len(querys)):
            old_value = querys[i][1]    # clone the old one
            querys[i][1] = payload

            # replace the data
            _target[2] = '&'.join(['='.join(_) for _ in querys])
            yield UrlItem(*_target), querys[i][0]

            querys[i][1] = old_value    # restore it
    return
