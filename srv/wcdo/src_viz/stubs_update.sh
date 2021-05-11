#!/bin/bash

cd /srv/wcdo/
source venv/bin/activate
cd /srv/wcdo/src_viz/
python3 -u stubs_update.py > stubs_update.log
