#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       AchillesServer.py
Author:     Himyth
"""

from ConfigParser import ConfigParser
from logging import getLogger
from Queue import Queue
from threading import Thread, Lock

import os
import zerorpc
import logging
import gevent
import time

from .server.util.UrlUtilities import get_pattern, UrlItem, LoginForm, \
    get_domain, get_query
from .server.util.Constant import *
from .server.proxy.ClickProxy import ClickProxy

logger = getLogger(__name__)
config_file = os.path.dirname(__file__) + '/Config.ini'


class AchillesServer(Thread):

    def __init__(self):
        super(AchillesServer, self).__init__()

        self.types = ['url', 'domain', 'login']
        self.server_addr, self.clients_addr, init_url, self.config = read_config()
        self.sets, self.queues = self.init_server(init_url)

        init_logger()
        show_info()

        actions = ['get_config', 'get_task', 'put_result', 'leave']
        self.locks = {_: Lock() for _ in actions}

        self.click_proxy = (self.init_click_proxy(self.config['click_proxy'])
                            if self.config['click_proxy']['on'] else None)
        self.clients = dict()
        self.running = True

    def run(self):
        logger.debug('Started')

        # start the clients
        for addr in self.clients_addr:
            cid = gen_random_cid(self.clients, zerorpc.Client())
            config = {'server_ip': self.server_addr,
                      'cid': cid}

            try:
                self.clients[cid].connect("tcp://" + addr)
                stat = self.clients[cid].start_client(config)
            except:
                logger.error('Client [%s] not response, skip this one' % addr)
                del self.clients[cid]
                continue

            if stat:
                logger.info('Client [%s] with ID [%s] started' % (addr, cid))
            else:
                logger.error('Client [%s] is running already, not started '
                             'for this job' % addr)
                del self.clients[cid]

        if not self.clients:
            logger.error('No Clients alive, empty server started, you can stop it now')

        _daemon = Thread(target=self.daemon_running)
        _daemon.start()

        # start the server
        listen = zerorpc.Server(self)
        listen.bind("tcp://" + self.server_addr)
        sp = [gevent.spawn(listen.run),
              gevent.spawn(self.kill_server, listen, _daemon)]
        gevent.joinall(sp)
        logger.debug('Exit')

    def kill_server(self, listen, daemon):
        while True:
            if daemon.is_alive():
                gevent.sleep(1)
                continue
            break
        listen.close()

    def daemon_running(self):
        while self.running:
            time.sleep(1)

    def exit(self):
        # kill self-module
        if self.click_proxy is not None:
            self.click_proxy.tasks.put(TASK_NO_MORE)

        # send the TASK_NO_MORE to clients
        for _ in xrange(len(self.clients)):
            self.queues['url'].put(TASK_NO_MORE)
            self.queues['domain'].put(TASK_NO_MORE)

        # wait for clients go die
        while self.clients:
            time.sleep(1)

        # shut myself down
        self.running = False

    def init_server(self, init_url):
        sets = {_: set() for _ in self.types}
        queues = {_: Queue() for _ in self.types}

        if get_query(init_url) == '':
            method = HTTP_GET
        else:
            method = HTTP_GET_Q
        target = UrlItem(init_url, method, HTTP_EMPTY_POST,
                         HTTP_STAT_UNKNOWN, 0)
        queues['url'].put(target)
        sets['url'].add(get_pattern(target))

        domain = get_domain(init_url)
        queues['domain'].put(domain)
        sets['domain'].add(domain)

        return sets, queues

    def init_click_proxy(self, config):
        if not config['on']:
            return None

        cp = ClickProxy(server=self,
                        tasks=Queue(),
                        results=Queue(),
                        args=config)
        cp.start()
        return cp

    def leave(self, cid):
        self.locks['leave'].acquire()
        if cid in self.clients:
            del self.clients[cid]
        self.locks['leave'].release()

    def get_task(self, cid, type, max):
        self.locks['get_task'].acquire()

        """
        当Server不小心挂掉之后重启，Client即便已经因为超时关闭了，
        也会重新连上来，应该是zerorpc的保障机制，为了保证不被上次
        的连接取走task，这里要验证，如果不是，则返回TASK_NO_MORE
        全杀掉。
        有可能上次的client的id也在这次的列表中，但是这个概率极低。
        put_result处理类似。
        """
        if cid not in self.clients:
            task = TASK_NO_MORE
        elif type == TASK_URL:
            task = self.get_from(self.queues['url'], max)
        elif type == TASK_DOMAIN:
            task = self.get_from(self.queues['domain'], max)
        else:
            task = TASK_NO_MORE

        self.locks['get_task'].release()
        return task

    def get_from(self, q, max):
        _ = []
        while not q.empty() and len(_) < max:
            t = q.get()
            if t == TASK_NO_MORE:
                return TASK_NO_MORE
            _.append(t)
        return _

    def put_result(self, cid, type, results):
        self.locks['put_result'].acquire()
        if cid not in self.clients:
            self.locks['put_result'].release()
            return

        if type == RESULT_UPDATE_URL:
            for _result in results:
                result = UrlItem(*tuple(_result))
                logger.debug('Updated: %d - %s', result.status, result.url)
        elif type == RESULT_NEW_URL:
            for _result in results:
                result = UrlItem(*tuple(_result))

                t = get_pattern(result)
                if t in self.sets['url']:
                    continue
                self.sets['url'].add(t)

                self.queues['url'].put(result)

                t = get_domain(result.url)
                if t not in self.sets['domain']:
                    self.sets['domain'].add(t)
                    self.queues['domain'].put(t)

                logger.debug('Found: %d - %s', result.depth, result.url)
        elif type == RESULT_LOGIN_FORM:
            for _result in results:
                result = LoginForm(*tuple(_result))
                logger.info('LoginForm: %s - %s', result.url, result.data)
        elif type == RESULT_SQL_INJECTION:
            log_scan_result(results, 'SQL found on %s\n%s')
        elif type == RESULT_DOM_XSS:
            log_scan_result(results, 'DOM-Xss found on %s\n%s')
        elif type == RESULT_REFLECT_XSS:
            log_scan_result(results, 'Reflect-XSS found on %s\n%s')

        self.locks['put_result'].release()

    def get_config(self, cid):
        return self.config


def log_scan_result(results, msg):
    for _result in results:
        result = UrlItem(*tuple(_result[0]))
        logger.info(msg % (result.url, _result[1]))


def read_config():
    # read from config files
    config = ConfigParser()
    config.read(config_file)

    server_addr = config.get('Communicate', 'server_addr')
    clients_addr = config.get('Communicate', 'clients_addr').split('|')

    init_url = config.get('Scanner', 'init_url')
    cookie = config.get('Scanner', 'cookie')
    filetype = config.get('Scanner', 'filetype')
    allow_domain = config.get('Scanner', 'allow_domain')
    depth_limit = config.get('Scanner', 'depth_limit')
    proxy_port = config.get('Scanner', 'proxy_port')

    switch_ons = [_[0] for _ in config.items('Modules') if _[1] == 'ON']

    # make dictionary
    config = dict()

    config['crawler'] = dict()
    config['crawler']['crawler'] = {'filetype': filetype,
                                    'allow_domain': allow_domain}
    config['crawler']['download_parser'] = {'cookie': cookie,
                                            'depth_limit': depth_limit,
                                            'filetype': filetype}

    config['scanner'] = dict()
    config['scanner']['sql_scanner'] = {'cookie': cookie,
                                        'on': 'sql_scanner' in switch_ons}
    config['scanner']['xss_scanner'] = {'cookie': cookie,
                                        'on': 'xss_scanner' in switch_ons}

    config['click_proxy'] = {'port': proxy_port,
                             'filetype': filetype,
                             'allow_domain': allow_domain,
                             'on': 'click_proxy' in switch_ons}
    return server_addr, clients_addr, init_url, config


def init_logger():
    _logger = logging.getLogger(__name__.split('.')[0])

    """
    因为服务器不会关闭，所以这里的logger会长期随着python进程存在，
    扫描器除第一次之外，启动的时候，全局的logger还拥有之前设置的
    handlers，也就意味着已经存在至少一个filehandler，此时如果
    在添加一个filehandler，就会出现文件被两个handler写的情况。内
    容会翻倍。同样适用于console的输出。

    如果只是单纯的沿用第一次生成的filehandler，而不是新建一个，
    其文件写指针已经到了第一次的末尾，此时即便如果删掉了源文件，
    也会继续写指针的位置，形成空行，所以比较保险的做法是关闭之前
    的handler，然后添加新的。
    """
    if _logger.handlers:
        for handler in _logger.handlers:
            handler.close()
        _logger.handlers = []

    fmt = '[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s.'
    datefmt = '%H:%M:%S'
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)

    # 输出到文件中时以\x00为分隔符
    fmt = '[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s.\x00'
    datefmt = '%H:%M:%S'
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    log = './AchillesServer/extra/log/server.log'
    log_file = logging.FileHandler(log, mode='w')
    log_file.setLevel(logging.DEBUG)
    log_file.setFormatter(formatter)

    _logger.setLevel(logging.DEBUG)
    _logger.addHandler(console)
    _logger.addHandler(log_file)
    _logger.propagate = False


def gen_random_cid(cids, obj):
    from random import randint
    while True:
        cid = '%08X' % randint(0, 0x100000000 - 1)
        if cid not in cids:
            cids[cid] = obj
            return cid
    pass


def show_info():
    logger.info('SSL proxy requires mitmproxy-certs to be installed, '
                'which can be located at /thirdparty/mitmproxy/')
