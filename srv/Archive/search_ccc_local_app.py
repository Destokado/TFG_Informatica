# -*- coding: utf-8 -*-

# flash dash
import flask
from flask import Flask, request, render_template
from flask import send_from_directory
from dash import Dash
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_table_experiments as dt
from dash.dependencies import Input, Output, State
# viz
import plotly
import chart_studio.plotly as py
import plotly.figure_factory as ff
# data
import urllib
from urllib.parse import urlparse, parse_qsl, urlencode
import pandas as pd
import sqlite3
import xlsxwriter
# other
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import datetime
import time

# script
import wikilanguages_utils


import requests



##### METHODS #####
# parse
def parse_state(url):
    parse_result = urlparse(url)
    params = parse_qsl(parse_result.query)
    state = dict(params)
    print (state)
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



def save_dict_to_file(dic):
    f = open('databases/'+'dict.txt','w')
    f.write(str(dic))
    f.close()

def load_dict_from_file():
    f = open('databases/'+'dict.txt','r')
    data=f.read()
    f.close()
    return eval(data)



# DASH APPS #
#########################################################
#########################################################
#########################################################

databases_path = 'databases/'

territories = wikilanguages_utils.load_wikipedia_languages_territories_mapping()
languages = wikilanguages_utils.load_wiki_projects_information();

wikilanguagecodes = languages.index.tolist()

# wikipedialanguage_numberarticles = wikilanguages_utils.load_wikipedia_language_editions_numberofarticles(wikilanguagecodes,'production')
# save_dict_to_file(wikipedialanguage_numberarticles) # using this is faster than querying the database for the number of articles in each table.

wikipedialanguage_numberarticles = load_dict_from_file()
for languagecode in wikilanguagecodes:
   if languagecode not in wikipedialanguage_numberarticles: wikilanguagecodes.remove(languagecode)


language_names = {}
for languagecode in wikilanguagecodes:
    lang_name = languages.loc[languagecode]['languagename']+' ('+languagecode+')'
    language_names[lang_name] = languagecode


closest_langs = wikilanguages_utils.obtain_closest_for_all_languages(wikipedialanguage_numberarticles, wikilanguagecodes, 4)

country_names, regions, subregions = wikilanguages_utils.load_iso_3166_to_geographical_regions()

country_names_inv = {v: k for k, v in country_names.items()}

ISO31662_subdivisions_dict, subdivisions_ISO31662_dict = wikilanguages_utils.load_iso_31662_to_subdivisions()

for i in (set(languages.index.tolist()) - set(list(wikipedialanguage_numberarticles.keys()))):
    try: languages.drop(i, inplace=True); territories.drop(i, inplace=True)
    except: pass
print (wikilanguagecodes)


wikilanguagecodes.remove('szy')
wikilanguagecodes.remove('awa')
wikilanguagecodes.remove('ary')


# # web
title_addenda = ' - Wikipedia Diversity Observatory (WDO)'
external_stylesheets = ['https://wcdo.wmflabs.org/assets/bWLwgP.css']

#########################################################
#########################################################
#########################################################







### DASH APP ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 
#dash_app23 = Dash(__name__, server = app, url_base_pathname = webtype + '/search_ccc_articles/', external_stylesheets=external_stylesheets ,external_scripts=external_scripts)
dash_app23 = Dash(url_base_pathname = '/search_ccc_articles/', external_stylesheets=external_stylesheets)


dash_app23.config['suppress_callback_exceptions']=True

#dash_app23.config.supress_callback_exceptions = True

dash_app23.title = 'Search CCC'+title_addenda
dash_app23.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content') 
])

#dash_app23.config['suppress_callback_exceptions']=True

source_lang_dict = {}
for languagecode in wikilanguagecodes:
    lang_name = languages.loc[languagecode]['languagename']+' ('+languagecode+')'
    source_lang_dict[lang_name] = languagecode

query_lang_dict = {}
for languagecode in wikilanguagecodes:
    lang_name = languages.loc[languagecode]['languagename']+' ('+languagecode+')'
    query_lang_dict[lang_name] = languagecode

target_langs_dict = {} 
for languagecode in wikilanguagecodes:
    lang_name = languages.loc[languagecode]['languagename']+' ('+languagecode+')'
    target_langs_dict[lang_name] = languagecode


features_dict = {'Editors':'num_editors','Edits':'num_edits','Pageviews':'num_pageviews','Inlinks':'num_inlinks','References':'num_references','Bytes':'num_bytes','Outlinks':'num_outlinks','Interwiki':'num_interwiki','WDProperties':'num_wdproperty','Discussions':'num_discussions','Inlinks from CCC':'num_inlinks_from_CCC','Outlinks to CCC':'num_outlinks_to_CCC'}

features_dict_inv = {'num_editors':'Editors', 'num_edits':'Edits', 'num_images':'Images', 'wikirank':'Wikirank', 'num_pageviews':'Pageviews', 'num_inlinks':'Inlinks', 'num_references':'References','num_bytes':'Bytes','num_outlinks':'Outlinks','num_interwiki':'Interwiki','num_wdproperty':'Wikidata Properties','num_discussions':'Discussions','date_created':'Creation Date','num_inlinks_from_CCC':'Inlinks from CCC','num_outlinks_to_CCC':'Outlinks to CCC','featured_article':'Featured Article'}

# ['apage_title', 'bpage_title', 'qitem', 'num_inlinks', 'num_outlinks','num_inlinks_from_CCC', 'num_outlinks_to_CCC', 'num_bytes','num_references', 'num_images', 'num_edits', 'num_editors','num_discussions', 'num_pageviews', 'featured_article']

ccc_all_dict = {'CCC':'ccc','Geolocated':'ccc_geolocated','Men':'men','Women':'women'}

query_type_dict = {'Wikipedia Article Search':'search', 'Wikidata SPARQL Query':'sparql', 'List of articles':'alist', "List of categories' articles":'clist'}


text_default = '''In this page you can search for articles in a Wikipedia language edition and see their availability in other language editions. First, you need to select the *Source Language* where you want to retrieve the content from. Then you can choose the *Type of query*: Wikipedia Article Search, Wikidata SPARQL Query, List of articles, and List of categories articles. 

    * The *Wikipedia Article Search* allows you to introduce a query to the same search engine of Wikipedia has (CirrusSearch) and retrieve some articles. For example, if you introduce the Source Language English and the query "Japanese Cuisine", you will obtain the articles from English Wikipedia along with their main stats on relevance features (number of editors, edits, discussion edits, pageviews, etc.). When using the search option, you can introduce the *Language of the query* and specify which language you are using to query (e.g. Japanese cuisine could be "cuisine du Japon" in French), no matter it is the same target language or not.
    * The *Wikidata SPARQL Query* allows you to introduce a query in the textbox and retrieve the articles related to the Qitems that appear in them (if the query does not contain any Qitem and only labels, there will be no results).
    * The *List of articles* query simply allows you to introduce a list of articles (their titles or their URLs separated by a comma, semicolon or a line break) in the textbox in order to see the main stats and their availability in the *Target Languages*. 
    * The *List of categories' articles* allows you to introduce a list of categories and retrieve the articles contained in them. 

    All the queries return a table with the articles in the source language and its main stats and its availability in the *Target Languages*. The table will also show the title of the article in the first target language as long as it is available. For this it is recommended that the first target language is English and the second target language is the one you are currently working on (probably your home-wiki). You can also filter the results with the parameter *Topic* which allows you to show only articles from certain topics (CCC, Geolocated, Men and Women). The parameter *Order by feature* sorts the results by a specific feature, and the parameter *Limit the results* limits the search results to a specific number.

    This tool is in Alpha version - you may find bugs. In this case, please e-mail us at tools.wcdo@tools.wmflabs.org.
'''

text_results = '''
The following table shows the results from the query. The columns present the title in the source language, a set of features (number of inlinks, number of inlinks from the source language CCC, number of Outlinks, number of Bytes, number of References, number of Images, number of Editors, number of Edits, number of Discussions, number of Pageviews, numer of Interwiki links and number of Wikidata properties) from the article in the source language, the title in the first target language (in case it exists), and the languages in which it is available from the target languages.
'''


# ['source_lang','query_lang','query_type','textbox','target_langs','topic','order_by','limit']

def dash_app23_build_layout(params):
    if len(params)!=0 and len(params['target_langs'])!=0 and params['query_type']!='none':
    
        functionstartTime = time.time() 

        if 'source_lang' in params:
            source_lang = params['source_lang']
            if source_lang != 'none': source_language = languages.loc[source_lang]['languagename']
        else:
            source_lang = 'none'

        if 'query_lang' in params:
            query_lang = params['query_lang']
        else:
            query_lang = 'none'

        if 'query_type' in params:
            query_type = params['query_type']
        else:
            query_type = 'none'

        if 'textbox' in params:
            textbox=params['textbox']
        else:
            textbox='textbox'

        target_langs = params['target_langs']
        target_langs = target_langs.split(',')

        if 'topic' in params:
            topic = params['topic']
        else:
            topic = 'none'

        if 'order_by' in params:
            order_by=params['order_by'].lower()
        else:
            order_by='none'

        if 'limit' in params:
            limit = int(params['limit'])
        else:
            limit = 'none'

        
        target_language = languages.loc[target_langs[0]]['languagename']

        columns_dict = {'position':'Nº','apage_title':source_language+' Title', 'bpage_title': target_language+' Title','target_langs':'Target Langs.'}
        columns_dict.update(features_dict_inv)

        conn = sqlite3.connect(databases_path + 'wikipedia_diversity.db'); cur = conn.cursor()



        if query_type == 'sparql':
            # WikIdata SPARQL Query
        #     textbox = '''#Escoles entre San Jose, CA i Sacramento, CA
        # # Schools between San Jose, CA and Sacramento, CA
        # #defaultView:Map
        # SELECT *
        # WHERE
        # { hint:Query hint:optimizer "None" .
        #   wd:Q16553 wdt:P625 ?SJloc .
        #   wd:Q18013 wdt:P625 ?SCloc .
        #   SERVICE wikibase:box {
        #       ?place wdt:P625 ?location .
        #       bd:serviceParam wikibase:cornerWest ?SJloc .
        #       bd:serviceParam wikibase:cornerEast ?SCloc .
        #     }
        #   ?place wdt:P31/wdt:P279* wd:Q3914 .
        # }'''

            qitems = wikidata_sparql_query_to_articles_qitems(textbox)
            df = lang1_page_titles_ids_to_lang2_page_titles_qitems_features(source_lang, target_langs, None, None, qitems, None, topic, conn)

        elif query_type == 'search':
            # Wikipedia Search / Wikidata Query API

            mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(source_lang); mysql_cur_read = mysql_con_read.cursor()

            page_titles = {}

            # textbox_query = 'Cuina de kenya'
            qitems,categories = wikidata_api_query_to_articles_qitems(query_lang, source_lang, textbox, 1000)
            # print (qitems,categories)

            # try:
            #     mysql_con_read = wikilanguages_utils.establish_mysql_connection_read('en'); mysql_cur_read = mysql_con_read.cursor()
            #     print ('trying to use the base categories')
            #     if len(categories)!= 0:
            #         page_titles = categories_to_page_ids_page_titles(categories, mysql_cur_read)
            #     print (page_titles)
            # except:
            #     print ('categories is not working for this language: '+source_language)
            # mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(source_lang); mysql_cur_read = mysql_con_read.cursor()


            # first iteration of categories from start
            # print ('trying to use the first categories')
            # page_ids = qitem_to_page_titles_page_ids(qitems, source_lang, cur)
            # if len(page_ids) != 0:
            #     pages_categories_dict, categories = article_page_ids_titles_to_categories(languagecode, list(page_ids.values()), None, mysql_cur_read)
            # page_titles_2 = categories_to_page_ids_page_titles(categories, mysql_cur_read)
            # page_titles.update(page_titles_2)
            # # print (page_titles_2)
            # print (len(page_titles_2))
            # try:
            #     pass
            # except:
            #     print ('categories is not working for this language: '+source_language)


            # # second iteration of categories from start
            # print ('trying to use the second categories')
            # categories = category_to_categories(categories)
            # page_titles_3 = categories_to_page_ids_page_titles(categories, mysql_cur_read)
            # page_titles.update(page_titles_3)
            # # print (page_titles_3)
            # print (len(page_titles_3))
            # try:
            #     pass
            # except:
            #     print ('categories is not working for this language: '+source_language)
            # if len(page_titles)==0: print ('no articles.')
            # page_titles = list(page_titles.values())

            df = lang1_page_titles_ids_to_lang2_page_titles_qitems_features(source_lang, target_langs, None, None, qitems, None, topic, conn)


        elif query_type == 'alist':
            # Text / List of Articles
            mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(source_lang); mysql_cur_read = mysql_con_read.cursor()
            # textbox_query = "Igualada;Vilanova del Camí; Vallbona d'Anoia; Manresa; òdena; Sant Cugat del Vallès;Barcelona; Mataró"
            page_dict_page_ids_page_titles = text_to_pageids_page_titles(source_lang, textbox.lower(), mysql_cur_read)
            page_ids = list(page_dict_page_ids_page_titles.keys())
            df = lang1_page_titles_ids_to_lang2_page_titles_qitems_features(source_lang, target_langs, page_ids, None, None, None, topic, conn)

        elif query_type == 'clist':
            # Category or Categories
            mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(source_lang); mysql_cur_read = mysql_con_read.cursor()
            # textbox_query = "https://ca.wikipedia.org/wiki/Categoria:Igualada\nhttps://ca.wikipedia.org/wiki/Categoria:Cultura_d'Igualada;Vilanova_del_Camí;\nhttps://ca.wikipedia.org/wiki/Categoria:Novel·les_en_valencià"

            categories = text_to_categories(source_lang, textbox.lower())
            page_dict_page_ids_page_titles = categories_to_page_ids_page_titles(categories,mysql_cur_read)
            page_ids = list(page_dict_page_ids_page_titles.keys())

            df = lang1_page_titles_ids_to_lang2_page_titles_qitems_features(source_lang, target_langs, page_ids, None, None, None, topic, conn)



        df['target_langs'] = ''

        df['position'] = ''

        print (len(df))

        # PAGE CASE 2: PARAMETERS WERE INTRODUCED AND THERE ARE NO RESULTS
        if len(df) == 0:
            layout = html.Div([
                
                html.H3('Search CCC Articles', style={'textAlign':'center'}),

                html.Br(),

                dcc.Markdown(
                    text_default.replace('  ', '')),

                html.Br(),
                html.H5('Select the source'),

                html.Div(
                html.P('Source Wikipedia'),
                style={'display': 'inline-block','width': '200px'}),

                html.Div(
                html.P('Type of query'),
                style={'display': 'inline-block','width': '200px'}),

                html.Div(
                html.P('Language of the query'),
                style={'display': 'inline-block','width': '200px'}),


                html.Br(),
                html.Div(
                apply_default_value(params)(dcc.Dropdown)(
                    id='source_lang',
                    options=[{'label': i, 'value': source_lang_dict[i]} for i in sorted(source_lang_dict)],
                    value='none',
                    placeholder="Select a source language",
                    style={'width': '190px'}
                 ), style={'display': 'inline-block','width': '200px'}),
        #        dcc.Link('Query',href=""),

                html.Div(
                apply_default_value(params)(dcc.Dropdown)(
                    id='query_type',
                    options=[{'label': i, 'value': query_type_dict[i]} for i in query_type_dict],
                    value='none',
                    placeholder="Select the type of query",           
                    style={'width': '190px'}
                 ), style={'display': 'inline-block','width': '200px'}),

                html.Div(
                apply_default_value(params)(dcc.Dropdown)(
                    id='query_lang',
                    options=[{'label': i, 'value': query_lang_dict[i]} for i in sorted(query_lang_dict)],
                    value='none',
                    placeholder="Select a query language (optional)",           
                    style={'width': '190px'}
                 ), style={'display': 'inline-block','width': '200px'}),


                html.Br(),

                html.H5('Query or Input Data'),
                html.Div(
                apply_default_value(params)(dcc.Textarea)(
                    id='textbox',
                    placeholder='You can introduce your search query or input data to obtain the results.',
                    value='',
                    style={'width': '100%', 'height':'100'}
                 ), style={'display': 'inline-block','width': '590px'}),
        #        dcc.Link('Query',href=""),

                html.Br(),

                html.H5('Target Wikipedias'),

                html.Div(
                apply_default_value(params)(dcc.Dropdown)(
                    id='target_langs',
                    options=[{'label': i, 'value': target_langs_dict[i]} for i in sorted(target_langs_dict)],
                    value=[],
                    multi=True,
                    placeholder="Select languages",           
                    style={'width': '590px'}
                 ), style={'display': 'inline-block','width': '590px'}),


                html.H5('Filter by content'),

                html.Div(
                html.P('Topic'),
                style={'display': 'inline-block','width': '200px'}),

                html.Div(
                html.P('Order by feature'),
                style={'display': 'inline-block','width': '200px'}),

                html.Div(
                html.P('Limit the results'),
                style={'display': 'inline-block','width': '200px'}),

                html.Br(),
                html.Div(
                apply_default_value(params)(dcc.Dropdown)(
                    id='topic',
                    options=[{'label': i, 'value': ccc_all_dict[i]} for i in sorted(ccc_all_dict, reverse=False)],
                    value='',
                    placeholder="Set topic (optional)",
                    style={'width': '190px'}
                 ), style={'display': 'inline-block','width': '200px'}),

                html.Div(
                apply_default_value(params)(dcc.Dropdown)(
                    id='order_by',
                    options=[{'label': i, 'value': features_dict[i]} for i in sorted(features_dict)],
                    value='none',
                    placeholder="Order by (optional)",           
                    style={'width': '190px'}
                 ), style={'display': 'inline-block','width': '200px'}),

                html.Div(
                apply_default_value(params)(dcc.Input)(
                    id='limit',                    
                    placeholder='Enter a value...',
                    type='text',
                    value='100',
                    style={'width': '190px'}
                 ), style={'display': 'inline-block','width': '200px'}),

                html.A(html.Button('Query Results!'),
                    href=''),


                html.Br(),
                html.Br(),

                html.Hr(),
                html.H5('Results'),
                dcc.Markdown(text_results.replace('  ', '')),
                html.Br(),

                html.H5('There are not results. Unfortunately there are not articles proposed for the local content for this language. Try another combination of parameters and query again.'),


                

            ], className="container")

            return layout

        # print (df.columns)

#        print(str(datetime.timedelta(seconds=time.time() - functionstartTime))+' after queries.')

        # # PREPARE THE DATA
        df=df.rename(columns=columns_dict)

        order_by = order_by.lower()
        if order_by != 'none':
            order = features_dict_inv[order_by]
        else:
            order = features_dict_inv['num_pageviews']
        df = df.sort_values(order,ascending=False)

        # print (df.head(100))
        # input('')

        columns = []
        for x in list(df.columns):
            if x in columns_dict.values():
                columns.append(x)

        columns = columns[-1:] + columns[:-1] 
#        print (columns_dict)

        df_list = list()
        # print (columns)
        # print (len(columns))
        # print (df.head(100))
#        print (len(df))

        k = 0
        for index, rows in df.iterrows():
            df_row = list()

            for col in columns:
                title = rows[source_language+' Title']
                if not isinstance(title, str):
                    title = title.iloc[0]

                if col == 'Nº':
                    k+=1
                    df_row.append(str(k))

                elif col == source_language+' Title':
                    title = rows[source_language+' Title']
                    if not isinstance(title, str):
                        title = title.iloc[0]
                    df_row.append(html.A(title.replace('_',' '), href='https://'+source_lang+'.wikipedia.org/wiki/'+title.replace(' ','_'), target="_blank", style={'text-decoration':'none'}))

                elif col == target_language+' Title':

                    t_title = rows[target_language+' Title']

                    if isinstance(t_title, int): 
                        df_row.append('')

                    elif not isinstance(t_title, str):
                        t_title = t_title.iloc[0]

                    if isinstance(t_title, str):  
                        df_row.append(html.A(t_title.replace('_',' '), href='https://'+target_langs[0]+'.wikipedia.org/wiki/'+t_title.replace(' ','_'), target="_blank", style={'text-decoration':'none'}))


                elif col == 'Interwiki':
                    # print (rows['Qitem'])
                    # print (rows['Interwiki'])
                    # print (rows)
                    df_row.append(html.A( rows['Interwiki'], href='https://www.wikidata.org/wiki/'+rows['qitem'], target="_blank", style={'text-decoration':'none'}))

                elif col == 'Bytes':
                    value = round(float(int(rows[col])/1000),1)
                    df_row.append(str(value)+'k')

                elif col == 'Outlinks' or col == 'References' or col == 'Images':
                    title = rows[source_language+' Title']
                    df_row.append(html.A( rows[col], href='https://'+target_langs[0]+'.wikipedia.org/wiki/'+title.replace(' ','_'), target="_blank", style={'text-decoration':'none'}))

                elif col == 'Inlinks':
                    df_row.append(html.A( rows['Inlinks'], href='https://'+source_lang+'.wikipedia.org/wiki/Special:WhatLinksHere/'+rows[source_language+' Title'].replace(' ','_'), target="_blank", style={'text-decoration':'none'}))

                elif col == 'Inlinks from CCC':
                    df_row.append(html.A( rows['Inlinks from CCC'], href='https://'+source_lang+'.wikipedia.org/wiki/Special:WhatLinksHere/'+rows[source_language+' Title'].replace(' ','_'), target="_blank", style={'text-decoration':'none'}))

                elif col == 'Outlinks from CCC':
                    df_row.append(html.A( rows['Outlinks from CCC'], href='https://'+source_lang+'.wikipedia.org/wiki/'+rows[source_language+' Title'].replace(' ','_'), target="_blank", style={'text-decoration':'none'}))

                elif col == 'Editors':
                    df_row.append(html.A( rows['Editors'], href='https://'+source_lang+'.wikipedia.org/w/index.php?title='+rows[source_language+' Title'].replace(' ','_')+'&action=history', target="_blank", style={'text-decoration':'none'}))

                elif col == 'Edits':
                    df_row.append(html.A( rows['Edits'], href='https://'+source_lang+'.wikipedia.org/w/index.php?title='+rows[source_language+' Title'].replace(' ','_')+'&action=history', target="_blank", style={'text-decoration':'none'}))

                elif col == 'Discussions':
                    df_row.append(html.A( rows['Discussions'], href='https://'+source_lang+'.wikipedia.org/wiki/Talk:'+rows[source_language+' Title'].replace(' ','_'), target="_blank", style={'text-decoration':'none'}))

                elif col == 'Wikirank':
                    df_row.append(html.A( rows['Wikirank'], href='https://wikirank.net/'+source_lang+'/'+rows[source_language+' Title'], target="_blank", style={'text-decoration':'none'}))

                elif col == 'Pageviews':
                    df_row.append(html.A( rows['Pageviews'], href='https://tools.wmflabs.org/pageviews/?project='+source_lang+'.wikipedia.org&platform=all-access&agent=user&range=latest-20&pages='+rows[source_language+' Title'].replace(' ','_')+'&action=history', target="_blank", style={'text-decoration':'none'}))

                elif col == 'Wikidata Properties':
                    df_row.append(html.A( rows['Wikidata Properties'], href='https://www.wikidata.org/wiki/'+rows['qitem'], target="_blank", style={'text-decoration':'none'}))

                elif col == 'Discussions':
                    title = rows[source_language+' Title']
                    df_row.append(html.A(str(rows[col]), href='https://'+source_lang+'.wikipedia.org/wiki/'+title.replace(' ','_'), target="_blank", style={'text-decoration':'none'}))

                elif col == 'Target Langs.':
                    target_langs_titles = []
                    tget_pgtitle = rows[target_language+' Title']
                    if isinstance(tget_pgtitle, int):
                        tget_pgtitle = ''
                    elif not isinstance(tget_pgtitle, str):
                        tget_pgtitle = tget_pgtitle.iloc[0]

                    target_langs_titles.append(tget_pgtitle)

                    for i in range(1,len(target_langs)):
                        target_langs_titles.append(rows['c' + str(i) + 'page_title'])
                    text = ''

                    for x in range(0,len(target_langs)):
                        cur_title = target_langs_titles[x]
                        if cur_title!= None and cur_title != '' and cur_title != 0:
                            if text!='': text+=', '

                            text+= '['+target_langs[x]+']'+'('+'http://'+target_langs[x]+'.wikipedia.org/wiki/'+ cur_title.replace(' ','_')+')'
 #                    print (target_langs_titles)
                    df_row.append(dcc.Markdown(text))

                elif col == 'Qitem':
                    df_row.append(html.A( rows['Qitem'], href='https://www.wikidata.org/wiki/'+rows['Qitem'], target="_blank", style={'text-decoration':'none'}))
                else:
                    df_row.append(rows[col])

            # print (rows)
            # print (len(rows))
            # print (len(df_row))
            
            if k <= limit:
                df_list.append(df_row)

#        print(str(datetime.timedelta(seconds=time.time() - functionstartTime))+' after htmls')
#        print (df.head())

        # print (df.columns)
        # print (columns)

        # print (len(df.columns))
        # print (len(columns))

        title = 'Search CCC Articles'
        df1 = pd.DataFrame(df_list)
        dash_app23.title = title+title_addenda

        # LAYOUT
        layout = html.Div([
            
            html.H3(title, style={'textAlign':'center'}),
#            html.Br(),

            dcc.Markdown(
                text_default.replace('  ', '')),

            html.Br(),

            # HERE GOES THE INTERFACE
            html.H5('Select the source'),

            html.Div(
            html.P('Source Wikipedia'),
            style={'display': 'inline-block','width': '200px'}),

            html.Div(
            html.P('Type of query'),
            style={'display': 'inline-block','width': '200px'}),

            html.Div(
            html.P('Language of the query'),
            style={'display': 'inline-block','width': '200px'}),


            html.Br(),
            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='source_lang',
                options=[{'label': i, 'value': source_lang_dict[i]} for i in sorted(source_lang_dict)],
                value='none',
                placeholder="Select a source language",
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),
    #        dcc.Link('Query',href=""),

            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='query_type',
                options=[{'label': i, 'value': query_type_dict[i]} for i in query_type_dict],
                value='none',
                placeholder="Select the type of query",           
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),

            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='query_lang',
                options=[{'label': i, 'value': query_lang_dict[i]} for i in sorted(query_lang_dict)],
                value='none',
                placeholder="Select a query language (optional)",           
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),


            html.Br(),

            html.H5('Query or Input Data'),
            html.Div(
            apply_default_value(params)(dcc.Textarea)(
                id='textbox',
                placeholder='You can introduce your search query or input data to obtain the results.',
                value='',
                style={'width': '100%', 'height':'100'}
             ), style={'display': 'inline-block','width': '590px'}),
    #        dcc.Link('Query',href=""),

            html.Br(),

            html.H5('Target Wikipedias'),

            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='target_langs',
                options=[{'label': i, 'value': target_langs_dict[i]} for i in sorted(target_langs_dict)],
                value=[],
                multi=True,
                placeholder="Select languages",           
                style={'width': '590px'}
             ), style={'display': 'inline-block','width': '590px'}),


            html.H5('Filter by content'),

            html.Div(
            html.P('Topic'),
            style={'display': 'inline-block','width': '200px'}),

            html.Div(
            html.P('Order by feature'),
            style={'display': 'inline-block','width': '200px'}),

            html.Div(
            html.P('Limit the results'),
            style={'display': 'inline-block','width': '200px'}),

            html.Br(),
            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='topic',
                options=[{'label': i, 'value': ccc_all_dict[i]} for i in sorted(ccc_all_dict, reverse=False)],
                value='',
                placeholder="Set topic (optional)",
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),

            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='order_by',
                options=[{'label': i, 'value': features_dict[i]} for i in sorted(features_dict)],
                value='none',
                placeholder="Order by (optional)",           
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),

            html.Div(
            apply_default_value(params)(dcc.Input)(
                id='limit',                    
                placeholder='Enter a value...',
                type='text',
                value='100',
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),

            html.A(html.Button('Query Results!'),
                href=''),

            # here there is the table            
            html.Br(),
            html.Br(),

            html.Hr(),
            html.H5('Results'),
            dcc.Markdown(text_results.replace('  ', '')),
            html.Br(),

            html.Table(
            # Header
            [html.Tr([html.Th(col) for col in columns])] +
            # Body
            [html.Tr([
                html.Td(df_row[x]) for x in range(len(columns))
            ]) for df_row in df_list]),

            

        ], className="container")

#        print(str(datetime.timedelta(seconds=time.time() - functionstartTime))+' before printing')


    else:

        # PAGE 1: FIRST PAGE. NOTHING STARTED YET.

        layout = html.Div([
            
            html.H3('Search CCC Articles', style={'textAlign':'center'}),
            html.Br(),
            dcc.Markdown(text_default.replace('  ', '')),

            # HERE GOES THE INTERFACE
            html.Br(),

            html.H5('Select the source'),

            html.Div(
            html.P('Source Wikipedia'),
            style={'display': 'inline-block','width': '200px'}),

            html.Div(
            html.P('Type of query'),
            style={'display': 'inline-block','width': '200px'}),

            html.Div(
            html.P('Language of the query'),
            style={'display': 'inline-block','width': '200px'}),


            html.Br(),
            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='source_lang',
                options=[{'label': i, 'value': source_lang_dict[i]} for i in sorted(source_lang_dict)],
                value='none',
                placeholder="Select a source language",
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),
    #        dcc.Link('Query',href=""),

            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='query_type',
                options=[{'label': i, 'value': query_type_dict[i]} for i in query_type_dict],
                value='none',
                placeholder="Select the type of query",           
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),

            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='query_lang',
                options=[{'label': i, 'value': query_lang_dict[i]} for i in sorted(query_lang_dict)],
                value='none',
                placeholder="Select a query language (optional)",           
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),


            html.Br(),

            html.H5('Query or Input Data'),
            html.Div(
            apply_default_value(params)(dcc.Textarea)(
                id='textbox',
                placeholder='You can introduce your search query or input data to obtain the results.',
                value='',
                style={'width': '100%', 'height':'100'}
             ), style={'display': 'inline-block','width': '590px'}),
    #        dcc.Link('Query',href=""),

            html.Br(),

            html.H5('Target Wikipedias'),

            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='target_langs',
                options=[{'label': i, 'value': target_langs_dict[i]} for i in sorted(target_langs_dict)],
                value=['en'],
                multi=True,
                placeholder="Select languages",           
                style={'width': '590px'}
             ), style={'display': 'inline-block','width': '590px'}),


            html.H5('Filter by content'),

            html.Div(
            html.P('Topic'),
            style={'display': 'inline-block','width': '200px'}),

            html.Div(
            html.P('Order by feature'),
            style={'display': 'inline-block','width': '200px'}),

            html.Div(
            html.P('Limit the results'),
            style={'display': 'inline-block','width': '200px'}),

            html.Br(),
            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='topic',
                options=[{'label': i, 'value': ccc_all_dict[i]} for i in sorted(ccc_all_dict, reverse=False)],
                value='',
                placeholder="Set topic (optional)",
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),

            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='order_by',
                options=[{'label': i, 'value': features_dict[i]} for i in sorted(features_dict)],
                value='none',
                placeholder="Order by (optional)",           
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),

            html.Div(
            apply_default_value(params)(dcc.Input)(
                id='limit',                    
                placeholder='Enter a value...',
                type='text',
                value='100',
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),

            html.A(html.Button('Query Results!'),
                href=''),

            

        ], className="container")

    return layout



def wikidata_sparql_query_to_articles_qitems(textbox_query):

    params = {'query': str(textbox_query), 'format': 'json'}
    url = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
    # data = requests.get(url,headers={'User-Agent': 'https://wikitech.wikimedia.org/wiki/User:Marcmiquel'}, params=params)

    data = requests.get(url,headers={'User-Agent': 'https://wikitech.wikimedia.org/wiki/User:Marcmiquel'}, params=params)

    data = data.json()
    qitems = set()
    try:
        for item in data['results']['bindings']:
            for x,y in item.items():
                currentv = y['value']
                if "http://www.wikidata.org/entity/" in currentv:
                    qitems.add(currentv.replace('http://www.wikidata.org/entity/',''))
    except:
        pass

    return qitems


def wikidata_api_query_to_articles_qitems(query_lang, target_lang, textbox_query, limit):

    functionstartTime = time.time()

    langs= ['en','fr','de','nl','ru','zh','es']

    if target_lang != None:
        langs.append(target_lang)

    languagecodes = []
    textbox_queries = []; 
    # for langcode in langs:
    #     print (langcode)
    #     trans = text_translation(query_lang, langcode, textbox_query)
    #     if trans != None:
    #         textbox_queries.append(trans)
    #         languagecodes.append(langcode)

    languagecodes.append(query_lang)
    textbox_queries.append(textbox_query)
#    print (languagecodes)

    categories = set()
    qitems = set()
    for v in range(0,len(languagecodes)):
        text = textbox_queries[v].lower()
        l = languagecodes[v]

        # print (text,l)
        # https://gist.github.com/edsu/dd92a2964e95782ce675 -> EXEMPLE! 
        API_ENDPOINT = "https://www.wikidata.org/w/api.php"
        params = {
        'action': 'query',
        'list': 'search',
        'srsearch': text,
        'format': 'json',
        'srprop': 'titlesnippet',
        'srlimit': limit
        }

        # https://www.wikidata.org/w/api.php?action=query&list=search&srsearch=igualada&srlimit=100

        # API_ENDPOINT = "https://www.wikidata.org/w/api.php"
        # params = {
        # 'action': 'wbsearchentities',
        # 'format': 'json',
        # 'language': l,
        # 'search': text
        # }

        r = requests.get(API_ENDPOINT, params = params)

        search = r.json()['query']['search']
        for element in search:
            qitem = element['title']
            snippet = element['titlesnippet'].replace('<span class="searchmatch">','').replace('</span>','')
            if 'Category' in snippet: categories.add(snippet.split(':')[1])
            qitems.add(qitem)
        # except:
        #     pass
        # print (len(qitems))

#    print (len(qitems))
    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
#    print(duration)

    return qitems, categories


def text_to_pageids_page_titles(languagecode, textbox, mysql_cur_read):
#    print (textbox)

    textbox = textbox.lower()
    page_titles = []

    if ('.org') in textbox:
        textbox = textbox.replace('https://'+languagecode+'.wikipedia.org/wiki/','')

    if '\n' in textbox:
        textbox = textbox.replace('\n','\t')

    if ';' in textbox:
        textbox = textbox.replace(';','\t')

    if ',' in textbox:
        textbox = textbox.replace(',','\t')

    page_titles = textbox.split('\t')

    page_titles = set(page_titles)

#    print (page_titles)
    params = []
    for x in page_titles:
        x = str(x).strip()
        params.append(x.replace(' ','_'))

#    print (params)
    page_asstring = ','.join( ['%s'] * len(params) )

    query = 'SELECT page_id, page_title FROM page WHERE page_namespace=0 AND page_is_redirect=0 AND CONVERT(page_title USING utf8mb4) COLLATE utf8mb4_general_ci IN (%s)' % page_asstring

    mysql_cur_read.execute(query,params)
    rows = mysql_cur_read.fetchall()

    page_dict = {}
    for row in rows:
        page_id = row[0]
        page_title = row[1].decode('utf-8')
        page_dict[page_id] = page_title

#    print (page_dict)

    return page_dict


def text_to_categories(languagecode, textbox):

#    textbox = textbox.lower()
    cat_titles = []

    if ('.org') in textbox:
        textbox = textbox.replace('https://'+languagecode+'.wikipedia.org/wiki/','')

    if '\n' in textbox:
        textbox = textbox.replace('\n','\t')

    if ';' in textbox:
        textbox = textbox.replace(';','\t')

    if ',' in textbox:
        textbox = textbox.replace(',','\t')

    cat_titles = textbox.split('\t')

    for x in range(0,len(cat_titles)):
        cat = str(cat_titles[x])
        if cat == '': continue
        if ':' in cat:
            cat_titles[x]=cat.split(':')[1].strip()

    cat_titles = set(cat_titles)

    return cat_titles


def category_to_categories(categories):

    mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()

    params = []
    for x in categories:
        params.append(x.replace(' ','_'))

    page_asstring = ','.join( ['%s'] * len(params) )
    query = 'SELECT page_title FROM page INNER JOIN categorylinks ON page_id=cl_from WHERE page_namespace=14 AND cl_to IN (%s);' % page_asstring

    # print (categories)
    # print(params)
    mysql_cur_read.execute(query,params)
    rows = mysql_cur_read.fetchall()

    for row in rows:
        page_title = row[0].decode('utf-8')
        categories.add(page_title)

    # print (categories)
    return categories


def categories_to_page_ids_page_titles(categories, mysql_cur_read):

    # print (categories)
    params = []
    for x in categories:
        params.append(x.replace(' ','_'))

    page_asstring = ','.join( ['%s'] * len(params) )

    # query = 'SELECT page_id, page_title, cl_to FROM page INNER JOIN categorylinks ON page_id = cl_from WHERE page_namespace=0 AND page_is_redirect=0 AND CONVERT(cl_to USING utf8mb4) COLLATE utf8mb4_general_ci IN (%s)' % page_asstring

    query = 'SELECT page_id, page_title, cl_to FROM page INNER JOIN categorylinks ON page_id = cl_from WHERE page_namespace=0 AND page_is_redirect=0 AND cl_to IN (%s)' % page_asstring

    # print (query)
    mysql_cur_read.execute(query,params)
    rows = mysql_cur_read.fetchall()

    page_dict = {}
    for row in rows:
        page_id = row[0]
        page_title = row[1].decode('utf-8')
        category = row[2].decode('utf-8')
        page_dict[page_id] = page_title#+','+category

    return page_dict

###

def qitem_to_page_titles_page_ids(qitems, languagecode, cursor):

    page_asstring = ','.join( ['?'] * len(qitems) )
    query = 'SELECT page_title, page_id FROM '+languagecode+'wiki WHERE qitem IN (%s)' % page_asstring
    page_titles_page_ids = {}

    for row in cursor.execute(query,list(qitems)):
        page_title = row[0]
        page_id = row[1]

        page_titles_page_ids[page_title]=page_id

    return page_titles_page_ids


def text_translation(langcode_original, langcode_target, title):

    tryit=1
    while(tryit==1):
        try:
            q = "https://cxserver.wikimedia.org/v2/translate/"+langcode_original+"/"+langcode_target+"/Apertium"
            # print (q)
            r = requests.post(q, data={'html': '<div>'+title+'</div>'}, timeout=0.3)
            tryit=0 # https://cxserver.wikimedia.org/v2/?doc  https://codepen.io/santhoshtr/pen/zjMMrG           
        except:
            print ('timeout.')
            time.sleep(1)

    if str(r) == '<Response [200]>':
        page_title_target = str(r.text).split('<div>')[1].split('</div>')[0]
        return page_title_target


def article_page_ids_titles_to_categories(languagecode, page_ids, page_titles, mysql_cur_read):

    if page_titles != None and len(page_titles)!=0:
        # print ('page_titles')
        if isinstance(page_titles, str):
            page_titles = [page_titles]

        params = page_titles
        page_asstring = ','.join( ['%s'] * len(params) )
        query = 'SELECT cl_to, page_title FROM categorylinks INNER JOIN page ON cl_from = page_id WHERE page_title IN (%s)' % page_asstring

    elif page_ids != None and len(page_ids)!=0:
        # print ('page_ids')
        if isinstance(page_ids, str):
            page_ids = [page_ids]

        params = page_ids
        page_asstring = ','.join( ['%s'] * len(params) )
        query = 'SELECT cl_to, cl_from FROM categorylinks WHERE cl_from IN (%s)' % page_asstring

    else:
#        print (page_ids, page_titles)
#        print ('No input!')
        return

    mysql_cur_read.execute(query,params)
    rows = mysql_cur_read.fetchall()

    pages_categories_dict = {}

    categories = set()
    for row in rows:
        category = row[0].decode('utf-8')
        data_input = row[1]
        categories.add(category)

        try:
            pages_categories_dict[data_input]=pages_categories_dict[data_input].add(category)
        except:
            a=set()
            pages_categories_dict[data_input]=a.add(category)

    # print (categories)
    return pages_categories_dict, categories


def lang1_page_titles_ids_to_lang2_page_titles_qitems_features(source_lang, target_langs, page_ids, page_titles, qitems, features, topic, conn):

    if features != None:
        qfeat = ''
        for f in features:
            if qfeat != '': qfeat+= ', '
            qfeat += 'a.'+f
    else:
        qfeat = 'a.num_inlinks, a.num_inlinks_from_ccc, a.num_outlinks, a.num_bytes, a.num_references, a.num_images, a.num_editors, a.num_edits, a.num_discussions, a.num_pageviews, a.num_interwiki, a.num_wdproperty'

    query = 'SELECT a.page_title as apage_title, '+qfeat+', b.page_title as bpage_title'
    for x in range(1,len(target_langs)):
        query+= ', c'+str(x)+'.page_title as c'+str(x)+'page_title'

    query+= ', a.qitem FROM '+source_lang+'wiki a LEFT JOIN '+target_langs[0]+'wiki b ON a.qitem = b.qitem '
    for x in range(1,len(target_langs)):
        query += 'LEFT JOIN '+target_langs[x]+'wiki c'+str(x)+' USING (qitem) '

    if page_ids != None:
        if isinstance(page_ids, str):
            page_ids = [page_ids]
        params = page_ids

        page_asstring = ','.join( ['?'] * len(params) )
        query += 'WHERE a.page_id IN (%s)' % page_asstring

    elif page_titles != None:
        if isinstance(page_titles, str):
            page_titles = [page_titles]
        params = page_titles

        page_asstring = ','.join( ['?'] * len(params) )
        query += 'WHERE a.page_title IN (%s)' % page_asstring

    elif qitems != None:
        params = qitems

        page_asstring = ','.join( ['?'] * len(params) )
        query += 'WHERE a.qitem IN (%s)' % page_asstring


    if topic == 'ccc':
        query+= ' AND a.ccc_binary=1'

    if topic == 'ccc_geolocated':
        query+= ' AND a.ccc_geolocated=1'

    if topic == 'men':
        query+= ' AND a.gender="Q6581097"'

    if topic == 'women':
        query+= ' AND a.gender="Q6581072"'

    # print (topic)
    # print (query)
    df = pd.read_sql_query(query, conn, params = params)#, parameters)
    df = df.fillna(0)

#    print (len(df))
    return df


# callback update URL
component_ids_app23 = ['source_lang','query_lang','query_type','textbox','target_langs','topic','order_by','limit']
@dash_app23.callback(Output('url', 'search'),
              inputs=[Input(i, 'value') for i in component_ids_app23])
def update_url_state(*values):
    if not isinstance(values[4], str):
        values = values[0],values[1],values[2],values[3],','.join(values[4]),values[5],values[6],values[7]

    state = urlencode(dict(zip(component_ids_app23, values)))
    return '?'+state
#    return f'?{state}'

# callback update page layout
@dash_app23.callback(Output('page-content', 'children'),
              inputs=[Input('url', 'href')])
def page_load(href):
    if not href:
        return []
    state = parse_state(href)
    return dash_app23_build_layout(state)


    
if __name__ == '__main__':
    dash_app23.run_server(debug=True)
