#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       AchillesClient.py
Author:     Himyth
"""

from logging import getLogger
from threading import Thread

import logging
import zerorpc

from .scanner.core.Core import Core

logger = getLogger(__name__)


class AchillesClient(Thread):

    def __init__(self, listen_ip):
        super(AchillesClient, self).__init__()
        init_logger()
        show_info()
        self.core = None
        self.listen_ip = listen_ip

    def run(self):
        logger.debug('Waiting for server at %s' % self.listen_ip)
        listen = zerorpc.Server(self)
        listen.bind('tcp://' + self.listen_ip)
        listen.run()

    def start_client(self, config):
        if self.core is None or not self.core.is_alive():
            logger.debug('Server coming in, starting scanner now')
            self.core = Core(config)
            self.core.start()
            return True
        else:
            logger.debug('Only one instance allow at the same time')
            return False


def init_logger():
    fmt = '[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s.'
    datefmt = '%H:%M:%S'
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)

    _logger = logging.getLogger(__name__.split('.')[0])
    _logger.setLevel(logging.DEBUG)
    _logger.addHandler(console)
    _logger.propagate = False


def show_info():
    logger.info('If running on Linux, make sure you have FontConfig '
                'installed to run with phantomJS')
    logger.info('Sqlmapapi had been modified at line 158@/lib/utils/api.py '
                'to avoid possible related path error')
