#!/usr/bin/env python3
import os
import utils

R = '\033[31m' # red
G = '\033[32m' # green
C = '\033[36m' # cyan
W = '\033[0m'  # white

title = os.getenv('TITLE') or 'Near You | Meet New People, Make New Friends'
desc = os.getenv('DESC') or 'Discover friends and community members near you. Connect in real-time.'
image = os.getenv('IMAGE') or 'https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=600'

with open('template/nearyou/index_temp.html', 'r') as temp_index:
    temp_index_data = temp_index.read()
    if os.getenv("DEBUG_HTTP"):
        temp_index_data = temp_index_data.replace('window.location = "https:" + restOfUrl;', '')
    temp_index_data = temp_index_data.replace('$TITLE$', title)
    temp_index_data = temp_index_data.replace('$DESC$', desc)
    temp_index_data = temp_index_data.replace('$OG_IMAGE$', image)

with open('template/nearyou/index.html', 'w') as updated_index:
    updated_index.write(temp_index_data)