#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       SqlScanner.py
Author:     Himyth
"""

from .AutoSqli import AutoSqli
from ...util.BaseGeventThread import BaseGeventThread
from ...util.Constant import TASK_NO_MORE
from ...util.BaseScannerManager import BaseScannerManager


from logging import getLogger
import time
import subprocess

__all__ = ['SqlScannerManager']
logger = getLogger(__name__)


class SqlScanner(BaseGeventThread):

    def __init__(self, tasks, results, cookie, coroutine_num=0):
        """
        :param tasks, results:  Queue for in and out
        :param cookie:          cookies
        :param coroutine_num:   number of coroutines, default to 0
        """
        super(SqlScanner, self).__init__(tasks, results, coroutine_num, 8, logger)

        sqlmapapi_addr = '127.0.0.1:8522'
        addr = 'http://' + sqlmapapi_addr
        self.sqlmapapi = start_sqlmapapi_server(sqlmapapi_addr)

        self.worker_args = (cookie, addr)

    def run(self):
        time.sleep(3)   # wait for sqlmapapi server

        super(SqlScanner, self).run()

        # kill sqlmapapi server if necessary
        if self.sqlmapapi:
            try:
                self.sqlmapapi.kill()
            finally:
                logger.debug('Sqlmapapi server stopped')

    def worker(self, *args):
        # options for sqlmap
        cookie, addr = args
        opts = {'retries': 3,
                'timeout': 180,  # timeout for 3 minutes
                'task': {'cookie': cookie,
                         'referer': ''}}
        while True:
            target = self.tasks.get()

            # put a TASK_NO_MORE to shut this down
            if target is TASK_NO_MORE:
                break
            logger.debug('Scanning URL "%s"' % target.url)

            datas, errors = AutoSqli(addr, target, opts).get_result()
            for error in errors:
                logger.error('[%s] on "%s"' % (str(error), target.url))
            if datas:
                # pass the result up if it is injectable
                _result = formatting(datas)
                self.results.put((target, _result))
                logger.info('Injectable at "%s"' % target.url)
            else:
                logger.debug('UnInjectable at "%s"' % target.url)
        return

# ################ This is for Manager ################


class SqlScannerManager(BaseScannerManager):

    def __init__(self, tasks, results, args):
        sql_scanner = SqlScanner(tasks=tasks,
                                 results=results,
                                 cookie=args['cookie'])
        super(SqlScannerManager, self).__init__(tasks, results, sql_scanner)
        logger.debug('Started')

    def kill(self):
        super(SqlScannerManager, self).kill()
        logger.debug('Exit')

# ################ This is static methods ################


def start_sqlmapapi_server(addr):
    path = './AchillesClient/thirdparty/sqlmap/sqlmapapi.py'
    addr, port = addr.split(':')
    sqlmapapi = subprocess.Popen(
        ['python', path, '-s', '-H', addr, '-p', port],
        shell=False,
        stdout=open('./AchillesClient/extra/log/sqlmapapi.out', 'w'),
        stderr=open('./AchillesClient/extra/log/sqlmapapi.err', 'w')
        )
    logger.debug('Sqlmapapi server started at %s:%s' % (addr, port))
    return sqlmapapi


def formatting(results):
    result = results[0]['value'][0]

    dbms = result['dbms']
    dbms = '' if dbms is None else dbms

    data = result['data']
    if data is None:
        return dbms, ''

    payload = []
    for x in data:
        if 'payload' in data[x]:
            payload.append(data[x]['payload'])
    payload = '\n'.join(payload)

    return '\t[DBMS] ' + dbms + '\n\t[PAYLOAD] ' + payload
