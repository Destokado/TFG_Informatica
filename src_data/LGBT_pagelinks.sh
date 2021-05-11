#!/bin/bash

cd /srv/wcdo/
source venv/bin/activate
cd /srv/wcdo/src_data/
python3 -u LGBT_pagelinks_ccc.py > lgbt_pagelinks.log
