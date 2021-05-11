# -*- coding: utf-8 -*-

import flask
from flask import Flask, request, render_template
from flask import send_from_directory
from dash import Dash
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_table
from dash.dependencies import Input, Output, State
import squarify
# viz
import plotly
import plotly.figure_factory as ff
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
# data
import pandas as pd
import sqlite3
import urllib
from urllib.parse import urlparse, parse_qsl, urlencode
# other
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import datetime
import time
import random
import json

# script
import wikilanguages_utils


databases_path = 'databases/'

territories = wikilanguages_utils.load_wikipedia_languages_territories_mapping()
languages = wikilanguages_utils.load_wiki_projects_information();

wikilanguagecodes = languages.index.tolist()



######

import csv

conn = sqlite3.connect(databases_path + 'wikipedia_diversity_production.db'); cursor = conn.cursor()
#conn = sqlite3.connect(databases_path + 'lgbt_content.db'); cursor = conn.cursor()


path = 'LGBTQ.tsv'
#path = 'LGBTQ_alternate.tsv'


c = csv.writer(open(path,'a'), lineterminator = '\n', delimiter='\t')


headers = ['language','qitem', 'page_id', 'page_title', 'date_created', 'date_last_edit', 'first_timestamp_lang', 'geocoordinates', 'iso3166', 'iso31662', 'region', 'gender', 'ethnic_group', 'supra_ethnic_group', 'sexual_orientation', 'num_inlinks_from_women', 'num_outlinks_to_women', 'percent_inlinks_from_women', 'percent_outlinks_to_women', 'num_inlinks_from_men', 'num_outlinks_to_men', 'percent_inlinks_from_men', 'percent_outlinks_to_men', 'num_inlinks_from_lgbt', 'num_outlinks_to_lgbt', 'percent_inlinks_from_lgbt', 'percent_outlinks_to_lgbt', 'ccc_binary','ccc', 'folk', 'earth', 'monuments_and_buildings', 'music_creations_and_organizations', 'sport_and_teams', 'food', 'paintings', 'glam', 'books', 'clothing_and_fashion', 'industry', 'religion', 'time_interval', 'start_time', 'end_time', 'lgbt_topic', 'lgbt_keyword_title', 'num_bytes', 'num_references', 'num_images', 'num_inlinks', 'num_outlinks', 'num_edits', 'num_edits_last_month', 'num_editors', 'num_discussions', 'num_pageviews', 'num_interwiki', 'num_wdproperty', 'featured_article', 'wikirank']


#headers = ['language','qitem', 'page_id', 'page_title', 'lgbt_biography', 'keyword', 'category_crawling_level', 'num_inlinks_from_lgbt', 'num_outlinks_to_lgbt', 'percent_inlinks_from_lgbt', 'percent_outlinks_to_lgbt', 'lgbt_binary']
c.writerow(headers)

print (wikilanguagecodes)

#wikilanguagecodes = ['es', 'et', 'eu', 'ext', 'fa', 'ff', 'fi', 'fiu_vro', 'fj', 'fo', 'fr', 'frp', 'frr', 'fur', 'fy', 'ga', 'gag', 'gan', 'gd', 'gl', 'glk', 'gn', 'gom', 'gor', 'got', 'gu', 'gv', 'ha', 'hak', 'haw', 'he', 'hi', 'hif', 'ho', 'hr', 'hsb', 'ht', 'hu', 'hy', 'hz', 'ia', 'id', 'ie', 'ig', 'ii', 'ik', 'ilo', 'inh', 'io', 'is', 'it', 'iu', 'ja', 'jam', 'jbo', 'jv', 'ka', 'kaa', 'kab', 'kbd', 'kbp', 'tlh', 'kg', 'ki', 'kj', 'kk', 'kl', 'km', 'kn', 'ko', 'koi', 'kr', 'krc', 'ks', 'ksh', 'ku', 'kv', 'kw', 'ky', 'la', 'lad', 'lb', 'lbe', 'lez', 'lg', 'li', 'lfn', 'lij', 'lmo', 'ln', 'lo', 'lrc', 'lt', 'ltg', 'lv', 'mai', 'map_bms', 'mdf', 'mg', 'mh', 'mhr', 'mi', 'min', 'mk', 'ml', 'mn', 'mr', 'mrj', 'ms', 'mt', 'mus', 'mwl', 'my', 'myv', 'mzn', 'na', 'nah', 'zh_min_nan', 'nap', 'nds', 'nds_nl', 'ne', 'new', 'ng', 'nl', 'nn', 'no', 'nov', 'nrm', 'nso', 'nv', 'ny', 'oc', 'olo', 'om', 'or', 'os', 'pa', 'pag', 'pam', 'pap', 'pcd', 'pdc', 'pfl', 'pi', 'pih', 'pl', 'pms', 'pnb', 'pnt', 'ps', 'pt', 'qu', 'rm', 'rmy', 'rn', 'ro', 'roa_rup', 'roa_tara', 'ru', 'rue', 'rw', 'sa', 'sah', 'sc', 'scn', 'sco', 'sd', 'se', 'sg', 'sh', 'si', 'simple', 'sk', 'sl', 'sm', 'sn', 'so', 'sq', 'sat', 'sr', 'ru_sib', 'srn', 'ss', 'st', 'stq', 'su', 'sv', 'sw', 'szl', 'ta', 'tcy', 'te', 'tet', 'tg', 'th', 'ti', 'tk', 'tl', 'tn', 'to', 'tpi', 'tr', 'ts', 'tt', 'tum', 'tw', 'ty', 'tyv', 'udm', 'ug', 'uk', 'ur', 'uz', 've', 'vec', 'vep', 'vi', 'vls', 'vo', 'wa', 'war', 'wo', 'wuu', 'xal', 'xh', 'xmf', 'yi', 'yo', 'za', 'zea', 'zh', 'zh_classical', 'zh_yue', 'zu', 'shn', 'hyw', 'mnw', 'nqo', 'ban', 'gcr', 'szy', 'lld', 'awa', 'tokipona', 'ary', 'avk', 'smn']



for languagecode in wikilanguagecodes:
	print (languagecode)
	query = 'SELECT "'+languagecode+'", qitem, page_id, page_title, date_created, date_last_edit, first_timestamp_lang, geocoordinates, iso3166, iso31662, region, gender, ethnic_group, supra_ethnic_group, sexual_orientation, num_inlinks_from_women, num_outlinks_to_women, percent_inlinks_from_women, percent_outlinks_to_women, num_inlinks_from_men, num_outlinks_to_men, percent_inlinks_from_men, percent_outlinks_to_men, num_inlinks_from_lgbt, num_outlinks_to_lgbt, percent_inlinks_from_lgbt, percent_outlinks_to_lgbt, ccc_binary, ccc, folk, earth, monuments_and_buildings, music_creations_and_organizations, sport_and_teams, food, paintings, glam, books, clothing_and_fashion, industry, religion, time_interval, start_time, end_time, lgbt_topic, lgbt_keyword_title, num_bytes, num_references, num_images, num_inlinks, num_outlinks, num_edits, num_edits_last_month, num_editors, num_discussions, num_pageviews, num_interwiki, num_wdproperty, featured_article, wikirank FROM '+languagecode+'wiki;'

#	query = 'SELECT "'+languagecode+'", qitem, page_id, page_title, lgbt_biography, keyword, category_crawling_level, num_inlinks_from_lgbt, num_outlinks_to_lgbt, percent_inlinks_from_lgbt, percent_outlinks_to_lgbt, lgbt_binary FROM '+languagecode+'wiki_lgbt;'

	# cursor.execute(query)

	try:
	    cursor.execute(query)
	except:
		print ('no ha funcionat')
		continue

	i = 0
	for result in cursor:
	    i+=1
	    c.writerow(result)
	print (i)

print ('fí')
input('')
