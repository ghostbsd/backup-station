#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
from glob import glob
from setuptools import setup

import DistUtilsExtra.command.build_extra
import DistUtilsExtra.command.build_i18n
import DistUtilsExtra.command.clean_i18n

# to update i18n .mo files (and merge .pot file into .po files):
# ,,python setup.py build_i18n -m''

for line in open('be-station').readlines():
    if line.startswith('__VERSION__'):
        exec(line.strip())
        break
# Silence flake8, __VERSION__ is properly assigned below
else:
    __VERSION__ = '1.0'

PROGRAM_VERSION = __VERSION__


def datafilelist(installbase, sourcebase):
    datafileList = []
    for root, subFolders, files in os.walk(sourcebase):
        fileList = []
        for f in files:
            fileList.append(os.path.join(root, f))
        datafileList.append((root.replace(sourcebase, installbase), fileList))
    return datafileList


prefix = sys.prefix


# '{prefix}/share/man/man1'.format(prefix=sys.prefix), glob('data/*.1')),

data_files = [
    (f'{prefix}/share/applications', ['be-station.desktop']),
    (f'{prefix}/etc/sudoers.d', ['sudoers.d/be-station']),
]

data_files.extend(datafilelist('{prefix}/share/locale'.format(prefix=sys.prefix), 'build/mo'))

cmdclass ={
     "build": DistUtilsExtra.command.build_extra.build_extra,
     "build_i18n": DistUtilsExtra.command.build_i18n.build_i18n,
     "clean": DistUtilsExtra.command.clean_i18n.clean_i18n,
}

setup(name="be-station",
      version=PROGRAM_VERSION,
      description="GhostBSD boot environment manager",
      license='BSD',
      author='Eric Turgeon',
      url='https://github.com/GhostBSD/be-station/',
      packages=[],
      data_files=data_files,
      install_requires=['setuptools', 'bectl'],
      scripts=['be-station'],
      cmdclass = cmdclass)
