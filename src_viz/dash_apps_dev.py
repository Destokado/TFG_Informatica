# -*- coding: utf-8 -*-

# flash dash
import flask
from flask import Flask, request, render_template
from flask import send_from_directory
from dash import Dash
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_table
import dash_table_experiments as dt
from dash.dependencies import Input, Output, State
# dash bootstrap components
import dash_bootstrap_components as dbc

# viz
import plotly
import chart_studio.plotly as py
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# data
import urllib
from urllib.parse import urlparse, parse_qsl, urlencode
import pandas as pd
import sqlite3
import xlsxwriter

# other
import numpy as np
import random
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import datetime
import time
import requests
import subprocess


# script
from update_top_diversity_interwiki import *
sys.path.insert(0, '/srv/wcdo/src_data')
import wikilanguages_utils

setting_up_time = time.time()

##### DATA RESOURCES FOR ALL APPS #####
databases_path = '/srv/wcdo/databases/'

last_period = wikilanguages_utils.get_last_accumulated_period_year_month()
#last_period = '2019-05' # CHANGE WHEN THE NEXT stats.db IS COMPUTED.


territories = wikilanguages_utils.load_wikipedia_languages_territories_mapping()
languages = wikilanguages_utils.load_wiki_projects_information();

wikipedialanguage_numberarticles = wikilanguages_utils.load_wikipedia_language_editions_numberofarticles(sorted(languages.index.tolist()),'production')
wikilanguagecodes = list(wikipedialanguage_numberarticles.keys())

for i in (set(languages.index.tolist()) - set(list(wikipedialanguage_numberarticles.keys()))):
    try: languages.drop(i, inplace=True); territories.drop(i, inplace=True)
    except: pass


# Only those with a geographical context
languageswithoutterritory=list(set(languages.index.tolist()) - set(list(territories.index.tolist())))
for languagecode in languageswithoutterritory: wikilanguagecodes.remove(languagecode)

language_names_list = []
language_names = {}
language_names_full = {}
language_name_wiki = {}
for languagecode in wikilanguagecodes:
    lang_name = languages.loc[languagecode]['languagename']+' ('+languagecode+')'
    language_name_wiki[lang_name]=languages.loc[languagecode]['languagename']
    language_names_full[languagecode]=languages.loc[languagecode]['languagename']
    language_names[lang_name] = languagecode
    language_names_list.append(lang_name)

language_names_list = sorted(language_names_list)
language_names_inv = {v: k for k, v in language_names.items()}

lang_groups = list()
lang_groups += ['Top 5','Top 10', 'Top 20', 'Top 30', 'Top 40']#, 'Top 50']
lang_groups += territories['region'].unique().tolist()
lang_groups += territories['subregion'].unique().tolist()
try: lang_groups.remove(''); 
except: pass

#closest_langs = wikilanguages_utils.obtain_closest_for_all_languages(wikipedialanguage_numberarticles, wikilanguagecodes, 4)


country_names, regions, subregions = wikilanguages_utils.load_iso_3166_to_geographical_regions()
country_names_inv = {v: k for k, v in country_names.items()}

countries_list = list(set(country_names.values()))
subregions_list = list(set(subregions.values()))
regions_list = list(set(regions.values()))

ISO31662_subdivisions_dict, subdivisions_ISO31662_dict = wikilanguages_utils.load_iso_31662_to_subdivisions()

ISO31662_subdivisions, subdivisions_ISO31662 = wikilanguages_utils.load_iso_31662_to_subdivisions_names()

subregions_regions = {}
for x,y in subregions.items():
    subregions_regions[y]=regions[x]

language_countries = {}
for languagecode in wikilanguagecodes:
    countries = wikilanguages_utils.load_countries_from_language(languagecode,territories)
    countries_from_lang = {}
    for country in countries: countries_from_lang[country_names[country]+' ('+country.lower()+')']=country.lower()
    language_countries[languagecode] = countries_from_lang

language_subdivisions = {}
for languagecode in wikilanguagecodes:
    subdivisions = wikilanguages_utils.load_countries_subdivisions_from_language(languagecode,territories)
    subdivisions_from_lang = {}
    for subdivision in subdivisions:
        if subdivision!=None and subdivision!='':
            subdivisions_from_lang[ISO31662_subdivisions_dict[subdivision]+' ('+subdivision.lower()+')']=subdivision.lower()
    language_subdivisions[languagecode] = subdivisions_from_lang


group_labels = wikilanguages_utils.get_diversity_categories_labels()


##### WEB RESOURCES #####

title_addenda = ' - Wikipedia Diversity Observatory (WDO)'
#external_stylesheets = ['https://wdo-dev.wmcloud.org/assets/bWLwgP.css'] 
external_stylesheets = [dbc.themes.BOOTSTRAP]
external_scripts = ['https://wdo-dev.wmcloud.org/assets/gtag.js']
webtype = ''


##### NAVBAR #####
#LOGO = "https://wdo-dev.wmcloud.org/assets/logo.png"
LOGO = "./assets/logo.png"
LOGO_foot = "./assets/wikimedia-logo.png"
# LOGO = app.get_asset_url('logo.png') # this would have worked. 




navbar = html.Div([
    html.Br(),
    dbc.Navbar(
        [ dbc.Collapse(
                dbc.Nav(
                    [
                    dbc.DropdownMenu(
                        [dbc.DropdownMenuItem("Monuments and Buildings Articles",
                                              href="https://wdo-dev.wmcloud.org/monuments_and_buildings_articles/"),
                        dbc.DropdownMenuItem("Medical Articles", href="https://wdo-dev.wmcloud.org/medical_articles/"),
                        ],
                        label="Tools",
                        nav=True,
                    ),
                    dbc.DropdownMenu(
                        [dbc.DropdownMenuItem("Gender Home Page Gap",href="https://wdo-dev.wmcloud.org/gender_homepage_gap/"),
                        dbc.DropdownMenuItem("Map of Geolocated Articles", href="https://wdo-dev.wmcloud.org/map_of_gaps/"),
                        ],
                        label="Visualizations",
                        nav=True,
                    ),
                    html.A(
                    # Use row and col to control vertical alignment of logo / brand
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src=LOGO, height="35px")),
    #                        dbc.Col(dbc.NavbarBrand("Wikipedia Diversity Observatory", className="mb-5")),
                        ],
                        align="center",
                        no_gutters=True,
                    ),
                    href="https://meta.wikimedia.org/wiki/Wikipedia_Diversity_Observatory", target= "_blank",
                style = {'margin-left':"5px"}),
                ], className="ml-auto", navbar=True),
                id="navbar-collapse2",
                navbar=True,
            ),
        ],
        color="white",
        dark=False,
        className="ml-2",
    ),
    ])


##### FOOTBAR #####
footbar = html.Div([
        html.Br(),
        html.Br(),
        html.Hr(),

        html.Div(
            dbc.Nav(
                [
                    dbc.NavLink("Diversity Observatory Meta-Wiki Page", href="https://meta.wikimedia.org/wiki/Wikipedia_Diversity_Observatory", target="_blank", style = {'color': '#8C8C8C'}),
                    dbc.NavLink("View Source", href="https://github.com/marcmiquel/wcdo", style = {'color': '#8C8C8C'}),
                    dbc.NavLink("Datasets/Databases", href="https://meta.wikimedia.org/wiki/Wikipedia_Diversity_Observatory/Cultural_Context_Content#Datasets", style = {'color': '#8C8C8C'}),
                    dbc.NavLink("Research", href="https://meta.wikimedia.org/wiki/Wikipedia_Diversity_Observatory/Cultural_Context_Content#References", style = {'color': '#8C8C8C'}),
                ], className="ml-2"), style = {'textAlign': 'center', 'display':'inline-block' , 'width':'60%'}),

        html.Div(id = 'current_data', children=[        
            'Updated with dataset from: ',
            html.B(last_period)],
#            html.B(current_dataset_period_stats)],
            style = {'textAlign':'right','display': 'inline-block', 'width':'40%'}),
        html.Br(),
        html.Div([
            html.P('Hosted with ♥ on ',style = {'display':'inline-block'}),
            html.A('Wikimedia Cloud VPS',href='https://wikitech.wikimedia.org/wiki/Portal:Cloud_VPS', target="_blank", style = {'display':'inline-block'}),
            html.P('.',style = {'display':'inline-block', 'margin-right':"5px"}),
            html.A(html.Img(src=LOGO_foot, height="35px"),href='https://wikitech.wikimedia.org/wiki/Help:Cloud_Services_Introduction', target="_blank", style = {'display':'inline-block'}),

            ], style = {'textAlign':'right'}
            ),
        html.Br(),
    ])




##### FLASK APP #####
app_dev = flask.Flask(__name__)

if __name__ == '__main__':
    app_dev.run_server(host='0.0.0.0', threaded=True)

# @app.route('/')
# def main():
#     return flask.redirect('https://meta.wikimedia.org/wiki/Wikipedia_Diversity_Observatory')

@app_dev.route('/gender_homepage_gap')
def gender_homepage():
    return flask.redirect('https://wdo-dev.wmcloud.org/gender_homepage_gap')

@app_dev.route('/monuments_and_buildings_articles')
def monuments():
    return flask.redirect('https://wdo-dev.wmcloud.org/monuments_and_buildings_articles/')

@app_dev.route('/medical_articles')
def medical():
    return flask.redirect('https://wdo-dev.wmcloud.org/medical_articles/')

#@app_dev.route('/map_of_gaps/')
#def map_of_gaps():
#    return flask.redirect('https://wdo-dev.wmcloud.org/map_of_gaps/')


@app_dev.errorhandler(404)
def handling_page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404





##### DASH APPS #####

print ('* importing apps.')

# others
from apps_dev.home_app import *


# visualizations
# from apps_dev.language_territories_mapping_app import *
# from apps_dev.cultural_context_content_app import *

# from apps_dev.ccc_coverage_spread_apps import *
# from apps_dev.geography_gap_app import *
# from apps_dev.gender_gap_app import *
# from apps_dev.top_ccc_coverage_spread_apps import *

# from apps_dev.ethnic_groups_gap_app import *
# from apps_dev.religious_groups_gap_app import *
# from apps.lgbtq_gap_app import *
# from apps_dev.time_gap_app import *

# from apps_dev.topical_coverage_app import *
# from apps_dev.last_month_pageviews_app import *
# from apps_dev.diversity_over_time_app import *
from apps_dev.gender_homepage_app import *
from apps_dev.map_of_gaps_app import *

# tools
from apps_dev.monuments_and_buildings_articles_app import *
from apps_dev.medical_articles_app import *
# from apps_dev.missing_ccc_app import *
# from apps_dev.common_ccc_app import *
# from apps_dev.visual_ccc_app import *
# from apps_dev.search_ccc_app import *
# from apps_dev.incomplete_ccc_app import *

# from apps_dev.lgbtq_articles_app import *
# from apps_dev.ethnic_groups_articles_app import *
# from apps_dev.time_articles_app import *
# from apps_dev.recent_changes_diversity_app import *


##### FUNCTIONS #####
# parse
def parse_state(url):
    parse_result = urlparse(url)
    params = parse_qsl(parse_result.query)
    state = dict(params)
#    print (state)
    return state

# layout
def apply_default_value(params):
    def wrapper(func):
        def apply_value(*args, **kwargs):
            if 'id' in kwargs and kwargs['id'] in params:
                kwargs['value'] = params[kwargs['id']]
            return func(*args, **kwargs)
        return apply_value
    return wrapper


def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]


def get_item_labels(df, langcode):
    headers = {
        'User-Agent': 'WikipediaDiversityObservatory WDO (https://meta.wikimedia.org/wiki/Wikipedia_Diversity_Observatory;'
                      'tools.wcdo@tools.wmflabs.org) python-requests/2.18.4'}
    # Divide list of items into size 50 (Limit of API)
    divided = divide_chunks(df.values.tolist(), 50)
    labels_dict = {}
    for chunk in divided:
        query = 'https://www.wikidata.org/w/api.php?action=wbgetentities&props=labels&ids={}&languages={}&format=json'.format(
            '|'.join(chunk), langcode + '|en')
        response = requests.get(query, headers=headers)
        data = response.json()
        for q in data['entities']:
            try:
                labels_dict[q] = data['entities'][q]['labels'][langcode]['value'].capitalize()
            except KeyError as e:
                try:
                    labels_dict[q] = data['entities'][q]['labels']['en'][
                        'value'].capitalize()+' (en)'  # If doesn't exist in source lang, get it in EN
                except Exception as exep:
                    print('{}}: Something wrong with QITEM {} with data {}'.format(ex, q, data['entities'][q]))
                    labels_dict[q] = 'N/A' #If it doesn't have laben in either target or english, assign random
            except Exception as ex:
                labels_dict[q] = 'N/A'
                print('{}}: Something wrong with QITEM {} with data {}'.format(ex, q, data['entities'][q]))

    return labels_dict

##### EXECUTING FUNCTIONS #####

print ('* dash_apps_dev loaded after: '+str(datetime.timedelta(seconds=time.time() - setting_up_time)))
print ('\n\n\n*** START WDO APP:'+str(datetime.datetime.now()))



# # UPDATE TOP CCC INTERWIKIS AND INTERSECTIONS
# while True:
#     # DAILY
#     # print ('hi!')
#     time.sleep(84600)
#     print ("Good morning. Update the Top Diversity Lists Interwiki and Intersections: "+str(datetime.datetime.now()))
#     update_top_diversity_articles_interwiki()
#     # update_top_diversity_interwiki.update_top_diversity_articles_intersections() # this needs to be tested with the new database.
#     print ("done.")
#     # time.sleep(84600)