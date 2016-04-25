#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       ClickProxy.py
Author:     Himyth
"""

from .MasterOfProxy import MasterOfProxy
from ..util.Constant import TASK_NO_MORE

from mitmproxy.proxy.server import ProxyServer
from mitmproxy.proxy import ProxyConfig
from logging import getLogger
from threading import Thread
from Queue import Queue
from time import sleep

logger = getLogger(__name__)


class ClickProxy(Thread):

    def __init__(self, server, tasks, results, args):
        super(ClickProxy, self).__init__()
        self.tasks = tasks
        self.results = results
        self.server = server

        proxy_server = ProxyServer(ProxyConfig(port=int(args['port'])))
        self.cproxy = MasterOfProxy(proxy_server, Queue(), args)

    def run(self):
        logger.debug('Started')
        thread = Thread(target=self.cproxy.run)
        thread.setDaemon(True)
        thread.start()
        thread = Thread(target=self.upload)
        thread.setDaemon(True)
        thread.start()
        while self.tasks.get() != TASK_NO_MORE:
            continue
        logger.debug('Exit')

    def upload(self):
        while True:
            results = self.cproxy.get()
            if not results[1]:
                sleep(1)
                continue
            self.server.put_result('PROXY', *results)
