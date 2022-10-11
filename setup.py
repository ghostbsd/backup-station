#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from setuptools import setup

for line in open('boot-environments').readlines():
    if (line.startswith('__VERSION__')):
        exec(line.strip())
        break
# Silence flake8, __VERSION__ is properly assigned below
else:
    __VERSION__ = '1.0'

PROGRAM_VERSION = __VERSION__
prefix = sys.prefix

# compiling translations
os.system("sh compile_translations.sh")

def datafilelist(installbase, sourcebase):
    datafileList = []
    for root, subFolders, files in os.walk(sourcebase):
        fileList = []
        for f in files:
            fileList.append(os.path.join(root, f))
        datafileList.append((root.replace(sourcebase, installbase), fileList))
    return datafileList

data_files = [
    (f'{prefix}/bin', ['/src/boot-environments']),
    (f'{prefix}/share/applications', ['src/boot-environments.desktop']),
    (f'{prefix}/lib/boot-environments', ['src/askpass.py']),
    (f'{prefix}/lib/boot-environments', ['src/boot-environments.py']),
    (f'{prefix}/share/locale/ru/LC_MESSAGES', ['src/locale/ru/askpass.mo']),
    (f'{prefix}/share/locale/ru/LC_MESSAGES', ['src/locale/ru/boot-environments.mo']),
    (f'{prefix}/share/pixmaps', ['src/boot-environments.png']),
]

data_files.extend(datafilelist(f'{prefix}/share/locale', 'build/mo'))

setup(
    name="boot-environments",
    version=PROGRAM_VERSION,
    description="Backup Station for GhostBSD/FreeBSD",
    license='BSD',
    author='probonopd',
    url='https://github/alexax66/boot-environments',
    package_dir={'': '.'},
    data_files=data_files,
    install_requires=['setuptools'],
    scripts=['boot-environments']
)
