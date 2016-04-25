#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       AutoSqli.py
Author:     Himyth
Statement:  Modified from AutoSqli.py by Manning, gevent supported
"""

from gevent import sleep
import requests
import time
import json

from ...util.Constant import HTTP_POST
from logging import getLogger

__all__ = ['AutoSqli']
logger = getLogger(__name__)

OP_TIMEOUT = 0
OP_SUCCEED = 1
OP_FAILED = 2

STAT_RUNNING = 0
STAT_STOPPED = 1
STAT_NOT_RUNNING = 2


class AutoSqli(object):

    def __init__(self, server, target, options):
        self.server = server
        self.target = target
        self.retries = options['retries']
        self.timeout = options['timeout']
        self.options = options['task']
        self.info = dict()

    def get_result(self):
        count = self.retries
        while count > 0:
            result = self.scan()
            if result == OP_TIMEOUT:
                logger.error('Timeout for "%s"' % self.target.url)
            elif result == OP_SUCCEED:
                return self.info['datas'], self.info['errors']
            else:
                logger.error('Something wrong with "%s"' % self.target.url)
            count -= 1
            sleep(1)
        logger.error('Retried for %d time(s), abort on "%s"' %
                     (self.retries, self.target.url))
        return [], []

    def scan(self):
        # task new will ocassionally fail, guess server not ready yet
        try:
            self.task_new()
        except:
            return OP_FAILED
        self.scan_start()

        start = time.time()
        while time.time() - start < self.timeout:
            status = self.scan_status()

            if status == STAT_RUNNING:
                sleep(2)

            elif status == STAT_STOPPED:
                self.scan_data()
                self.task_delete()
                return OP_SUCCEED

            elif status == STAT_NOT_RUNNING:
                return OP_FAILED

        self.task_delete()
        return OP_TIMEOUT

    # ###### methods communicating with sqlmapapi server

    def task_new(self):
        url = self.server + '/task/new'
        self.info['taskid'] = json.loads(requests.get(url).text)['taskid']

    def task_delete(self):
        url = self.server + '/task/' + self.info['taskid'] + '/delete'
        requests.get(url)

    def scan_start(self):
        headers = {'Content-Type': 'application/json'}
        option = {'url': self.target.url,
                  'smart': True}
        if self.target.method == HTTP_POST:
            option['data'] = self.target.data
        for key in self.options:
            option[key] = self.options[key]

        url = self.server + '/scan/' + self.info['taskid'] + '/start'
        response = json.loads(requests.post(url,
                                            data=json.dumps(option),
                                            headers=headers).text)
        self.info['engineid'] = response['engineid']

    def scan_stop(self):
        url = self.server + '/scan/' + self.info['taskid'] + '/stop'
        requests.get(url)

    def scan_kill(self):
        url = self.server + '/scan/' + self.info['taskid'] + '/kill'
        requests.get(url)

    def scan_status(self):
        statuses = {'not running': STAT_NOT_RUNNING,
                    'terminated': STAT_STOPPED,
                    'running': STAT_RUNNING}

        url = self.server + '/scan/' + self.info['taskid'] + '/status'
        return statuses[json.loads(requests.get(url).text)['status']]

    def scan_data(self):
        url = self.server + '/scan/' + self.info['taskid'] + '/data'
        response = json.loads(requests.get(url).text)
        self.info['datas'] = response['data']
        self.info['errors'] = response['error']
