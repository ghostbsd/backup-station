#!/usr/bin/env sh

xgettext src/boot-environments.py -o src/locale/boot-environments.pot
xgettext src/askpass.py -o src/locale/askpass.pot

msgmerge -U src/locale/ru/boot-environments.po src/locale/boot-environments.pot
msgmerge -U src/locale/ru/askpass.po src/locale/askpass.pot
