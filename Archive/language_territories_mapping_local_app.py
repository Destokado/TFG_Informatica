import sys
sys.path.insert(0, '/srv/wcdo/src_viz')
from dash_apps import *

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
import random
import json

# script
import wikilanguages_utils


def save_dict_to_file(dic):
    f = open('dict.txt','w')
    f.write(str(dic))
    f.close()

def load_dict_from_file():
    f = open('dict.txt','r')
    data=f.read()
    f.close()
    return eval(data)

##### RESOURCES GENERAL #####
title_addenda = ' - Wikipedia Cultural Diversity Observatory (WCDO)'

databases_path = 'databases/'
territories = wikilanguages_utils.load_wikipedia_languages_territories_mapping()
languages = wikilanguages_utils.load_wiki_projects_information();

wikilanguagecodes = languages.index.tolist()

### for the table
languageswithoutterritory=['eo','got','ia','ie','io','jbo','lfn','nov','vo']
# Only those with a geographical context
for languagecode in languageswithoutterritory: wikilanguagecodes.remove(languagecode)
country_names, regions, subregions = wikilanguages_utils.load_iso_3166_to_geographical_regions()

subregions_regions = {}
for x,y in subregions.items():
    subregions_regions[y]=regions[x]

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
language_names_inv = {v: k for k, v in language_names.items()}


#wikipedialanguage_numberarticles = wikilanguages_utils.load_wikipedia_language_editions_numberofarticles(wikilanguagecodes,'')
#print (wikipedialanguage_numberarticles)
#save_dict_to_file(wikipedialanguage_numberarticles)
wikipedialanguage_numberarticles = load_dict_from_file()
for languagecode in wikilanguagecodes:
   if languagecode not in wikipedialanguage_numberarticles: wikilanguagecodes.remove(languagecode)





def get_langs_group(topX, region, subregion):

    if topX != None:
        i = 0
        for w in sorted(wikipedialanguage_numberarticles, key=wikipedialanguage_numberarticles.get, reverse=True):
            i+=1
            if i==TopX: return langs
            langs.append(w)

    if region != None:
        return list(set(territories.loc[territories['region']==region].index.tolist()))

    if subregion != None:
        return list(set(territories.loc[territories['subregion']==subregion].index.tolist()))





#### DATA ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 

# TAB / TOPIC 1. wikipedia language editions and geography


# Quantes llengües hi ha per continent?
# SELECT region, count(distinct WikimediaLanguagecode) FROM wikipedia_languages_territories_mapping GROUP BY 1 ORDER BY 2 DESC;

# SELECT sub_region, count(distinct WikimediaLanguagecode) FROM wikipedia_languages_territories_mapping GROUP BY 1 ORDER BY 2 DESC;


# * When were the Wikipedia language editions related to each continent created?

# * Which Wikipedia language edition is related to a language that is spoken in more countries?
query = 'SELECT WikimediaLanguagecode, count(distinct country) FROM wikipedia_languages_territories_mapping GROUP BY 1 ORDER BY 2 DESC'

# * How many languages are spoken in each country, subregion and world region?
# Languages by Country, World Region and Subregion and Average Status
query = 'SELECT region, count(distinct WikimediaLanguagecode) FROM wikipedia_languages_territories_mapping GROUP BY 1 ORDER BY 2 DESC'

query = 'SELECT sub_region, count(distinct WikimediaLanguagecode) FROM wikipedia_languages_territories_mapping GROUP BY 1 ORDER BY 2 DESC'

query = 'SELECT ISO3166, count(distinct WikimediaLanguagecode) FROM wikipedia_languages_territories_mapping GROUP BY 1 ORDER BY 2 DESC'


# Quins són els països que aporten més llengües a Viquipèdia?
query = 'SELECT country, count(distinct WikimediaLanguagecode) FROM wikipedia_languages_territories_mapping GROUP BY 1 ORDER BY 2 DESC'



# * Where are the languages of the Wikipedia language editions spoken officially or native?
# Language-Territories (Countries and subdivisions)
conn = sqlite3.connect(databases_path+'diversity_categories.db'); cursor = conn.cursor();  
query = 'SELECT WikimediaLanguagecode, languagenameEnglishethnologue, territoryname, territorynameNative, QitemTerritory, demonym, demonymNative, ISO3166, ISO31662, regional, country, indigenous, languagestatuscountry, officialnationalorregional, region, subregion, intermediateregion FROM wikipedia_languages_territories_mapping;'

df_langterritories = pd.read_sql_query(query, conn)
#df_langterritories = df_langterritories[['territoryname','territorynameNative','QitemTerritory','WikimediaLanguagecode','demonym','demonymNative','ISO3166','ISO31662']]

df_langterritories.WikimediaLanguagecode = df_langterritories['WikimediaLanguagecode'].str.replace('-','_')
df_langterritories.WikimediaLanguagecode = df_langterritories['WikimediaLanguagecode'].str.replace('be_tarask', 'be_x_old')
df_langterritories.WikimediaLanguagecode = df_langterritories['WikimediaLanguagecode'].str.replace('nan', 'zh_min_nan')
df_langterritories = df_langterritories.set_index('WikimediaLanguagecode')
df_langterritories['Language Name'] = pd.Series(languages[['languagename']].to_dict('dict')['languagename'])
df_langterritories = df_langterritories.reset_index()
columns_dict = {'Language Name':'Language','WikimediaLanguagecode':'Wiki','QitemTerritory':'WD Qitem','territoryname':'Territory','territorynameNative':'Territory (Local)','demonymNative':'Demonyms (Local)','ISO3166':'ISO 3166', 'ISO31662':'ISO 3166-2','country':'Country','region':'Region','subregion':'Subregion'}
df_langterritories=df_langterritories.rename(columns=columns_dict)



# * Which are the Wikipedia language editions of Artificial languages?
query = 'SELECT languagename, wiki_projects.Qitem, Wikipedia, nativeLabel FROM wikipedia_languages_territories_mapping INNER JOIN wiki_projects on wikipedia_languages_territories_mapping.WikimediaLanguagecode=wiki_projects.WikimediaLanguagecode where territoryname is null;'







# GRÀFIC: treemap.
# mida. nombre d’speakers. nombre de countries. nombre d'articles.
# colors. continents. subregions. països. any de creació.

# GRÀFIC: cloropeth map (pel tema de comptar llengües per països)

# GRÀFIC: 3D bubble chart (pel tema de llengües per any…). Scatterplot 2D i 3D. Poder escollir el nombre de dimensions i els eixos.

# TAULA




#----------------


# TAB / TOPIC 2. wikipedia languages editions of languages with a marginalized status or indigenous

# * Which of the 300 Wikipedia language editions are from a language with a marginalization status (its presence is threatened in environments such as education, business or any public spaces)?

# * Which languages with Wikipedia language editions coexist in the same territory with more languages with Wikipedia language editions?
# Wikipedias of Dominant Languages # Quines són les llengües més solapadores?
query = 'SELECT languagename, wikimedia_higher, count(distinct wikimedia_lower) FROM wikipedia_language_pairs_territory_status LEFT JOIN wiki_projects ON wikipedia_language_pairs_territory_status.wikimedia_higher=wiki_projects.WikimediaLanguagecode WHERE equal_status = 0 GROUP by 1 ORDER BY 3 DESC'

# * Which Wikipedia language editions are native and not native in which territories?
# Languages present in more countries but not as a native language
query = 'SELECT WikimediaLanguagecode, count(distinct country) FROM wikipedia_languages_territories_mapping WHERE indigenous = "no" GROUP BY 1 ORDER BY 2 DESC'


# * Which are the Wikipedias language editions of the languages in a minoritization situation?
# Wikipedias of Minoritized Languages

"""
Quines són les llengües minoritzades?
Buscar el nombre de territoris on la llengua és indígena.
Després buscar les llengües que en aquest territori tenen un status superior.
num_higher_status_langs
"""




# Languages with lowest status # Quines són les llengües més solapades?
query = 'SELECT languagename, wikimedia_lower, count(distinct wikimedia_higher) FROM wikipedia_language_pairs_territory_status inner join wiki_projects on wikipedia_language_pairs_territory_status.wikimedia_lower=wiki_projects.WikimediaLanguagecode where equal_status = 0 GROUP BY 1 ORDER BY 3 DESC'

query = 'SELECT languagename, wiki_projects.WikimediaLanguagecode, MIN(languagestatuscountry), wikipedia_languages_territories_mapping.subregion, wikipedia_languages_territories_mapping.region FROM wikipedia_languages_territories_mapping left join wiki_projects on wiki_projects.WikimediaLanguagecode = wikipedia_languages_territories_mapping.WikimediaLanguagecode GROUP BY 1 ORDER BY 3;'

# * Which are the Wikipedia language editions of indigenous languages?
# Native languages but without an official status and minoritized by other languages (Indigenous langs)

# Quines són les llengües natives però que no tenen status oficial i estan solapades per d’altres llengües de més estatus?
query = 'SELECT languagename, wikimedia_lower, status_lower, wikimedia_higher FROM wikipedia_language_pairs_territory_status INNER JOIN wiki_projects on wikipedia_language_pairs_territory_status.wikimedia_lower=wiki_projects.WikimediaLanguagecode where equal_status = 0 and indigenous_lower = “yes” GROUP BY 1 ORDER BY 3 DESC'

# Indigenous languages
# Quines són les llengües indígenes?
# identificar els idiomes indígenes com aquells que estan solapats per un idioma 
# https://meta.wikimedia.org/wiki/Wikimedia_Indigenous_Languages
# For the purpose of this project, an "indigenous language" is a language that is native, or aboriginal to a region and spoken by indigenous people, but has been reduced to the status of a minority language
# Hauríem de posar més columnes a la taula: wiki_projects.
# Quines són les llengües minoritzades?
# Buscar el nombre de territoris on la llengua és indígena.
# Després buscar les llengües que en aquest territori tenen un status superior.
# num_higher_status_langs


# * What territories (countries and their subdivisions) are not covered by a language that is indigenous in that territory?


# GRÀFIC: treemap.

# GRÀFIC: cloropeth map (pel tema de comptar països)



#----------------

# TAB / TOPIC 3. world languages... that can become a wikipedia
# * In which countries are there more languages spoken without a Wikipedia language edition?

query = ''


# * Is there any territory (country or subdivision) in which none of the languages spoken there has a Wikipedia language edition?


query = ''

# * Which languages without a Wikipedia language edition have more speakers or a better legal status and are more likely create one?


query = ''

# * How many of the world languages have an article in this language edition? (World Languages Lists) -> cal agafar la taula all_languages_wikidata i passar-la com a paràmetre a una consulta a wikipedia_diversity.db per la taula de la llengua target. fer un left join i veure quines falten. permetre filtrar.



# GRÀFIC: scatterplot (pel tema de llengües amb possibilitats de convertir-se en viquipèdia)

# GRÀFIC: treemap.

# GRÀFIC: cloropeth map (pel tema de comptar països)

# TAULA


#----------------






















conn = sqlite3.connect(databases_path + 'stats.db'); cursor = conn.cursor() 
conn2 = sqlite3.connect(databases_path + 'wikipedia_diversity.db'); cursor2 = conn2.cursor() 
conn3 = sqlite3.connect(databases_path+'diversity_categories.db'); cursor3 = conn3.cursor();  


query = 'SELECT WikimediaLanguagecode, languagenameEnglishethnologue, territoryname, territorynameNative, QitemTerritory, demonym, demonymNative, ISO3166, ISO31662, regional, country, indigenous, languagestatuscountry, officialnationalorregional, region, subregion, intermediateregion FROM wikipedia_languages_territories_mapping;'


# THE NUMBER OF WIKIPEDIA LANGUAGES PER REGION
query = 'SELECT country as COUNTRY, alpha_3 as CODE, count(DISTINCT WikimediaLanguagecode) as languages FROM wikipedia_languages_territories_mapping INNER JOIN country_regions ON ISO3166=alpha_2 GROUP BY 1'


# THE NUMBER OF WIKIPEDIA LANGUAGES PER COUNTRY
query = 'SELECT country as COUNTRY, alpha_3 as CODE, count(DISTINCT WikimediaLanguagecode) as languages FROM wikipedia_languages_territories_mapping INNER JOIN country_regions ON ISO3166=alpha_2 GROUP BY 1'


df = pd.read_sql_query(query, conn3)

print (df.head(100))









#----------------

### DASH APP ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###
# dash_app1 = Dash(__name__, server = app, url_base_pathname= webtype + '/language_territories_mapping/', external_stylesheets=external_stylesheets, external_scripts=external_scripts)

dash_app1 = Dash()
dash_app1.config['suppress_callback_exceptions']=True

title = 'World Languages (Wikipedia Language Editions Gap)'
dash_app1.title = title+title_addenda
dash_app1.layout = html.Div([
    # navbar,
    html.H3(title, style={'textAlign':'center'}),

    dcc.Tabs([

        dcc.Tab(label='Language-Territories Mapping Table', children=[

            dcc.Markdown(
            '''This is a copy of the latest version of the **Language Territories Mapping database** (see wikipedia_language_territories_mapping.csv in [github project page](https://github.com/marcmiquel/WCDO/tree/master/language_territories_mapping)). The first version of this database has been generated using Ethnologue, 
            Wikidata and Wikipedia language pages. Wikimedians are invited to suggest changes by e-mailing [tools.wcdo@tools.wmflabs.org](mailto:tools.wcdo@tools.wmflabs.org).

            The database contains all the territories (political divisions of first and second level) in which a language 
            is spoken because it is indigeneous or official, along with some specific metadata used in the generation of 
            Cultural Context Content (CCC) dataset.

            The following table is a reduced version of the database with the Language name, wikicode, Wikidata Qitem for 
            the territory, territory in native language, demonyms in native language, ISO 3166 and ISO 3166-2, whereas 
            the full database includes the Qitem for the language, language names in Native languages among other information. 
            Additionally, the full table is extended with the database country_regions.csv, which presents an equivalence 
            table between countries, world regions (continents) and subregions (see country_regions.csv in the github).'''.replace('  ', '')),
            dash_table.DataTable(
                id='datatable-languageterritories',
                columns=[
                    {"name": i, "id": i, "deletable": True, "selectable": True} for i in ['Wiki','Language','WD Qitem','Territory','Territory (Local)','ISO 3166','ISO 3166-2','Region','Subregion']
                ],
                data=df_langterritories.to_dict('records'),
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
            ),
        ]),

        dcc.Tab(label='Language-Territories Mapping Table', children=[
            html.Br(),


            dcc.Dropdown(
                id='source_lang',
                options=[{'label': i, 'value': language_names[i]} for i in sorted(language_names)],
                value='en',
                placeholder="Select a source language",           
                style={'width': '190'}
             ),
            dcc.Graph(
            id = 'treemap',
            style={"height": "800px", "width": "1000px",'display': 'inline-block'}),
           


        ]),



    ]),
    # footbar,

], className="container")

### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###


#### CALLBACKS ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 


# none by now.


@dash_app.callback(
    Output('treemap', 'figure'),
    [Input('source_lang', 'value')])
def update_treemap(value):
    source_lang = value

    # https://analyticsindiamag.com/beginners_guide_geographical_plotting_with_plotly/

    # gapminder = px.data.gapminder().query("year==2007")
    # fig = px.choropleth(gapminder, locations="iso_alpha",
    #                     color="lifeExp", # lifeExp is a column of gapminder
    #                     hover_name="country", # column to add to hover information
    #                     color_continuous_scale=px.colors.sequential.Plasma)


    fig = go.Figure(data=go.Choropleth(
        locations = df['CODE'],
        z = df['languages'],
        text = df['COUNTRY'],
        colorscale = 'Blues',
        autocolorscale=False,
        reversescale=False,
        marker_line_color='darkgray',
        marker_line_width=0.5,
        colorbar_tickprefix = '',
        colorbar_title = 'Number of languages',
    ))

    # fig.update_layout(
    #     title_text='2014 Global GDP',
    #     geo=dict(
    #         showframe=False,
    #         showcoastlines=False,
    #         projection_type='equirectangular'
    #     ),
    #     annotations = [dict(
    #         x=0.55,
    #         y=0.1,
    #         xref='paper',
    #         yref='paper',
    #         text='Source: <a href="https://www.cia.gov/library/publications/the-world-factbook/fields/2195.html">\
    #             CIA World Factbook</a>',
    #         showarrow = False
    #     )]
    # )

    return fig







# ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

if __name__ == '__main__':
    dash_app1.run_server(debug=True)
