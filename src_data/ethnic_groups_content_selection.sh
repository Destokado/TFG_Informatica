#!/bin/bash

cd /srv/wcdo/
source venv/bin/activate
cd /srv/wcdo/src_data/
python3 -u ethnic_groups_content_selection.py > ethnic_groups_content_selection.log
