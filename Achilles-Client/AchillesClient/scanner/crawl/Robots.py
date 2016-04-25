#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       Robots.py
Author:     Himyth
"""

from ..util.BaseManager import BaseManager
from ..util.Constant import TASK_DOMAIN, TASK_NO_MORE, HTTP_GET, \
    HTTP_EMPTY_POST, HTTP_STAT_UNKNOWN
from ..util.UrlUtilities import get_url_join, UrlItem

import requests
import re

from threading import Thread
from logging import getLogger

__all__ = ['RobotsManager']
logger = getLogger(__name__)


class Robots(Thread):

    def __init__(self, tasks, results):
        super(Robots, self).__init__()

        self.domains = tasks
        self.results = results

    def run(self):
        while True:
            domain = self.domains.get()
            if domain == TASK_NO_MORE:
                break
            logger.debug('Fetching Robots.txt for domain "%s"' % domain)
            self.results.put(parse_robots_txt(domain))

# ################ This is for Manager ################


class RobotsManager(BaseManager):

    def __init__(self, tasks, results):
        robots = Robots(tasks=tasks,
                        results=results)

        super(RobotsManager, self).__init__(tasks, results, robots)
        logger.debug('Started')

    def put(self, task):
        if task[0] != TASK_DOMAIN:
            return

        self.tasks.put(task[1])

    def kill(self):
        self.tasks.put(TASK_NO_MORE)
        logger.debug('Exit')

# ################ This is static methods ################


def parse_robots_txt(domain):
    robots_loc = domain + '/robots.txt'
    content = requests.get(robots_loc).text
    paths = re.findall(r'(?:Disallow|Allow|Sitemap):[ ]*([^ \r\n]*)',
                       content)

    return [UrlItem(get_url_join(robots_loc, path), HTTP_GET,
                    HTTP_EMPTY_POST, HTTP_STAT_UNKNOWN, 0)
            for path in paths if not ('*' in path or '?' in path)]
