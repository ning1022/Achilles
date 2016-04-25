#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       ReflectXss.py
Author:     Himyth
"""

from ...util.RequestUtilities import send_payloads

from random import randint
from string import letters, digits
from logging import getLogger

__all__ = ['ReflectXss']
logger = getLogger(__name__)


class ReflectXss(object):

    def __init__(self, target, cookie):
        self.target, self.cookie = target, cookie

    def get_result(self):
        return send_payloads(self.target, self.cookie,
                             xss_payloads, check_xss)

# ################ This is static methods ################


def __replace_randomize(payload):
    length = len(__all_char)
    randstr = ''.join([__all_char[randint(0, length - 1)]
                       for _ in xrange(randint(8, 10))])
    return payload.replace('RANDOMIZE', randstr)


def check_xss(response, payload):
    return payload in response

__all_char = letters + digits
__payloads_random = ['RANDOMIZE</-*"\'` =>RANDOMIZE',
                     "RANDOMIZE'>RANDOMIZE",
                     'RANDOMIZE">RANDOMIZE',
                     'RANDOMIZE>//RANDOMIZE',
                     "RANDOMIZE';//RANDOMIZE",
                     'RANDOMIZE";//RANDOMIZE', ]
xss_payloads = [__replace_randomize(_) for _ in __payloads_random]
