#!/usr/bin/env python
# -*- encoding:utf-8 -*-

"""
File:       run.py
Author:     Himyth
"""

from AchillesClient.AchillesClient import AchillesClient


def main():
    import sys
    addr = check_args(sys.argv)
    if not addr:
        usage()
        return

    client = AchillesClient(addr)
    client.start()
    client.join()


def check_args(argv):
    if len(argv) != 5:
        return False
    if argv[1] != '-h' or argv[3] != '-p':
        return False
    return argv[2] + ':' + argv[4]


def usage():
    print 'Usage: python thisscript.py -h bind_addr -p bind_port'

if __name__ == '__main__':
    main()
