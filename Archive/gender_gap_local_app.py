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
# other
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import datetime
import time

# script
import wikilanguages_utils

from dash_apps import *


##### RESOURCES GENERAL #####


title_addenda = ' - Wikipedia Diversity Observatory (WDO)'

databases_path = 'databases/'

territories = wikilanguages_utils.load_wikipedia_languages_territories_mapping()
languages = wikilanguages_utils.load_wiki_projects_information();

wikilanguagecodes = languages.index.tolist()

language_names_list = []
language_names = {}
language_names_full = {}
for languagecode in wikilanguagecodes:
    lang_name = languages.loc[languagecode]['languagename']+' ('+languagecode+')'
    language_names_full[languagecode]=languages.loc[languagecode]['languagename']
    language_names[lang_name] = languagecode
    language_names_list.append(lang_name)

language_names_inv = {v: k for k, v in language_names.items()}

lang_groups = list()
lang_groups += ['Top 10', 'Top 20', 'Top 30', 'Top 40','All languages']#, 'Top 50']
lang_groups += territories['region'].unique().tolist()
lang_groups += territories['subregion'].unique().tolist()

### for the table
languageswithoutterritory=['eo','got','ia','ie','io','jbo','lfn','nov','vo']
# Only those with a geographical context
for languagecode in languageswithoutterritory: wikilanguagecodes.remove(languagecode)

wikipedialanguage_numberarticles = wikilanguages_utils.load_wikipedia_language_editions_numberofarticles(wikilanguagecodes,'')
for languagecode in wikilanguagecodes:
   if languagecode not in wikipedialanguage_numberarticles: wikilanguagecodes.remove(languagecode)

country_names, regions, subregions = wikilanguages_utils.load_iso_3166_to_geographical_regions()





### DATA ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 

conn = sqlite3.connect(databases_path + 'stats.db'); cursor = conn.cursor() 

gender_dict = {'Q6581097':'male','Q6581072':'female', 'Q1052281':'transgender female','Q1097630':'intersex','Q1399232':"fa'afafine",'Q17148251':'travesti','Q19798648':'unknown value','Q207959':'androgyny','Q215627':'person','Q2449503':'transgender male','Q27679684':'transfeminine','Q27679766':'transmasculine','Q301702':'two-Spirit','Q303479':'hermaphrodite','Q3177577':'muxe','Q3277905':'māhū','Q430117':'Transgene','Q43445':'female non-human organism'}
lang_groups.insert(3, 'All languages')

# articles gender
query = 'SELECT set1, set2descriptor, abs_value, rel_value FROM wdo_intersections_accumulated WHERE content = "articles" AND set1descriptor = "wp" AND set2descriptor IN ("male","female") AND set2 = "wikidata_article_qitems" AND period = "'+last_period+'" ORDER BY set1, rel_value DESC;'
df_gender_articles = pd.read_sql_query(query, conn)
df_gender_articles = df_gender_articles.rename(columns={'set1':'Wiki', 'set2descriptor':'Gender', 'abs_value':'Articles', 'rel_value':'Extent Articles (%)'})
df_gender_articles = df_gender_articles.fillna(0).round(1)

df_gender_articles['Language'] = df_gender_articles['Wiki'].map(language_names_full)
df_gender_articles['Language (Wiki)'] = df_gender_articles['Language']+' ('+df_gender_articles['Wiki']+')'
df_gender_articles['Extent Articles WP (%)'] = df_gender_articles['Extent Articles (%)']


df_gender_articles_male = df_gender_articles.loc[df_gender_articles['Gender'] == 'male']
df_gender_articles_male = df_gender_articles_male.set_index('Wiki')
df_gender_articles_female = df_gender_articles.loc[df_gender_articles['Gender'] == 'female']
df_gender_articles_female = df_gender_articles_female.set_index('Wiki')

for x in df_gender_articles_male.index.values.tolist():
    try:
        male = df_gender_articles_male.loc[x]['Articles']
    except:
        male = 0  
    try:
        female = df_gender_articles_female.loc[x]['Articles']
    except:
        female = 0
    df_gender_articles_male.at[x, 'Extent Articles (%)'] =  100*male/(male+female)
    df_gender_articles_female.at[x, 'Extent Articles (%)'] =  100*female/(male+female)

df_gender_articles_male = df_gender_articles_male.reset_index().round(1)
df_gender_articles_female = df_gender_articles_female.reset_index().round(1)


# -------------------------- # -------------------------- # -------------------------- # --------------------------


# DATA FOR DOTPLOTS (la idea és punts per CCC i per WP d'homes i dones)



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

schools = ["Brown", "NYU", "Notre Dame", "Cornell", "Tufts", "Yale",
           "Dartmouth", "Chicago", "Columbia", "Duke", "Georgetown",
           "Princeton", "U.Penn", "Stanford", "MIT", "Harvard"]
n_schools = len(schools)

men_salary = [72, 67, 73, 80, 76, 79, 84, 78, 86, 93, 94, 90, 92, 96, 94, 112]
women_salary = [92, 94, 100, 107, 112, 114, 114, 118, 119, 124, 131, 137, 141, 151, 152, 165]

df = pd.DataFrame(dict(school=schools*2, salary=men_salary + women_salary,
                       gender=["Men"]*n_schools + ["Women"]*n_schools))
































### DASH APP ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 
# dash_app12 = Dash(__name__, server = app, url_base_pathname= webtype + '/gender_gap/', external_stylesheets=external_stylesheets, external_scripts=external_scripts)
dash_app12 = Dash()


dash_app12.config['suppress_callback_exceptions']=True

title = "Gender Gap"
dash_app12.title = title+title_addenda

dash_app12.layout = html.Div([
    navbar,
    html.H3(title, style={'textAlign':'center'}),
    dcc.Markdown('''
        This page shows stastistics and graphs that illustrate the gender gap in Wikipedia language editions content. For a detailed analysis on the evolution of gender gap over time or the pageviews women articles receive, you can check [Diversity Over Time](http://wcdo.wmflabs.org/diversity_over_time) and [Last Month Pageviews](https://wcdo.wmflabs.org/last_month_pageviews/).
        '''),

    # html.H5('Gender Gap in Wikipedia Language Editions'),

    dcc.Markdown('''* **What is the gender gap in specific groups of Wikipedia language editions?**'''.replace('  ', '')),


    html.Div(
    html.P('Select a group of Wikipedias'),
    style={'display': 'inline-block','width': '200px'}),

    html.Br(),

    html.Div(
    dcc.Dropdown(
        id='grouplangdropdown',
        options=[{'label': k, 'value': k} for k in lang_groups],
        value='Top 10',
        style={'width': '190px'}
     ), style={'display': 'inline-block','width': '200px'}),

    html.Br(),
    html.Div(
    html.P('You can add or remove languages:'),
    style={'display': 'inline-block','width': '500px'}),

    dcc.Dropdown(id='sourcelangdropdown_gender_gap',
        options = [{'label': k, 'value': k} for k in language_names_list],
        multi=True),


    dcc.Graph(id = 'language_gendergap_barchart'),


    # dcc.Graph(id = 'dotplot'),
    


    footbar,

], className="container")


### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

#### CALLBACKS ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 


# GENDER GAP Dropdown languages
@dash_app12.callback(
    dash.dependencies.Output('sourcelangdropdown_gender_gap', 'value'),
    [dash.dependencies.Input('grouplangdropdown', 'value')])
def set_langs_options_spread(selected_group):
    langolist, langlistnames = wikilanguages_utils.get_langs_group(selected_group, None, None, None, wikipedialanguage_numberarticles, territories, languages)
    available_options = [{'label': i, 'value': i} for i in langlistnames.keys()]
    list_options = []
    for item in available_options:
        list_options.append(item['label'])
    re = sorted(list_options,reverse=False)

    return re

#    return ['Cebuano (ceb)', 'Dutch (nl)', 'English (en)', 'French (fr)', 'German (de)', 'Italian (it)', 'Polish (pl)', 'Russian (ru)', 'Spanish (es)', 'Swedish (sv)']


# GENDER GAP BARCHART
@dash_app12.callback(
    Output('language_gendergap_barchart', 'figure'),
    [Input('sourcelangdropdown_gender_gap', 'value')])
def update_barchart(langs):

    languagecodes = []
    for l in langs:
        try:
            languagecodes.append(language_names[l])
        except:
            pass

    df = df_gender_articles_male.loc[df_gender_articles_male['Wiki'].isin(languagecodes)].set_index('Wiki').sort_values(by ='Extent Articles (%)', ascending=False)
    df2 = df_gender_articles_female.loc[df_gender_articles_female['Wiki'].isin(languagecodes)].set_index('Wiki').sort_values(by ='Extent Articles (%)', ascending=True)

    height = len(df2)*25
    if len(languagecodes)==10: height = 500

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df['Language'],
        x=df['Extent Articles (%)'],
        name='Men Articles',
        marker_color='blue',
#        values = df2['Extent Articles (%)'],
        customdata = df['Articles'],
        texttemplate='%{y}',
        orientation='h',
        hovertemplate='<br>Articles: %{customdata}<br>Extent Articles: %{x}%<br><extra></extra>',

    ))
    fig.add_trace(go.Bar(
        y=df2['Language'],
        x=df2['Extent Articles (%)'],
        name='Women Articles',
        marker_color='red',
#        values = df2['Extent Articles (%)'],
        customdata = df2['Articles'],
        texttemplate='%{y}',
        orientation='h',
        hovertemplate='<br>Articles: %{customdata}<br>Extent Articles: %{x}%<br><extra></extra>',
    ))

    fig.update_layout(
#        autosize=True,
        title_font_size=12,
        height = height,
        titlefont_size=12,
        width=700,
        barmode='stack')



    return fig




# DOTPLOTS (la idea és punts per CCC i per WP d'homes i dones)
@dash_app.callback(
    Output('dotplot', 'figure'),
    [Input('source_lang', 'value')])
def update_dotplot(value):
    source_lang = value

    # Això serviria per ensenyar que els d'homes i dones estan desenvolupats diferent (bytes, etc.) a cada llengua.

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[72, 67, 73, 80, 76, 79, 84, 78, 86, 93, 94, 90, 92, 96, 94, 112],
        y=schools,
        marker=dict(color="crimson", size=12),
        mode="markers",
        name="Women",
    ))

    fig.add_trace(go.Scatter(
        x=[92, 94, 100, 107, 112, 114, 114, 118, 119, 124, 131, 137, 141, 151, 152, 165],
        y=schools,
        marker=dict(color="gold", size=12),
        mode="markers",
        name="Men",
    ))

    fig.update_layout(title="Gender Earnings Disparity",
                      xaxis_title="Annual Salary (in thousands)",
                      yaxis_title="School")


    return fig




"""


# TO COPY PASTE ######## ######## ######## ######## ######## ######## ######## ######## ########
@dash_app12.callback(
    [Output('sourcelangdropdown_gender_gap', 'disabled'), Output('grouplangdropdown', 'disabled'), Output('grouplangdropdown','value')],
    [Input('specific_group_radio','value')])
def set_radio_languages(radio_value):

    if radio_value == "all":
        return True, True, []
    else:
        return False, False, "Top 10"

@dash_app12.callback(
    dash.dependencies.Output('sourcelangdropdown_gender_gap', 'value'),
    [dash.dependencies.Input('grouplangdropdown', 'value'), Input('specific_group_radio','value')])
def set_langs_options_geography(selected_group, radio_value):
    langolist, langlistnames = wikilanguages_utils.get_langs_group(selected_group, None, None, None, wikipedialanguage_numberarticles, territories, languages)
    available_options = [{'label': i, 'value': i} for i in langlistnames.keys()]
    list_options = []
    for item in available_options:
        list_options.append(item['label'])
    re = sorted(list_options,reverse=False)

    if radio_value == "all":
        re = []

    return re


@dash_app12.callback(Output('gender_extent_barchart', 'figure'),
    [Input('sourceentityspecific', 'value'), Input('sourcelangdropdown_gender_gap', 'value')])
def update_barchart(entityspecific, languages):

    print (entityspecific, entitytype, languages)

    s = 20
    langs = []

    if type(languages) == list and len(languages) != 0:
        for x in languages: 
            langs.append(language_names[x])
        s = len(langs)

    elif type(languages) == str:
        langs.append(language_names[languages])

    else:
        langs = wikilanguagecodes


    if entitytype == 'Countries':
        df = df_lang_countries_final.loc[(df_lang_countries_final['Wiki'].isin(langs)) & (df_lang_countries_final['Country'] == entityspecific)]
        df = df.head(s)
        fig = px.bar(df, x='Language', y='Coverage (%)', hover_data=['Language','Articles','Total Articles','Coverage (%)','Extent (%)','ISO 3166','Country','Subregion','Region'], color='Articles', height=400)

    if entitytype == 'Subregions':
        df = df_lang_subregion_final.loc[(df_lang_subregion_final['Wiki'].isin(langs)) & (df_lang_subregion_final['Subregion'] == entityspecific)]
        df = df.head(s)
        fig = px.bar(df, x='Language', y='Coverage (%)', hover_data=['Language','Articles','Total Articles','Coverage (%)','Extent (%)','Subregion','Region'], color='Articles', height=400)

    if entitytype == 'Regions':
        df = df_lang_region_final.loc[(df_lang_region_final['Wiki'].isin(langs)) & (df_lang_region_final['Region'] == entityspecific)]
        df = df.head(s)
        fig = px.bar(df, x='Language', y='Coverage (%)', hover_data=['Language','Articles','Total Articles','Coverage (%)','Extent (%)','Region'], color='Articles', height=400)

    return fig


"""


### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

if __name__ == '__main__':
    dash_app12.run_server(debug=True)
