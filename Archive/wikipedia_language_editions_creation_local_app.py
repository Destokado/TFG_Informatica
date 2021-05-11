# -*- coding: utf-8 -*-


import flask
from flask import Flask, request, render_template
from flask import send_from_directory
from dash import Dash
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_table_experiments as dt
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
# other
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import datetime
import time

# script
import wikilanguages_utils


databases_path = 'databases/'

territories = wikilanguages_utils.load_wikipedia_languages_territories_mapping()
languages = wikilanguages_utils.load_wiki_projects_information();

wikilanguagecodes = languages.index.tolist()
languageswithoutterritory=['eo','got','ia','ie','io','jbo','lfn','nov','vo']
# Only those with a geographical context
for languagecode in languageswithoutterritory: wikilanguagecodes.remove(languagecode)

language_names = {}
for languagecode in wikilanguagecodes:
    lang_name = languages.loc[languagecode]['languagename']+' ('+languagecode+')'
    language_names[lang_name] = languagecode

# # web
title_addenda = ' - Wikipedia Diversity Observatory (WDO)'
functionstartTime = time.time()


### DATA ###
conn = sqlite3.connect(databases_path + 'stats.db'); cursor = conn.cursor() 
conn2 = sqlite3.connect(databases_path + 'wikipedia_diversity.db'); cursor2 = conn2.cursor() 

source_lang = 'en'








### ------------------- ### ------------------- ### -------------------

# 1. Creation of Wikipedias by region


first_timestamp = {}
# for languagecode in wikilanguagecodes:
#     query = 'SELECT MIN(date_created) FROM '+languagecode+'wiki;'
#     try:
#         for row in cursor2.execute(query):
#             first_timestamp[languagecode]=row[0]
#     except:
#         print (languagecode)

first_timestamp = {'aa': 20080517105742, 'ab': 20041206142500, 'ace': 20080413081536, 'ady': 20080427041734, 'af': 20011116223018, 'ak': 20040802073305, 'als': 20031227000200, 'am': 20021219231221, 'an': 20040721223304, 'ang': 20041014225930, 'ar': 20030711002302, 'arc': 20040728183303, 'arz': 20080403231428, 'as': 20050322201312, 'ast': 20040720233305, 'atj': 20130604133903, 'av': 20050528024736, 'ay': 20031201004206, 'az': 20020602161944, 'azb': 20081024205859, 'ba': 20020602162346, 'bar': 20050730070214, 'bat_smg': 20060325072256, 'bcl': 20071124215549, 'be': 20060803171202, 'be_x_old': 20031006084806, 'bg': 20031206231136, 'bh': 20040417193652, 'bi': 20030722151817, 'bjn': 20081124082209, 'bm': 20040828213305, 'bn': 20040127164554, 'bo': 20031225063103, 'bpy': 20060803193113, 'br': 20040623075519, 'bs': 20021212224053, 'bug': 20051107024029, 'bxr': 20060330044619, 'ca': 20010317014148, 'cbk_zam': 20060817004342, 'cdo': 20060729232901, 'ce': 20050420155919, 'ceb': 20050623122206, 'ch': 20040729183302, 'cho': 20040922103304, 'chr': 20040526050340, 'chy': 20040922113304, 'ckb': 20040427075123, 'co': 20031130094515, 'cr': 20040828203303, 'crh': 20060920100640, 'cs': 20021114000021, 'csb': 20040401000146, 'cu': 20060625140617, 'cv': 20041122134407, 'cy': 20030712092211, 'da': 20020211105924, 'de': 20010407102011, 'din': 20141104221427, 'diq': 20060326063937, 'dsb': 20051003151933, 'dty': 20140823144906, 'dv': 20050417060755, 'dz': 20051214025753, 'ee': 20040726123304, 'el': 20010821050720, 'eml': 20060909103518, 'en': 20010117001313, 'es': 20010525115355, 'et': 20020824202606, 'eu': 20011206195950, 'ext': 20070206094844, 'fa': 20031219132941, 'ff': 20040828193305, 'fi': 20020909132348, 'fiu_vro': 20050622105117, 'fj': 20020603102120, 'fo': 20040530225042, 'fr': 20010804094916, 'frp': 20060410165045, 'frr': 20030120121549, 'fur': 20050125065526, 'fy': 20020907172305, 'ga': 20031227223153, 'gag': 20071207081807, 'gan': 20070614141509, 'gd': 20021103084741, 'gl': 20030312050012, 'glk': 20061007233441, 'gn': 20030904132158, 'gom': 20070304181043, 'gor': 20110506143034, 'gu': 20031209080004, 'gv': 20030920230203, 'ha': 20020603102658, 'hak': 20070527223124, 'haw': 20040922123305, 'he': 20030708105851, 'hi': 20020225155115, 'hif': 20071011130412, 'ho': 20060514011108, 'hr': 20030216205244, 'hsb': 20051003145438, 'ht': 20040829123308, 'hu': 20030708171244, 'hy': 20040701214519, 'hz': 20040829073307, 'id': 20030530101259, 'ig': 20050302045246, 'ii': 20040829113308, 'ik': 20020603103156, 'ilo': 20051007131503, 'inh': 20070720053549, 'is': 20030117174955, 'it': 20010824094450, 'iu': 20030726212755, 'ja': 20020901221854, 'jam': 20081202080324, 'jv': 20030125054432, 'ka': 20040224211055, 'kaa': 20061123170553, 'kab': 20070506150301, 'kbd': 20090925184015, 'kbp': 20080427054048, 'kg': 20040828173303, 'ki': 20040808143308, 'kj': 20060302183610, 'kk': 20020603103631, 'kl': 20031226140642, 'km': 20020603103712, 'kn': 20030612091121, 'ko': 20021012063430, 'koi': 20090420191545, 'kr': 20060620162714, 'krc': 20070323032715, 'ks': 20030726043702, 'ksh': 20050813142159, 'ku': 20020603104208, 'kv': 20050315140159, 'kw': 20040813164928, 'ky': 20041008123144, 'la': 20020525203818, 'lad': 20050925130914, 'lb': 20040721074516, 'lbe': 20060930195114, 'lez': 20071019213931, 'lg': 20060512092134, 'li': 20040829103306, 'lij': 20060410081304, 'lmo': 20051024070715, 'ln': 20050109162822, 'lo': 20030719174303, 'lrc': 20090124213523, 'lt': 20030220195409, 'ltg': 20060915194805, 'lv': 20030606172705, 'mai': 20040417195217, 'map_bms': 20060324223605, 'mdf': 20070928144102, 'mg': 20040415223633, 'mh': 20040829033304, 'mhr': 20061125165104, 'mi': 20040206185243, 'min': 20090113225544, 'mk': 20030904100457, 'ml': 20021220220025, 'mn': 20040410161738, 'mo': None, 'mr': 20030501195942, 'mrj': 20090122060813, 'ms': 20021026074157, 'mt': 20040726063304, 'mus': 20050911042016, 'mwl': 20080215215722, 'my': 20040730112454, 'myv': 20061127055550, 'mzn': 20060410141904, 'na': 20030809223741, 'nah': 20030815201303, 'zh_min_nan': 20040528022944, 'nap': 20050925163649, 'nds': 20030427220839, 'nds_nl': 20060324233857, 'ne': 20020603114854, 'new': 20060604211915, 'ng': 20051116000628, 'nl': 20010807170658, 'nn': 20040731033303, 'no': 20011206234137, 'nrm': 20060325052047, 'nso': 20070728205437, 'nv': 20040828133314, 'ny': 20040829013312, 'oc': 20030316184935, 'olo': 20070313111157, 'om': 20021203223643, 'or': 20020603115613, 'os': 20050228084641, 'pa': 20020603120025, 'pag': 20060526124340, 'pam': 20050622102213, 'pap': 20060324225048, 'pcd': 20070505110730, 'pdc': 20060325170804, 'pfl': 20060325184617, 'pi': 20050116175240, 'pih': 20051024123726, 'pl': 20010927185222, 'pms': 20060326211524, 'pnb': 20080821171928, 'pnt': 20070923164001, 'ps': 20050217124618, 'pt': 20010617165832, 'qu': 20031122234332, 'rm': 20040609080123, 'rmy': 20060324223109, 'rn': 20040309165041, 'ro': 20030712090540, 'roa_rup': 20040526114915, 'roa_tara': 20060415173421, 'ru': 20021113184805, 'rue': 20070430190912, 'rw': 20020603103746, 'sa': 20040616025431, 'sah': 20061221101826, 'sc': 20040827150014, 'scn': 20041010122309, 'sco': 20050622101703, 'sd': 20051212222007, 'se': 20041007171848, 'sg': 20040309165406, 'sh': 20031012063904, 'si': 20050710142038, 'simple': 20011008124414, 'sk': 20030104002001, 'sl': 20030710090451, 'sm': 20040309165544, 'sn': 20040309165737, 'so': 20041220225312, 'sq': 20031012085518, 'sat': 20120620224005, 'sr': 20030626022340, 'srn': 20071014210708, 'ss': 20040127202114, 'st': 20030918043600, 'stq': 20050622165013, 'su': 20031025010831, 'sv': 20010523100128, 'sw': 20030308043013, 'szl': 20060115223501, 'ta': 20030930183448, 'tcy': 20071105192215, 'te': 20031210011627, 'tet': 20060324224729, 'tg': 20040127190147, 'th': 20030315190951, 'ti': 20040229232144, 'tk': 20040216022600, 'tl': 20040104020215, 'tn': 20040324232945, 'to': 20040115143819, 'tpi': 20040404082920, 'tr': 20021205225128, 'ts': 20040319060351, 'tt': 20030921061124, 'tum': 20041203153317, 'tw': 20031111033943, 'ty': 20050210010831, 'tyv': 20060511132519, 'udm': 20051024070854, 'ug': 20031217114218, 'uk': 20031227004500, 'ur': 20040305131655, 'uz': 20031221073545, 've': 20040828153305, 'vec': 20040119091734, 'vep': 20080219073249, 'vi': 20021116145424, 'vls': 20060329134021, 'wa': 20030622050048, 'war': 20050925130652, 'wo': 20030627184124, 'wuu': 20060515145818, 'xal': 20060325090426, 'xh': 20030609011258, 'xmf': 20080104122928, 'yi': 20040315220350, 'yo': 20040328162518, 'za': 20040729153303, 'zea': 20060930200059, 'zh': 20021030053428, 'zh_classical': 20060801132918, 'zh_yue': 20060325005118, 'zu': 20031130014112, 'shn': 20090705234310, 'hyw': 20060506124847, 'nqo': None, 'ban': None}

for languagecode in wikilanguagecodes:
    try:
        first_timestamp[languagecode]=str(first_timestamp[languagecode])[:4]
    except:
        try:
            del first_timestamp[languagecode]
        except:
            pass
        pass

#   print (first_timestamp)


# Coverage of other languages CCC by Arabic Wikipedia
# set1, set1descriptor, set2, set2descriptor
# set1 (all languages), wp, ccc, wp
# CCC

query = 'SELECT set1 as Wiki, abs_value as ccc_number_articles, rel_value as ccc_percent FROM wdo_intersections_accumulated WHERE period IN (SELECT MAX(period) FROM wdo_intersections_accumulated WHERE set1descriptor = "wp" AND set2descriptor = "ccc" AND content = "articles" AND set1=set2) AND set1descriptor = "wp" AND set2descriptor = "ccc" AND content = "articles" AND set1=set2 ORDER BY abs_value DESC;'

df = pd.read_sql_query(query, conn)
df = df.set_index('Wiki')

df['Language']=languages.languagename

df['wp_number_articles'] = 100*df['ccc_number_articles']/df['ccc_percent']
df.wp_number_articles = df.wp_number_articles.astype(int)

df['ccc_percent'] = round(df['ccc_percent'],2)

df['Region']=languages.region
for x in df.index.values.tolist():
    if ';' in df.loc[x]['Region']: df.at[x, 'Region'] = df.loc[x]['Region'].split(';')[0]

df['Subregion']=languages.subregion
for x in df.index.values.tolist():
    if ';' in df.loc[x]['Subregion']: df.at[x, 'Subregion'] = df.loc[x]['Subregion'].split(';')[0]

df['First timestamp'] = pd.Series(first_timestamp)


# Renaming the columns
columns_dict = {'Language':'Language','wp_number_articles':'Articles','ccc_number_articles':'CCC art.','ccc_percent':'CCC %'}
df=df.rename(columns=columns_dict)
df = df.reset_index()

df = df.rename(columns={0: 'Wiki'})
df = df.fillna('')



print (df.head(10))







### ------------------- ### ------------------- ### -------------------


"""

2. Percentage of articles by languages’ first timestamp
Percentatge d’articles per llengua en els quals han tingut el primer timestamp

* Which Wikipedia language editions did create more first versions of articles?
seleccionar per cada llengua.
# treemap.

SELECT first_timestamp_lang,count(*) FROM cawiki GROUP BY 1 ORDER BY 2 desc limit 10;

SELECT first_timestamp_lang,count(*) FROM cawiki and ccc_binary = 1 GROUP BY 1 ORDER BY 2 desc limit 10;

"""







### ------------------- ### ------------------- ### -------------------


# 3. Feature distribution/histogram (references, images, edits, editors, etc.)

# WINDROSE CHART -> això és per veure els features.

# number of editors.

# això serviria per comparar features de grups d’articles o d’articles sols entre llengües.

wind = px.data.wind()

# for x in df_gender_final_male.index.values.tolist():
#     try:
#         male = df_gender_final_male.loc[x]['Articles']
#     except:
#         male = 0    
#     try:
#         female = df_gender_final_female.loc[x]['Articles']
#     except:
#         female = 0
#     df_gender_final_male.at[x, 'Extent Articles (%)'] =  100*male/(male+female)
#     df_gender_final_female.at[x, 'Extent Articles (%)'] =  100*female/(male+female)

# print (wind)


# Coverage of other languages CCC by Arabic Wikipedia
# set1, set1descriptor, set2, set2descriptor
# set1 (all languages), ccc, ar, wp
# query = 'SELECT set2, set1, rel_value, abs_value FROM wcdo_intersections_monthly WHERE content="articles" AND set1descriptor="ccc" AND set2descriptor = "wp" AND period IN (SELECT MAX(period) FROM wcdo_intersections_monthly) ORDER BY set2, abs_value DESC;'
# df_langs = pd.read_sql_query(query, conn)
# df_langs1 = df_langs.set_index('set2')
# df_langs2 = df_langs1.loc[source_lang]
# labels = df_langs2.set1.tolist()
# values = df_langs2.abs_value.tolist()
# values = df_langs2.rel_value.tolist()




### ------------------- ### ------------------- ### -------------------


# 4. Geolocated articles by features in Density Heatmap



### ------------------- ### ------------------- ### -------------------

### DASH APP ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 
dash_app = Dash()
dash_app.config['suppress_callback_exceptions']=True

title = "Wikipedia Language Editions Creation"
dash_app.title = title+title_addenda
text_scatterplot = ''

dash_app.layout = html.Div([
        html.H3(title, style={'textAlign':'center'}),

        # html.H5('Language CCC Graph'),
        
        # dcc.Graph(id = 'scatterplot'),

        dcc.Dropdown(
            id='source_lang',
            options=[{'label': i, 'value': language_names[i]} for i in sorted(language_names)],
            value='en',
            placeholder="Select a source language",           
            style={'width': '190'}
         ),



        # dcc.Graph(id = 'windrose'),


        
        dcc.Graph(id = 'scatterplot3d'),

        dcc.Graph(id = 'density_heatmap'),



    ])




### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

#### CALLBACKS ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 



# scatterplot
@dash_app.callback(
    Output('scatterplot', 'figure'),
    [Input('source_lang', 'value')])
def update_scatterplot(value):
    source_lang = value

    start, end = 750, 1500

    print (df.head(10))

    df['Period'] = pd.to_datetime(df['First timestamp'])
    df.Articles = df.Articles.astype(int)


    fig = go.Figure(data=go.Scatter3d(
        x=df['Period'],#[start:end],
        y=df['Region'],
        z=df['Articles'],
        text=df['Language'],
        mode='markers',
        marker=dict(
            sizemode='diameter',
#            sizeref=750,
            size=df['Period'],
            color = df['Region'],
            colorscale = 'Viridis',
            # colorbar_title = 'Life<br>Expectancy',
            line_color='rgb(140, 140, 170)'
        )
    ))


    fig.update_layout(height=800, width=800,
                  title='Examining Population and Life Expectancy Over Time')

    # fig = px.scatter(df, x="CCC %", y="Articles", color="Region",
    #              size='CCC %',log_y=True,text="Language", hover_data=['Language'])

    # fig.update_traces(textposition='top center')

    return fig





@dash_app.callback(
    Output('windrose', 'figure'),
    [Input('source_lang', 'value')])
def update_treemap(value):
    source_lang = value

    # això serviria per comparar features de grups d’articles o d’articles sols entre llengües.



    fig = px.bar_polar(wind, r="frequency", theta="direction",
                       color="strength", template="plotly_dark",
                       color_discrete_sequence= px.colors.sequential.Plasma[-2::-1])
    fig.show()

    return fig





# 3D scatterplot
@dash_app.callback(
    Output('scatterplot3d', 'figure'),
    [Input('source_lang', 'value')])
def update_scatterplot(value):
    source_lang = value

    # values = ["11", "12", "13", "14", "15", "20", "30"]
    # labels = ["A1", "A2", "A3", "A4", "A5", "B1", "B2"]
    fig = px.scatter_3d(df, x='First timestamp', y='Region', z='Articles', color="Region",
                 size='Articles',log_z=True,hover_data=['Language'])# text="Language",

    fig.update_layout(height=900, width=900,
                  title='Examining Population and Life Expectancy Over Time')
 
    fig.update_traces(textposition='top center')

    return fig





# density_heatmap
@dash_app.callback(
    Output('density_heatmap', 'figure'),
    [Input('source_lang', 'value')])
def update_density_heatmap(value):
    source_lang = value

    conn2 = sqlite3.connect(databases_path + 'wikipedia_diversity.db'); cursor2 = conn2.cursor() 

    query = "SELECT geocoordinates, ISO3166, REPLACE(page_title,'_', ' ') as page_title, num_edits, num_editors FROM "+source_lang+"wiki WHERE geocoordinates is not null ORDER BY num_editors DESC LIMIT 10000;"

    df = pd.read_sql_query(query, conn2)
    df['Latitude'], df['Longitude'] = df['geocoordinates'].str.split(',', 1).str

    print (df.head(10))
    print (len(df))

    fig = go.Figure(go.Densitymapbox(lat=df.Latitude, lon=df.Longitude, z=df.num_editors, radius=10,  customdata=df.page_title, hovertemplate='%{customdata}<br>number of editors: %{z}<extra></extra>'))

    fig.update_layout(mapbox_style="stamen-terrain") # mapbox_center_lon=180
#    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    # fig.show()

    fig.update_layout(height=800, width=1000,
                  title='The first 10000 articles by number of editors in '+source_lang+'wiki')


    return fig




### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

if __name__ == '__main__':
    dash_app.run_server(debug=True)
