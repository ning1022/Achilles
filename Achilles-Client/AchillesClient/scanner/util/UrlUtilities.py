#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       UrlUtilities.py
Author:     Himyth
"""

from urlparse import urlparse, ParseResult, urljoin
from collections import namedtuple

import re
import os

from .Constant import HTTP_POST

__all__ = ['UrlItem', 'LoginForm', 'get_path', 'get_netloc',
           'get_query',  'get_url_join', 'get_ext', 'get_pattern',
           'clean_up', 'multi_replace', 'get_domain',
           'get_split_query', 'replace_query']


class UrlItem(namedtuple('UrlItem', 'url method data status depth')):
    def __init__(self, *args):
        super(UrlItem, self).__init__(*args)


class LoginForm(namedtuple('LoginForm', 'url method data')):
    def __init__(self, *args):
        super(LoginForm, self).__init__(*args)


def get_path(url):
    path = urlparse(url).path
    return '/' if path == '' else path


def get_netloc(url):
    return urlparse(url).netloc


def get_query(url):
    return urlparse(url).query


def get_url_join(base, url):
    return urljoin(base, url)


def get_ext(url):
    path = get_path(url)
    return os.path.splitext(path)[1]


def get_domain(url):
    url = urlparse(url)
    return url.scheme + '://' + url.netloc + '/'


# [[name, value], ...] not used for now
def get_split_query(query):
    spl = []
    for query in query.split('&'):
        _ = query.split('=', 1)
        _.append('') if len(_) == 1 else 0
        spl.append(_)
    return spl


def replace_query(url, query):
    urlp = list(urlparse(url))
    urlp[4] = query         # update query
    return ParseResult(*urlp).geturl()


def get_pattern(url_item, level=3):
    """
    method还可能是HTTP_GET_Q，但是处理相同所以就不额外声明了
    GET与POST永远不会相同，因为开头有P/G区分
    同一种请求不存在只有在POST字段跟GET字段都相同的情况下，才可能相同
    在上面的基础上，通过level调整pattern的相似度
    """
    url = url_item.url
    path = get_path(url)

    # level - 模式化的层数， sepc - 可模式化的最大层数
    sepc = path.count('/')
    level = min(sepc, level)

    # 模式化
    paths = path.split('/', sepc - level + 1)
    paths[-1] = re.sub(r'\d+', '^_^', paths[-1])

    # 整理查询字符串，组装
    parse_result = urlparse(url)
    path = '/'.join(paths)
    query = __sort_query(parse_result.query)      # GET请求字串
    if url_item.method == HTTP_POST:
        query += '&&' + __sort_query(url_item.data)   # POST字串附在后面
        scheme = 'P' + parse_result.scheme      # 表示GET或者POST
    else:
        scheme = 'G' + parse_result.scheme

    parse_result = list(parse_result)
    parse_result[0] = scheme
    parse_result[2] = path
    parse_result[4] = query
    parse_result[5] = ''
    return ParseResult(*parse_result).geturl()


# name1&name2&...
def __sort_query(query):
    querys = [_.split('=', 1)[0].lower() for _ in query.split('&')]
    querys.sort()
    return '&'.join(querys)


def clean_up(url):
    return re.sub(r'[\x00-\x1f\xff]', '', url).strip(' ')


def multi_replace(string, repls):
    for repl in repls:
        string = string.replace(repl[0], repl[1])
    return string
