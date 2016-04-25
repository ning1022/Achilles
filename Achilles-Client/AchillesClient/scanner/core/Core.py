#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       Core.py
Author:     Himyth
"""

from logging import getLogger
from threading import Thread
from Queue import Queue

from ..crawl.Crawler import CrawlerManager
from ..scan.Scanner import ScannerManager

from ..util.BaseAdministrator import BaseAdministrator
from ..util.Constant import TASK_MAX_SIZE, TASK_NO_MORE, \
    TASK_URL, TASK_DOMAIN, TASK_LOGIN_FORM
from ..util.UrlUtilities import UrlItem, LoginForm

import zerorpc
import time

__all__ = ['Core']
logger = getLogger(__name__)


class Core(BaseAdministrator):

    def __init__(self, config):
        """
        Server calls Client.start to start this scanner through
        ZeroRPC, so leave all configuration stuffs to thread
        running stage, try not to block the Server.
        """
        super(Core, self).__init__(tasks=Queue(maxsize=TASK_MAX_SIZE),
                                   results=Queue())
        self.server_ip = config['server_ip']
        self.cid = config['cid']

    def run(self):
        # init the scanner
        rmgr = self.init_scanner()
        if rmgr is None:
            return

        # run as a normal administrator
        super(Core, self).run()

        # shut down the result manager
        self.results.put(TASK_NO_MORE)
        rmgr.join()
        logger.debug('Exit')

    def init_scanner(self):
        server = self.connect('Core')
        if server is None:
            return None
        try:
            config = server.get_config(self.cid)
        except:
            return None

        logger.debug('Scanner configuration retrived, id from server [%s], started' % self.cid)

        # add managers
        self.managers = [CrawlerManager(tasks=Queue(maxsize=TASK_MAX_SIZE),
                                        results=Queue(),
                                        args=config['crawler']),
                         ScannerManager(tasks=Queue(maxsize=TASK_MAX_SIZE),
                                        results=Queue(),
                                        args=config['scanner']),
                         # add more managers here
                         ]

        # start task and result manager
        Thread(target=self.task_manager).start()
        rmgr = Thread(target=self.result_manager)
        rmgr.start()
        return rmgr

    # override
    def handle_result(self):
        for manager in self.managers:
            for res in manager.get():
                self.results.put(res)
        pass

    def connect(self, msg):
        server = zerorpc.Client()
        try:    # in case server is down
            server.connect("tcp://" + self.server_ip)
        except:
            return None
        logger.debug(' '.join([msg, "connected to server at:", self.server_ip]))
        return server

    def result_manager(self):
        server = self.connect('ResultManager')
        if server is None:
            return
        while True:
            result = self.results.get()
            if result is TASK_NO_MORE:
                break

            # in case server is down
            try:
                server.put_result(self.cid, *result)
            except:
                break

        # tell server i am gone
        try:
            server.leave(self.cid)
        except:
            logger.error('Server not response, exit client now')

    """
    ZeroRPC Object cannot be used cross-threads, had to
    create another one for task/result manager
    """
    def task_manager(self):
        server = self.connect('TaskManager')
        if server is None:
            return

        max_tasks = 10
        reconstructs = {TASK_URL: lambda x: UrlItem(*tuple(x)),
                        TASK_DOMAIN: lambda x: x,
                        TASK_LOGIN_FORM: lambda x: LoginForm(*tuple(x))}

        leaving = False
        while not leaving:
            leaving = True
            for _type in reconstructs:
                if self.get_tasks(server, max_tasks, _type, reconstructs[_type]):
                    leaving = False
                    continue
                reconstructs[_type] = None

            time.sleep(2)

        # bye bye
        self.tasks.put(TASK_NO_MORE)

    def get_tasks(self, server, max_tasks, _type, reconstruct):
        if reconstruct is None:
            return False

        # in case server is down
        try:
            tasks = server.get_task(self.cid, _type, max_tasks)
        except:
            return False

        if tasks is TASK_NO_MORE:
            return False

        for task in tasks:
            self.tasks.put((_type, reconstruct(task)))

        return True
