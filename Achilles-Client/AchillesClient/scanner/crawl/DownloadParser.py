#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       Downloader.py
Author:     Himyth
"""


from ..util.BaseManager import BaseManager
from ..util.UrlUtilities import get_path, get_ext, multi_replace, get_netloc
from ..util.Constant import TASK_URL, HTTP_POST, TASK_NO_MORE
from ..util.ParseUtilities import parse_page
from ..util.BaseGeventThread import BaseGeventThread

from logging import getLogger
import re
import os
import time
from random import randint

# monkey is evil, try to avoid
# from gevent import monkey
# monkey.patch_subprocess()
# import subprocess
# from gevent import subprocess
import subprocess
from gevent import sleep

__all__ = ['DownloadParserManager']
logger = getLogger(__name__)


class DownloadParser(BaseGeventThread):

    def __init__(self, tasks, results, cookie, coroutine_num=0):
        """
        :param tasks, results:  Queue for in and out
        :param cookie:          (domain for cookie, cookie)
        :param coroutine_num:   number of coroutines, default to 0
        """

        # _co_num is default coroutine number, *cpu threads num*
        # _path is the phantomjs executable path
        # _encoding is the terminal input encoding
        _co_num, _path, _encoding = platform_dependency()
        super(DownloadParser, self).__init__(tasks=tasks,
                                             results=results,
                                             cort_num=coroutine_num,
                                             _cort_num=_co_num,
                                             logger=logger)

        self.worker_args = ([], cookie, _path, _encoding)

    def worker(self, *download_args):
        # ugly but useful
        download_args = list(download_args)
        temp_file = get_temp_file(download_args[0])
        download_args.remove(download_args[0])
        download_args.append(temp_file)
        download_args = tuple(download_args)

        while True:
            target = self.tasks.get()

            # put a TASK_NO_MORE to shut this down
            if target is TASK_NO_MORE:
                break
            logger.debug('Fetching URL "%s"' % target.url)

            source_code = download_page(target, *download_args)
            self.results.put(parse_page(target, source_code))

        # delete the temp_file
        try:
            os.unlink(temp_file)
        finally:
            return

# ################ This is for Manager ################


class DownloadParserManager(BaseManager):

    def __init__(self, tasks, results, args):
        """
        """
        self.depth_limit = args['depth_limit']
        self.filetype = re.compile(args['filetype'], re.IGNORECASE)
        self.logout = re.compile(r'.*?(?:sign|check|log)out', re.IGNORECASE)

        download_parser = DownloadParser(tasks=tasks,
                                         results=results,
                                         cookie=args['cookie'])

        super(DownloadParserManager, self).__init__(tasks, results, download_parser)
        logger.debug('Started')

    # 不符合深度、扩展名、logout要求的URL，不进行处理
    def put(self, task):
        if task[0] != TASK_URL:
            return

        task = task[1]

        # depth limitation
        if task.depth >= self.depth_limit:
            return

        # url extention filter, except which is empty
        # get_ext returns '' or '.xxx'
        ext = get_ext(task.url)
        if not self.filetype.match(ext[1:]) and ext != '':
            return

        # careful with logout url, save the cookies
        if self.logout.match(get_path(task.url)):
            return

        self.tasks.put(task)

    def kill(self):
        # kill the download_parser
        for i in xrange(self.module.coroutine_num):
            self.tasks.put(TASK_NO_MORE)

        logger.debug('Exit')

# ################ This is static methods ################


def download_page(target, cookie, phantomjs, term_encoding, temp_file):
    """
    :target:            target url as UrlItem
    :cookie:            (domain for cookie, cookie)
    :phantomjs:         platform dependent path
    :term_encoding:     terminal dependent encoding
    :temp_file:         temp file for phantomjs
    :return:    source code
    """
    _pj = phantomjs
    _op = '--disk-cache=true --load-images=false --web-security=false ' \
          '--ignore-ssl-errors=true --ssl-protocol=any --output-encoding=UTF8'
    _js = '"./AchillesClient/thirdparty/phantomjs/EvalJS.js"'
    _me = '"POST"' if target.method == HTTP_POST else '"GET"'
    cmd = ' '.join([_pj, _op, _js, _me, ''])
    cmd += filter_strs([target.url, target.data, get_netloc(target.url), cookie])

    # since phantomjs ensures the source to be in *utf-8* encoding
    # and parse_page will have result varies from *unicode* to
    # *utf-8* encoding, so if it is not *unicode*, then decode it
    # to *unicode* with *utf-8* encoding
    if type(cmd) is not unicode:
        cmd = cmd.decode('utf8')

    # and here, encode it to platform-dependent encoding
    cmd = cmd.encode(term_encoding)

    # phantomjs存在偶尔崩溃的情况，总的尝试三次，都失败则放弃
    retry = 3
    for _ in xrange(retry):
        try:
            """
            # 最开始使用gevent.subprocess.check_output试图来以协程的方式来等待进程执行，
            # 在Windows没有问题，但是POSIX的信号机制使得这个方法不能在子线程里用，所以这个
            # 方法就不能在Unix类的系统上运行。

            result = subprocess.check_output(cmd.encode(term_encoding),
                                             stderr=subprocess.STDOUT,
                                             shell=True,
                                             universal_newlines=True)

            # 采取折中的办法，使用系统的subprocess.Popen来执行，并利用gevent.sleep来使协程
            # 工作，但是因为Popen的PIPE太小，如果直接将STDOUT输到subprocess.PIPE，很容易使
            # 子进程的输出阻塞，从而使进程无法结束，所以这里需要用到临时文件，将下载的结果保存
            # 到临时文件中，然后再读出来。
            """
            fh = open(temp_file, 'wb')
            process = subprocess.Popen(args=cmd,
                                       stdout=fh,
                                       stderr=subprocess.STDOUT,
                                       shell=True,
                                       universal_newlines=True)
            while process.poll() is None:
                sleep(0.2)
            fh.close()
            result = open(temp_file, 'rb').read()

            """
            # 因为使用Popen并不会在运行出错的情况下抛出异常，所以这里要主动抛出异常
            """
            retcode = process.poll()
            if retcode:
                raise subprocess.CalledProcessError(retcode, cmd, output=result)
        except subprocess.CalledProcessError as _exc:
            exc = _exc
            sleep(1)
            continue
        except Exception as e:
            logger.error(str(e))
            return ''
        return result
    else:
        logger.error('Phantomjs crashed, stderr output saved to log')
        format_time = time.strftime('%Y-%m-%d %H:%M:%S',
                                    time.localtime(time.time()))
        _log_path = './AchillesClient/extra/log/phantomjs.txt'
        try:
            f = open(_log_path, 'r+')
            f.seek(0, os.SEEK_END)
        except:
            f = open(_log_path, 'w')

        msg = '\n'.join(['', format_time, cmd, exc.output, target.url, ''])
        msg += '===========================================================\n'

        f.write(msg)
        f.close()
        return ''


def filter_strs(strs):
    def x(s): return '"' + multi_replace(s, [('\\', '\\\\'), ('"', '\\"')]) + '"'
    return ' '.join([x(_) for _ in strs])


def platform_dependency():
    import platform
    _sys = platform.system()
    _sys += platform.architecture()[0] if _sys == 'Linux' else ''

    # phantomjs path
    _base = './AchillesClient/thirdparty/phantomjs/phantomjs-'
    exes = {'Windows':      'windows',
            'Darwin':       'macosx',
            'Linux32bit':   'linux-x86',
            'Linux64bit':   'linux-x64'}

    # cannot find a matching system
    if _sys not in exes:
        raise NameError('No platform matched, quit.')

    _path = filter_strs([_base + exes[_sys]])

    # default the cpu threads number
    from multiprocessing import cpu_count
    _cpu = cpu_count()

    # terminal default encoding
    import sys
    _encoding = sys.stdin.encoding

    return _cpu, _path, _encoding


# a random file name not in flist
def get_temp_file(flist):
    _filename = ('./AchillesClient/extra/temp/phantomjs/%08X' %
                 randint(0, 0x100000000 - 1))
    if _filename in flist:
        return get_temp_file(flist)
    flist.append(_filename)
    return _filename
