#!/bin/bash

cd /srv/wcdo/
source venv/bin/activate
cd /srv/wcdo/src_data/
python3 -u missing_ccc_selection.py > missing_ccc_selection.log
