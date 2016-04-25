#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       XssScanner.py
Author:     Himyth
"""

from ...util.BaseGeventThread import BaseGeventThread
from ...util.Constant import TASK_NO_MORE, HTTP_GET, TASK_URL, \
    RESULT_DOM_XSS, RESULT_REFLECT_XSS
from ...util.BaseScannerManager import BaseScannerManager
from ...util.UrlUtilities import get_path

from .DomXss import DomXss
from .ReflectXss import ReflectXss

from logging import getLogger

__all__ = ['XssScannerManager']
logger = getLogger(__name__)


class XssScanner(BaseGeventThread):

    def __init__(self, tasks, results, cookie, coroutine_num=0):
        """
        :param tasks, results:  Queue for in and out
        :param cookie:          cookies
        :param coroutine_num:   number of coroutines, default to 0
        """
        super(XssScanner, self).__init__(tasks, results, coroutine_num, 8, logger)

        self.worker_args = (cookie,)

    def worker(self, *args):
        cookie, = args
        while True:
            target = self.tasks.get()

            # put a TASK_NO_MORE to shut this down
            if target is TASK_NO_MORE:
                break
            logger.debug('Scanning URL "%s"' % target.url)

            # dom test accept all kinds of requests
            dom_result = DomXss(target, cookie).get_result()
            if dom_result:
                _result = formatting_dom(dom_result)
                self.results.put((RESULT_DOM_XSS, (target, _result)))
                logger.info('Possible DOM-based XSS found at "%s"' % target.url)
            else:
                logger.debug('No DOM-based XSS found at "%s"' % target.url)

            if target.method == HTTP_GET:
                continue

            reflect_result = ReflectXss(target, cookie).get_result()
            if reflect_result:
                _result = formatting_reflect(reflect_result)
                self.results.put((RESULT_REFLECT_XSS, (target, _result)))
                logger.info('Possible Reflected XSS found at "%s"' % target.url)
            else:
                logger.debug('No Reflected XSS found at "%s"' % target.url)

        return

# ################ This is for Manager ################


class XssScannerManager(BaseScannerManager):

    def __init__(self, tasks, results, args):
        sql_scanner = XssScanner(tasks=tasks,
                                 results=results,
                                 cookie=args['cookie'])
        super(XssScannerManager, self).__init__(tasks, results, sql_scanner)
        logger.debug('Started')

    # accept HTTP_GET requests too,
    # since dom-xss may hit without parameters
    def put(self, task):
        if task[0] != TASK_URL:
            return
        task = task[1]

        # careful with logout url, save the cookies
        if self.logout.match(get_path(task.url)):
            return

        self.tasks.put(task)

    def kill(self):
        super(XssScannerManager, self).kill()
        logger.debug('Exit')

# ################ This is static methods ################


def formatting_dom(results):
    payloads = ['\t[SOURCE] ' + key + '\n\t[KEYWORD] ' + results[key]
                for key in results]
    return '\n'.join(payloads)


def formatting_reflect(results):
    payloads = ['\t[PARAMETER] ' + _[0] + '\n\t[PAYLOAD] ' + _[1]
                for _ in results]
    return '\n'.join(payloads)
