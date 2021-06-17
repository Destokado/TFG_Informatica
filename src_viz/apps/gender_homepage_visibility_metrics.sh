#!/bin/bash

cd /srv/wcdo/
source venv/bin/activate
cd /srv/wcdo/src_viz/apps_dev
python3 -u gender_homepage_visibility_metrics.py > gender_homepage_visibility_metrics.log
