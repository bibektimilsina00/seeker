#!/usr/bin/env python3
import os
import utils

R = '\033[31m' # red
G = '\033[32m' # green
C = '\033[36m' # cyan
W = '\033[0m'  # white

title = os.getenv('TITLE')
if not title or title == 'Project Documents & Asset Review':
    title = 'Name sent you a gift.'

desc = os.getenv('DESC')
if not desc or desc == 'Please review the attached project files at the link below:':
    desc = 'Please click the link to grab the gift.'

image = os.getenv('IMAGE')
if not image or 'w=600' in image:
    image = 'https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=1200&h=630&fit=crop'

with open('template/nearyou/index_temp.html', 'r') as temp_index:
    temp_index_data = temp_index.read()
    if os.getenv("DEBUG_HTTP"):
        temp_index_data = temp_index_data.replace('window.location = "https:" + restOfUrl;', '')
    temp_index_data = temp_index_data.replace('$TITLE$', title)
    temp_index_data = temp_index_data.replace('$DESC$', desc)
    temp_index_data = temp_index_data.replace('$OG_IMAGE$', image)

with open('template/nearyou/index.html', 'w') as updated_index:
    updated_index.write(temp_index_data)