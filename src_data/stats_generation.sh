#!/bin/bash

cd /srv/wcdo/
source venv/bin/activate
cd /srv/wcdo/src_data/
python3 -u stats_generation.py > stats_generation.log
