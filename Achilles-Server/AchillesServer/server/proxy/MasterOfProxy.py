#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       MasterOfProxy.py
Author:     Himyth
"""

from ..util.UrlUtilities import multi_replace, get_ext, UrlItem
from ..util.Constant import HTTP_POST, HTTP_GET_Q, HTTP_GET, HTTP_EMPTY_POST, \
    HTTP_STAT_UNKNOWN, RESULT_NEW_URL

from mitmproxy.controller import Master
from logging import getLogger
import re

logger = getLogger(__name__)


class MasterOfProxy(Master):

    def __init__(self, proxy_server, proxy_results, args):
        super(MasterOfProxy, self).__init__(proxy_server)

        self.proxy_results = proxy_results
        self.allow_domain = re.compile(
            multi_replace(args['allow_domain'], [('.', '\\.'), ('*', '.*?')]),
            re.IGNORECASE)
        self.filetype = re.compile(args['filetype'], re.IGNORECASE)

    def run(self):
        super(MasterOfProxy, self).run()

    def handle_request(self, flow):
        req = flow.request
        while self.filter(req):
            if req.method == 'GET':
                data = HTTP_EMPTY_POST
                if req.query is None:
                    method = HTTP_GET
                else:
                    method = HTTP_GET_Q
            elif req.method == 'POST':
                method = HTTP_POST
                data = req.content
            else:
                break
            self.proxy_results.put(UrlItem(req.url,
                                           method,
                                           data,
                                           HTTP_STAT_UNKNOWN,
                                           0))
            break
        flow.reply()

    def handle_response(self, flow):
        flow.reply()

    def filter(self, request):
        ext = get_ext(request.url)
        if not (self.filetype.match(ext[1:]) or ext == ''):
            return False
        return not not self.allow_domain.match(request.host)

    def get(self):
        _ = []
        while not self.proxy_results.empty():
            _.append(self.proxy_results.get())
        return RESULT_NEW_URL, _
