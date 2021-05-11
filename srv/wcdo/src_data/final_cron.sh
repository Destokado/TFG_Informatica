#!/bin/bash

cd /srv/wcdo/
source venv/bin/activate

cd /srv/wcdo/src_data/
python3 -u diversity_observatory.py
python3 -u content_selection.py
python3 -u article_features.py
python3 -u history_features.py
python3 -u stats_generation.py

cd /srv/wcdo/src_viz/

python3 -u meta_update.py
