#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       Crawler.py
Author:     Himyth
"""

from .DownloadParser import DownloadParserManager
from .Robots import RobotsManager

from ..util.BaseManager import BaseManager
from ..util.BaseAdministrator import BaseAdministrator
from ..util.Constant import RESULT_LOGIN_FORM, RESULT_NEW_URL, \
    RESULT_UPDATE_URL, TASK_MAX_SIZE, TASK_NO_MORE
from ..util.UrlUtilities import multi_replace, get_ext, get_netloc

from logging import getLogger
from Queue import Queue
import re

__all__ = ['CrawlerManager']
logger = getLogger(__name__)

DOWNLOAD_PARSER = 0
ROBOTS = 1


class Crawler(BaseAdministrator):

    def __init__(self, tasks, results, args):

        super(Crawler, self).__init__(tasks, results)

        _args = args['crawler']
        self.filetype = re.compile(_args['filetype'], re.IGNORECASE)
        self.allow_domain = re.compile(
            multi_replace(_args['allow_domain'], [('.', '\\.'), ('*', '.*?')]),
            re.IGNORECASE)

        self.managers = [DownloadParserManager(tasks=Queue(maxsize=TASK_MAX_SIZE),
                                               results=Queue(),
                                               args=args['download_parser']),
                         RobotsManager(tasks=Queue(),
                                       results=Queue())
                         # add more managers here
                         ]

    def handle_result(self):
        update_url = []
        new_url = []
        login_form = []

        # handle results of download_parser
        # [(base_url, new_urls, login_forms), ...]
        for res in self.managers[DOWNLOAD_PARSER].get():
            update_url.append(res[0])
            new_url.extend(self.filter(res[1]))
            login_form.extend(self.filter(res[2]))

        # handle results of robots
        # [[urls, ..], ...]
        for res in self.managers[ROBOTS].get():
            new_url.extend(self.filter(res))

        # add more module result handlers here

        # send to core
        self.hand_in(RESULT_UPDATE_URL, update_url)
        self.hand_in(RESULT_NEW_URL, new_url)
        self.hand_in(RESULT_LOGIN_FORM, login_form)

    def filter(self, objs):
        return self.__filetype_filter(self.__domain_filter(objs))

    def __filetype_filter(self, objs):
        result = []
        for obj in objs:
            ext = get_ext(obj.url)
            if self.filetype.match(ext[1:]) or ext == '':
                result.append(obj)
        return result

    def __domain_filter(self, objs):
        return [u for u in objs
                if self.allow_domain.match(get_netloc(u.url))]


# ################ This is for Manager ################


class CrawlerManager(BaseManager):

    def __init__(self, tasks, results, args):
        crawler = Crawler(tasks=tasks,
                          results=results,
                          args=args)
        super(CrawlerManager, self).__init__(tasks, results, crawler)
        logger.debug('Started')

    def put(self, task):
        """
        :param task:    different tasks will be passed down as
                        (type, body), filter here
        """
        # maybe some filter for future usage
        self.tasks.put(task)

    def kill(self):
        # kill the crawler
        self.tasks.put(TASK_NO_MORE)

        logger.debug('Exit')
