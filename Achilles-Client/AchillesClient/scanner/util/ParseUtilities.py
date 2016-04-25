#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       ParseUtilities.py
Author:     Himyth
"""

from lxml import etree
import re

from .UrlUtilities import get_url_join, clean_up, get_query, get_pattern, \
    UrlItem, LoginForm
from .Constant import HTTP_GET, HTTP_POST, HTTP_GET_Q, \
    HTTP_STAT_UNKNOWN, HTTP_EMPTY_POST, HTTP_PARSE_FAIL

__all__ = ['parse_page']
mail_js_filter = re.compile('^(?:javascript|mailto):', re.IGNORECASE)


def parse_page(current_url, source_code):
    """
    分析页面，提取出URL
    :current_url:   current url as UrlItem
    :source_code:   page source code
    :return:    statusCode, [UrlItem], [UrlItemLogin]
    """
    page = __get_parsed_xml(source_code)
    if page is HTTP_PARSE_FAIL:
        return HTTP_STAT_UNKNOWN, [], []

    depth = current_url.depth + 1
    status_code = __get_status_code(page.xpath('//stat'))

    # 处理A标签，处理表单，登录表单
    login_forms, urls = __handle_form_tag(page.xpath('//form'), current_url.url, depth)
    urls.extend(__handle_a_tag(page.xpath('//a'), current_url.url, depth))

    urls, login_forms = __eliminate_dup(current_url, urls, login_forms)
    updated_url = UrlItem(current_url.url, current_url.method,
                          current_url.data, status_code, current_url.depth)
    return updated_url, urls, login_forms


def __eliminate_dup(base, urls, logins):
    exists = {get_pattern(base)}
    r_urls = []
    r_logins = []

    for url in urls:
        p = get_pattern(url)
        if p in exists:
            continue
        exists.add(p)
        r_urls.append(url)

    exists.clear()
    for login in logins:
        p = __get_login_pattern(login)
        if p in exists:
            continue
        exists.add(p)
        r_logins.append(login)

    return r_urls, r_logins


def __get_login_pattern(login):
    # 本来需要传入UrlItem。但是get_pattern函数需要的
    # 三个成员UrlItemLogin都有，所以就无需转换了
    # 但是还需要把logindata转换一下。一边是list一边是str
    url = get_pattern(LoginForm(login.url, login.method, ''))
    inline = '&'.join(['/'.join([_[0], _[2]]) for _ in login.data])
    return url + '&&&' + inline


def __handle_form_tag(tags, url, depth):
    login_form = []
    urls = []
    for tag in tags:
        if 'action' not in tag.attrib:
            continue
        final_link = get_url_join(url, clean_up(tag.attrib['action']))

        method, final_link, inline, post_data = __handle_form(tag, final_link)

        if __is_login_form(post_data):
            login_form.append(LoginForm(final_link, method, post_data))

        urls.append(UrlItem(final_link, method, inline, HTTP_STAT_UNKNOWN, depth))
    return login_form, urls


def __handle_a_tag(tags, url, depth):
    urls = []
    for tag in tags:
        if 'href' not in tag.attrib:
            continue
        href = clean_up(tag.attrib['href'])

        if mail_js_filter.match(href):
            continue

        final_link = get_url_join(url, href)
        method = HTTP_GET if get_query(final_link) == '' else HTTP_GET_Q
        urls.append(UrlItem(final_link, method, HTTP_EMPTY_POST,
                            HTTP_STAT_UNKNOWN, depth))
    return urls


def __get_status_code(stat_tags):
    _ = str(stat_tags[0].attrib.get('code'))
    return int(_) if _.isdigit() else HTTP_STAT_UNKNOWN


def __get_parsed_xml(src):
    try:
        # 输入由phantomjs保证一定是utf-8
        page = etree.HTML(src.decode('utf-8'))
    except:
        return HTTP_PARSE_FAIL
    return page


def __is_login_form(inputs):
    """
    :form:      [(name, value, type), ...]
    :return:    True or False
    """
    text_c = passwd_c = 0
    for s_input in inputs:
        if s_input[2] == 'text':
            text_c += 1
        elif s_input[2] == 'password':
            passwd_c += 1

    # username + password
    if passwd_c == 1 and text_c == 1:
        return True
    # password only
    if passwd_c == 1 and text_c == 0:
        return True
    return False


def __analyze_form(tags):
    """
    :return:    [(name, value, type), ...]
    """
    f_input = []
    for _input in tags:
        if 'name' not in _input.attrib:
            continue
        name = _input.attrib['name']

        if 'value' in _input.attrib:
            value = _input.attrib['value']
        else:
            value = ''

        if 'type' in _input.attrib:
            _type = _input.attrib['type']
        else:
            _type = 'text'

        f_input.append((name, value, _type))

    return f_input


def __handle_form(form_tag, url):
    method = form_tag.attrib.get('method')
    if method is None or str(method).upper() == 'GET':
        method = HTTP_GET_Q
    else:
        method = HTTP_POST

    post_data = __analyze_form(form_tag.xpath('.//input'))
    inline = '&'.join(['='.join([_[0], _[1]]) for _ in post_data])
    if method == HTTP_GET_Q:
        if get_query(url) != '':
            url += '&' + inline
        else:
            url += '?' + inline
        inline = HTTP_EMPTY_POST

    return method, url, inline, post_data
