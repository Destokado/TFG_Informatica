#!/bin/bash

cd /srv/wcdo/
source venv/bin/activate
cd /srv/wcdo/src_data/
python3 -u wikipedia_diversity.py > wikipedia_diversity.log
