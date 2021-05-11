#!/bin/bash

cd /srv/wcdo/
source venv/bin/activate
cd /srv/wcdo/src_data/
python3 -u article_features.py > article_features.log
