# -*- coding: utf-8 -*-

# flash dash
import flask
from flask import Flask, request, render_template
from flask import send_from_directory
from dash import Dash
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_table_experiments as dt
from dash.dependencies import Input, Output, State
# viz
import plotly
import chart_studio.plotly as py
import plotly.figure_factory as ff
import plotly.express as px
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

ISO31662_subdivisions_dict, subdivisions_ISO31662_dict = wikilanguages_utils.load_iso_31662_to_subdivisions_names()


for i in (set(languages.index.tolist()) - set(list(wikipedialanguage_numberarticles.keys()))):
    try: languages.drop(i, inplace=True); territories.drop(i, inplace=True)
    except: pass
print (wikilanguagecodes)


# # web
title_addenda = ' - Wikipedia Diversity Observatory (WDO)'
external_stylesheets = ['https://wcdo.wmflabs.org/assets/bWLwgP.css']

#########################################################
#########################################################
#########################################################





group_labels = wikilanguages_utils.get_diversity_categories_labels()





####### -------------------- This is the beginning of the App.

##### METHODS SPECIFIC #####

# Get me the recent created articles or recent edits (Filter: Bot, New)
def get_recent_articles_recent_edits(languagecode, edittypes, editortypes, periodhours, resultslimit):
    functionstartTime = time.time()

    def conditions(s):
        if (s['rc_bot'] == 1):
            return 'bot'
        elif (s['rev_actor'] == 'NULL'):
            return 'anonymous'
        else:
            return 'editor'


    query = 'SELECT CONVERT(rc_title USING utf8mb4) as page_title, rc_cur_id as page_id, CONVERT(rc_timestamp USING utf8mb4) as rc_timestamp, rc_bot, rev_actor, rc_new_len as Bytes, CONVERT(actor_name USING utf8mb4) as actor_name FROM recentchanges rc INNER JOIN revision rv ON rc.rc_timestamp = rv.rev_timestamp INNER JOIN actor a ON rv.rev_actor = a.actor_id WHERE rc_namespace = 0 '

#    query = 'SELECT CONVERT(rc_title USING utf8mb4) as page_title, rc_cur_id as page_id, rc_new, rc_type, rc_deleted, rc_bot, CONVERT(rc_timestamp USING utf8mb4) as rc_timestamp FROM recentchanges WHERE rc_namespace = 0 '

    if edittypes == 'new_articles': 
        query += 'AND rc_new = 1 '

    if edittypes == 'wikidata_edits': 
        query += 'AND rc_type = 5 '

    if editortypes == 'no_bots':
        query+= 'AND rc_bot = 0 '

    if editortypes == 'bots_edits':
        query+= 'AND rc_bot = 1 '

    if editortypes == 'anonymous_edits':
        query+= 'AND actor_user IS NULL '

    if editortypes == 'editors_edits':
        query+= 'AND rc_bot = 0 '
        query+= 'AND actor_user IS NOT NULL '


    if periodhours != 0:
        now = datetime.datetime.now()
        timelimit = now - datetime.timedelta(hours=periodhours)
        timelimit_string = datetime.datetime.strftime(timelimit,'%Y%m%d%H%M%S') 
        query+= 'AND rc_timestamp > "'+timelimit_string+'" '

    query+= 'ORDER BY rc_timestamp DESC'
    if resultslimit != None: 
        query+= ' LIMIT '+str(resultslimit)
    else:
        query+= ' LIMIT '+str(5000)

    # print (query)
    mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()
    df = pd.read_sql(query, mysql_con_read);

    df['Editor Edit Type'] = df.apply(conditions, axis=1)
    df=df.drop(columns=['rev_actor','rc_bot'])

    # print (df.head(100))
    # print (len(df))
    # print(str(datetime.timedelta(seconds=time.time() - functionstartTime))+' after queries.')
    # input('')
    return df



# Get me the articles that are also in the wikipedia_diversity_production.db and the diversity categories it belongs to.
def get_articles_diversity_categories_wikipedia_diversity_db(languagecode, df_rc):

    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()
    df_rc = df_rc.set_index('page_title')

    # df_rc = df_rc.head(10)
    # print (df_rc)
    # print (len(df_rc))

    page_titles = df_rc.index.tolist()
    page_asstring = ','.join( ['?'] * len(page_titles) )
    df_categories = pd.read_sql_query('SELECT page_title, qitem, iso3166, iso31662, region, gender, ethnic_group, sexual_orientation, ccc_binary, num_editors, num_pageviews, date_created, num_inlinks, num_outlinks, num_inlinks_from_CCC, num_outlinks_to_CCC, num_inlinks_from_women, num_outlinks_to_women, num_references, num_discussions, num_wdproperty, num_interwiki, num_images, wikirank from '+languagecode+'wiki WHERE page_title IN ('+page_asstring+');', conn, params = page_titles)

    df_categories = df_categories.set_index('page_title')
    df_rc_categories = df_rc.merge(df_categories, how='left', on='page_title')

    return df_rc_categories




def get_proportion_diversity_category(df_rc_categories, limit, language):

    iso3166 = df_rc_categories['iso3166'].value_counts()#.to_dict()
    iso31662 = df_rc_categories['iso31662'].value_counts()#.to_dict()
    region = df_rc_categories['region'].value_counts()#.to_dict()
    gender = df_rc_categories['gender'].value_counts()#.to_dict()
    ethnic_group = df_rc_categories['ethnic_group'].value_counts()#.to_dict()
    sexual_orientation = df_rc_categories['sexual_orientation'].value_counts()#.to_dict()
    ccc_binary = df_rc_categories['ccc_binary'].value_counts().iloc[1:]#.to_dict()

#    print (ccc_binary); input('')


    dfx = pd.DataFrame(iso3166).rename_axis('Id').rename(columns={'iso3166':'Number of edits'}).reset_index()
    dfx['Category'] = 'ISO3166'
    dfx['Percentage'] = round(100*dfx['Number of edits']/dfx['Number of edits'].sum(),2)
    dfy = dfx

    dfx = pd.DataFrame(iso31662).rename_axis('Id').rename(columns={'iso31662':'Number of edits'}).reset_index()
    dfx['Category'] = 'ISO31662'
    dfx['Percentage'] = round(100*dfx['Number of edits']/dfx['Number of edits'].sum(),2)
    dfy = pd.concat([dfy, dfx],sort=True)

    dfx = pd.DataFrame(region).rename_axis('Id').rename(columns={'region':'Number of edits'}).reset_index()
    dfx['Category'] = 'Continent'
    dfx['Percentage'] = round(100*dfx['Number of edits']/dfx['Number of edits'].sum(),2)
    dfy = pd.concat([dfy, dfx],sort=True)

    dfx = pd.DataFrame(gender).rename_axis('Id').rename(columns={'gender':'Number of edits'}).reset_index()
    dfx['Category'] = 'Gender'
    dfx['Percentage'] = round(100*dfx['Number of edits']/dfx['Number of edits'].sum(),2)
    dfy = pd.concat([dfy, dfx],sort=True)

    dfx = pd.DataFrame(ethnic_group).rename_axis('Id').rename(columns={'ethnic_group':'Number of edits'}).reset_index()
    dfx['Category'] = 'Ethnic Group'
    dfx['Percentage'] = round(100*dfx['Number of edits']/dfx['Number of edits'].sum(),2)
    dfy = pd.concat([dfy, dfx],sort=True)

    dfx = pd.DataFrame(sexual_orientation).rename_axis('Id').rename(columns={'sexual_orientation':'Number of edits'}).reset_index()
    dfx['Category'] = 'Sexual Orientation'
    dfx['Percentage'] = round(100*dfx['Number of edits']/dfx['Number of edits'].sum(),2)
    dfy = pd.concat([dfy, dfx],sort=True)

    dfx = pd.DataFrame(ccc_binary).rename_axis('Id').rename(columns={'ccc_binary':'Number of edits'}).reset_index()
    dfx['Category'] = language+' CCC'
    dfx['Percentage'] = round(100*dfx['Number of edits']/limit,2)

#    dfx.at[0,'Id']= language+' CCC'

    dfy = pd.concat([dfy, dfx],sort=True)


    return dfy




### DASH APP ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 
#dash_app18 = Dash(__name__, server = app, url_base_pathname = webtype + '/search_ccc_articles/', external_stylesheets=external_stylesheets ,external_scripts=external_scripts)
dash_app18 = Dash(url_base_pathname = '/recent_changes_diversity/', external_stylesheets=external_stylesheets, suppress_callback_exceptions = True)

dash_app18.config['suppress_callback_exceptions']=True
dash_app18.title = 'Recent Changes Diversity'+title_addenda
dash_app18.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),

])


features_dict = {'Edit Timestamp':'rc_timestamp','Editors': 'num_editors', 'Edits': 'num_edits', 'Images': 'num_images', 'Wikirank': 'wikirank', 'Pageviews': 'num_pageviews', 'Inlinks': 'num_inlinks', 'References': 'num_references', 'Current Length': 'rev_len', 'Outlinks': 'num_outlinks', 'Interwiki': 'num_interwiki', 'Wikidata Properties': 'num_wdproperty', 'Discussions': 'num_discussions', 'Creation Date': 'date_created', 'Inlinks from CCC': 'num_inlinks_from_ccc', 'Outlinks to CCC': 'num_outlinks_to_ccc', 'Inlinks from Women': 'num_inlinks_from_women', 'Outlinks to Women': 'num_outlinks_to_women', 'Featured Article': 'featured_article', 'ISO3166':'iso3166', 'ISO3166-2':'iso31662', 'Continent':'region', 'Gender':'gender', 'Ethnic Group':'ethnic_group', 'Sexual Orientation':'sexual_orientation', 'CCC':'ccc_binary'}

features_dict_inv = {v: k for k, v in features_dict.items()}

editstype_dict = {'New articles':'new_articles','All edits':'all_edits','Wikidata Edits':'wikidata_edits'}
editortype_dict = {'Only registered editors edits':'editors_edits','Only anonymous edits':'anonymous_edits','Only bots edits':'bots_edits','No bots edits':'no_bots','All editors':'all_editors'}

diversitycategory_dict = {'Country Code (ISO3166)':'iso3166', 'Subdivision Code (ISO3166-2)':'iso31662', 'Continent':'region', 'Gender':'gender', 'Ethnic Group':'ethnic_group', 'Sexual Orientation':'sexual_orientation', 'CCC':'ccc_binary'}



## ----------------------------------------------------------------------------------------------------- ##



text_default = '''In this page you can retrieve the list of Recent Changes in a Wikipedia language edition according with different categories relevant to diversity (e.g. Gender, Sexual Orientation, Ethnic Group, Cultural Context Content (CCC), Country, Country Subdivisions, Continents).'''    



text_results = '''
The following graph shows the number of edits for each of the categories relevant to diversity that were detected using the project's database. The colors represent the different topics for each category. The table shows the list of requested Recent changes edits. The columns present the article title, timestamp, editor, article creation date, current length after the edit, number of pageviews and number of Interwiki links. When a featured is selected to sort the results (order by), it is added as a column. The remaining columns are the mentioned diversity-related categories.
'''    


## ----------------------------------------------------------------------------------------------------- ##


interface_row1 = html.Div([

    html.Div([
    html.P(
        [
            "Source ",
            html.Span(
                "language",
                id="tooltip-target-lang",
                style={"textDecoration": "underline", "cursor": "pointer"},
            ),
        ]
    ),
    dbc.Tooltip(
        html.P(
            "Select a source language to retrieve a list of recent changes.",
        style={"width": "38rem", 'font-size': 12, 'text-align':'left', 'backgroundColor':'#F7FBFE','padding': '12px 12px 12px 12px'}
        ),
        target="tooltip-target-lang",
        placement="bottom",
        style={'color':'black', 'backgroundColor':'transparent'},
    )],
    style={'display': 'inline-block','width': '200px'},
    ),



    html.Div([
    html.P(
        [
            "Types of ",
            html.Span(
                "edits",
                id="tooltip-target-content",
                style={"textDecoration": "underline", "cursor": "pointer"},
            ),
        ]
    ),
    dbc.Tooltip(
        html.P(
            "Select all the edits, edits that resulted in new articles, or external edits made in Wikidata.",
        style={"width": "21rem", 'font-size': 12, 'text-align':'left', 'backgroundColor':'#F7FBFE','padding': '12px 12px 12px 12px'}
        ),
        target="tooltip-target-content",
        placement="bottom",
        style={'color':'black', 'backgroundColor':'transparent'},
    )],
    style={'display': 'inline-block','width': '100px'},
    ),



    html.Div([
    html.P(
        [
            "Types of ",
            html.Span(
                "editors",
                id="tooltip-target-editortype",
                style={"textDecoration": "underline", "cursor": "pointer"},
            ),
        ]
    ),
    dbc.Tooltip(
        html.P(
            "Select or filter the edits by a specific type of editor.",
        style={"width": "21rem", 'font-size': 12, 'text-align':'left', 'backgroundColor':'#F7FBFE','padding': '12px 12px 12px 12px'}
        ),
        target="tooltip-target-editortype",
        placement="bottom",
        style={'color':'black', 'backgroundColor':'transparent'},
    )],
    style={'display': 'inline-block','width': '200px'},
    ),




    html.Div(
    [
    html.P(
        [
            "Filter by ",
            html.Span(
                "diversity category",
                id="tooltip-target-category",
                style={"textDecoration": "underline", "cursor": "pointer"},
            ),
        ]
    ),
    dbc.Tooltip(
        html.P(
            "Select a Topic to filter the results to show only articles about certain topic (geolocated with a ISO code, gender, CCC, etc.)",
        style={"width": "42rem", 'font-size': 12, 'text-align':'left', 'backgroundColor':'#F7FBFE','padding': '12px 12px 12px 12px'}
        ),
        target="tooltip-target-category",
        placement="bottom",
        style={'color':'black', 'backgroundColor':'transparent'},
    )],
    style={'display': 'inline-block','width': '200px'},
    ),

    ])


interface_row2 = html.Div([

    html.Div([
    html.P(
        [
            "Order by ",
            html.Span(
                "feature or category",
                id="tooltip-target-orderby",
                style={"textDecoration": "underline", "cursor": "pointer"},
            ),
        ]
    ),
    dbc.Tooltip(
        html.P(
            "Select a relevance feature or diversity category to sort the results).",
        style={"width": "38rem", 'font-size': 12, 'text-align':'left', 'backgroundColor':'#F7FBFE','padding': '12px 12px 12px 12px'}
        ),
        target="tooltip-target-orderby",
        placement="bottom",
        style={'color':'black', 'backgroundColor':'transparent'},
    )],
    style={'display': 'inline-block','width': '200px'},
    ),



    html.Div(
    [
    html.P(
        [
            "Timeframe in ",
            html.Span(
                "hours",
                id="tooltip-target-timeframe",
                style={"textDecoration": "underline", "cursor": "pointer"},
            ),
        ]
    ),
    dbc.Tooltip(
        html.P(
            "Specify the number of hours from now you to retrieve the recent changes (by default 24).",
        style={"width": "45rem", 'font-size': 12, 'text-align':'left', 'backgroundColor':'#F7FBFE','padding': '12px 12px 12px 12px'}
        ),
        target="tooltip-target-timeframe",
        placement="bottom",
        style={'color':'black', 'backgroundColor':'transparent'},
    )],
    style={'display': 'inline-block','width': '200px'},
    ),



    html.Div(
    [
    html.P(
        [
            "Limit the ",
            html.Span(
                "number of results",
                id="tooltip-target-limit",
                style={"textDecoration": "underline", "cursor": "pointer"},
            ),
        ]
    ),
    dbc.Tooltip(
        html.P(
            "Limit the number of results (by default 300)",
        style={"width": "22rem", 'font-size': 12, 'text-align':'left', 'backgroundColor':'#F7FBFE','padding': '12px 12px 12px 12px'}
        ),
        target="tooltip-target-limit",
        placement="bottom",
        style={'color':'black', 'backgroundColor':'transparent'},
    )],
    style={'display': 'inline-block','width': '200px'},
    )

])




def dash_app18_build_layout(params):

    if len(params)!=0 and params['lang']!='none' and params['lang']!= None:
        functionstartTime = time.time() 

        if 'lang' in params:
            languagecode = params['lang']
            if languagecode != 'none': language = languages.loc[languagecode]['languagename']
        else:
            languagecode = 'none'

        if 'content' in params:
            content = params['content']
        else:
            content = 'none'

        if 'editortype' in params:
            editortype=params['editortype']
        else:
            editortype='editortype'

        if 'diversitycategory' in params:
            category = params['diversitycategory']
        else:
            category = 'none'

        if 'orderby' in params:
            orderby=params['orderby'].lower()
        else:
            orderby='none'

        if 'timeframe' in params:
            timeframe = params['timeframe']
        else:
            timeframe = 'none'

        if 'limit' in params:
            limit = int(params['limit'])
        else:
            limit = 'none'
        

        # print (languagecode, language, content, editortype, category, orderby, timeframe, limit)
        df = pd.read_csv(databases_path+'df_rc_categories_sample.csv')
        df = df.rename_axis('position')
        df = df.reset_index()

        if limit != 'none':
            df = df.head(limit)

        if category != 'none':
            df = df.loc[df[category].notnull()]

        """
        df = get_recent_articles_recent_edits(languagecode, editstype, editortype, timeframe, limit)
        df = get_articles_diversity_categories_wikipedia_diversity_db(languagecode, df)     
        df = df.rename_axis('position')
        df = df.reset_index()
        """

        qitem_labels_lang = group_labels.loc[(group_labels["lang"] == languagecode)][['qitem','label','page_title']]
        qitem_labels_lang = qitem_labels_lang.set_index('qitem')
        qitem_labels_en = group_labels.loc[(group_labels["lang"] == "en")][['qitem','label','page_title']]
        qitem_labels_en = qitem_labels_en.set_index('qitem')



        # PAGE CASE 2: PARAMETERS WERE INTRODUCED AND THERE ARE NO RESULTS
        if len(df) == 0:

            layout = html.Div([
                
                html.H3('Recent Changes Diversity', style={'textAlign':'center'}),
                html.Br(),

                dcc.Markdown(
                    text_default.replace('  ', '')),


                # HERE GOES THE INTERFACE
                # LINE 
                html.Br(),
                html.H5('Select the source'),
                interface_row1,
                html.Div(
                apply_default_value(params)(dcc.Dropdown)(
                    id='lang',
                    options=[{'label': i, 'value': language_names[i]} for i in sorted(language_names)],
                    value='none',
                    placeholder="Select a source language",
                    style={'width': '190px'}
                 ), style={'display': 'inline-block','width': '200px'}),
        #        dcc.Link('Query',href=""),

                html.Div(
                apply_default_value(params)(dcc.Dropdown)(
                    id='editstype',
                    options=[{'label': i, 'value': editstype_dict[i]} for i in editstype_dict],
                    value='none',
                    placeholder="Select the type of edits",           
                    style={'width': '190px'}
                 ), style={'display': 'inline-block','width': '200px'}),

                html.Div(
                apply_default_value(params)(dcc.Dropdown)(
                    id='editortype',
                    options=[{'label': i, 'value': editortype_dict[i]} for i in editortype_dict],
                    value='none',
                    placeholder="Select the type of editors",           
                    style={'width': '190px'}
                 ), style={'display': 'inline-block','width': '200px'}),


                html.Div(
                apply_default_value(params)(dcc.Dropdown)(
                    id='diversitycategory',
                    options=[{'label': i, 'value': diversitycategory_dict[i]} for i in diversitycategory_dict],
                    value='none',
                    placeholder="Select the type of editors",           
                    style={'width': '190px'}
                 ), style={'display': 'inline-block','width': '200px'}),



                # LINE 
                html.Br(),
                interface_row2,
                html.Div(
                apply_default_value(params)(dcc.Dropdown)(
                    id='orderby',
                    options=[{'label': i, 'value': features_dict[i]} for i in sorted(features_dict)],
                    value='none',
                    placeholder="Order by (optional)",           
                    style={'width': '190px'}
                 ), style={'display': 'inline-block','width': '200px'}),

                html.Div(
                apply_default_value(params)(dcc.Input)(
                    id='timeframe',                    
                    placeholder='Enter a value...',
                    type='text',
                    value='10',
                    style={'width': '190px'}
                 ), style={'display': 'inline-block','width': '200px'}),

                html.Div(
                apply_default_value(params)(dcc.Input)(
                    id='limit',                    
                    placeholder='Enter a value...',
                    type='text',
                    value='300',
                    style={'width': '190px'}
                 ), style={'display': 'inline-block','width': '200px'}),

                ###            

                html.Div(
                html.A(html.Button('Query Results!'),
                    href=''),
                style={'display': 'inline-block','width': '200px'}),

                html.Br(),
                html.Br(),

                html.Hr(),
                # html.H5('Results'),
                # dcc.Markdown(text_results.replace('  ', '')),
                html.Br(),
                html.H6('There are not results. Unfortunately this list is empty for this language.'),

                # footbar,
            ], className="container")

            return layout


        # PAGE CASE 3: PARAMETERS WERE INTRODUCED AND THERE ARE RESULTS
#        print (df.columns)
        # print(str(datetime.timedelta(seconds=time.time() - functionstartTime))+' after queries.')


        # PREPARE THE GRAPH
        dfy = get_proportion_diversity_category(df, limit, language)
        column = list()
        for index, rows in dfy.iterrows():
            Topic = rows['Id']
            category = rows['Category']
            label = ''
            if category == 'ISO31662':


                try:
                    label = ISO31662_subdivisions_dict[Topic]
                except:
                    label = Topic
            
            elif category == 'ISO3166':
                label = country_names[Topic]

            elif category == 'Continent':
                label = Topic

            elif category == 'CCC':
                label = 'CCC'

            else:
                try:
                    try:
                        label = qitem_labels_lang.loc[Topic]['page_title']
                        if len(label) == 2: label = label.tolist()[0]
                        if label == '': label = qitem_labels_lang.loc[Topic]['label']
                    except:
                        label = qitem_labels_lang.loc[Topic]['label']
                        if len(label) == 2: label = label.tolist()[0]

                except: 
                    try:
                        try:
                            label = qitem_labels_en.loc[Topic]['page_title']
                            if len(label) == 2: label = label.tolist()[0]
                            if label == '': label = qitem_labels_en.loc[Topic]['label']
                        except:
                            label = qitem_labels_en.loc[Topic]['label']
                            if len(label) == 2: label = label.tolist()[0]
                    except:
                        label = Topic
            column.append(label)
        dfy['Topic'] = column 
        fig = px.bar(dfy, x="Category", y="Number of edits", color="Topic", title="Categories Summary", hover_data=['Id','Percentage'],text=dfy['Percentage'])




        # PREPARE THE DATATABLE
        columns_dict = {'position':'Nº','page_title':'Title','rc_timestamp':'Edit Timestamp','actor_name':'Editor','rev_len':'Current Length','ccc_binary':language+' CCC', 'num_inlinks_from_CCC':'Inlinks from CCC', 'num_outlinks_to_CCC':'Outlinks to CCC'}
        columns_dict.update(features_dict_inv)

        df=df.rename(columns=columns_dict)
        final_columns = ['Nº','Title','Edit Timestamp','Editor']+['Creation Date','Current Length','Pageviews','Interwiki']
        diversity = ['ISO3166','ISO3166-2','Continent','Gender','Ethnic Group','Sexual Orientation',language+' CCC']
        if orderby!='none' and features_dict_inv[orderby] not in diversity and features_dict_inv[orderby] not in final_columns:
            final_columns+= [features_dict_inv[orderby]]
        final_columns = final_columns + diversity
        columns = final_columns

        # print (df.columns.tolist())
        # print (columns)
        # df1=df1.drop(columns=todelete)        

        orderby = orderby.lower()
        if orderby != 'none':
            order = features_dict_inv[orderby]
        else:
            order = features_dict_inv['rc_timestamp']
        df = df.sort_values(order,ascending=False)
        df_list = list()

        k = 0
        for index, rows in df.iterrows():
            if k > limit: break

            df_row = list()

            for col in columns:
                title = rows['Title']
                if not isinstance(title, str):
                    title = title.iloc[0]

                if col == 'Nº':
                    k+=1
                    df_row.append(str(k))

                elif col == 'Title':
                    title = rows['Title']
                    if not isinstance(title, str):
                        title = title.iloc[0]
                    df_row.append(html.A(title.replace('_',' '), href='https://'+languagecode+'.wikipedia.org/wiki/'+title.replace(' ','_'), target="_blank", style={'text-decoration':'none'}))

                elif col == 'Editor':
                    editor = rows['Editor']
                    df_row.append(html.Div(editor, style={'text-decoration':'none'}))

                elif col == 'Interwiki':
                    df_row.append(html.A( rows['Interwiki'], href='https://www.wikidata.org/wiki/'+rows['qitem'], target="_blank", style={'text-decoration':'none'}))

                elif col == 'Current Length':
                    value = round(float(int(rows[col])/1000),1)
                    df_row.append(str(value)+'k')

                elif col == 'Outlinks' or col == 'References' or col == 'Images':
                    title = rows['Title']
                    df_row.append(html.A( rows[col], href='https://'+languagecode+'.wikipedia.org/wiki/'+title.replace(' ','_'), target="_blank", style={'text-decoration':'none'}))

                elif col == 'Inlinks':
                    df_row.append(html.A( rows['Inlinks'], href='https://'+languagecode+'.wikipedia.org/wiki/Special:WhatLinksHere/'+rows['Title'].replace(' ','_'), target="_blank", style={'text-decoration':'none'}))

                elif col == 'Inlinks from CCC':
                    df_row.append(html.A( rows['Inlinks from CCC'], href='https://'+languagecode+'.wikipedia.org/wiki/Special:WhatLinksHere/'+rows['Title'].replace(' ','_'), target="_blank", style={'text-decoration':'none'}))

                elif col == 'Outlinks from CCC':
                    df_row.append(html.A( rows['Outlinks from CCC'], href='https://'+languagecode+'.wikipedia.org/wiki/'+rows['Title'].replace(' ','_'), target="_blank", style={'text-decoration':'none'}))

                elif col == 'Inlinks from Women':
                    df_row.append(html.A( rows['Inlinks from Women'], href='https://'+languagecode+'.wikipedia.org/wiki/Special:WhatLinksHere/'+rows['Title'].replace(' ','_'), target="_blank", style={'text-decoration':'none'}))

                elif col == 'Outlinks from Women':
                    df_row.append(html.A( rows['Outlinks from Women'], href='https://'+languagecode+'.wikipedia.org/wiki/'+rows['Title'].replace(' ','_'), target="_blank", style={'text-decoration':'none'}))


                elif col == 'Editors':
                    df_row.append(html.A( rows['Editors'], href='https://'+languagecode+'.wikipedia.org/w/index.php?title='+rows['Title'].replace(' ','_')+'&action=history', target="_blank", style={'text-decoration':'none'}))

                elif col == 'Edits':
                    df_row.append(html.A( rows['Edits'], href='https://'+languagecode+'.wikipedia.org/w/index.php?title='+rows['Title'].replace(' ','_')+'&action=history', target="_blank", style={'text-decoration':'none'}))

                elif col == 'Discussions':
                    df_row.append(html.A( rows['Discussions'], href='https://'+languagecode+'.wikipedia.org/wiki/Talk:'+rows['Title'].replace(' ','_'), target="_blank", style={'text-decoration':'none'}))

                elif col == 'Wikirank':
                    df_row.append(html.A( rows['Wikirank'], href='https://wikirank.net/'+languagecode+'/'+rows['Title'], target="_blank", style={'text-decoration':'none'}))

                elif col == 'Pageviews':
                    df_row.append(html.A( rows['Pageviews'], href='https://tools.wmflabs.org/pageviews/?project='+languagecode+'.wikipedia.org&platform=all-access&agent=user&range=latest-20&pages='+rows['Title'].replace(' ','_')+'&action=history', target="_blank", style={'text-decoration':'none'}))

                elif col == 'Wikidata Properties':
                    df_row.append(html.A( rows['Wikidata Properties'], href='https://www.wikidata.org/wiki/'+rows['qitem'], target="_blank", style={'text-decoration':'none'}))

                elif col == 'Discussions':
                    title = rows['Title']
                    df_row.append(html.A(str(rows[col]), href='https://'+languagecode+'.wikipedia.org/wiki/'+title.replace(' ','_'), target="_blank", style={'text-decoration':'none'}))

                elif col == 'Edit Timestamp':
                    timestamp = str(int(rows[col]))
                    df_row.append(datetime.datetime.strftime(datetime.datetime.strptime(timestamp,'%Y%m%d%H%M%S'),'%H:%M:%S %d-%m-%Y'))

                elif col == 'Creation Date':
                    try:
                        timestamp = str(int(rows[col]))
                        df_row.append(datetime.datetime.strftime(datetime.datetime.strptime(timestamp,'%Y%m%d%H%M%S'),'%Y-%m-%d'))
                    except:
                        df_row.append('')

                elif col == 'Qitem':
                    df_row.append(html.A( rows['Qitem'], href='https://www.wikidata.org/wiki/'+rows['Qitem'], target="_blank", style={'text-decoration':'none'}))


                elif col == 'Sexual Orientation' or col == 'Ethnic Group' or col == 'Gender':
                    if pd.isna(rows[col]): 
                        df_row.append('')
                        continue
                    qit = str(rows[col])

                    if ';' in qit:
                        qlist = qit.split(';')
                    else:
                        qlist = [qit]

                    c = len(qlist)

                    text = ' '

                    i = 0
                    for ql in qlist:
                        i+= 1
                        try:
                            try:
                                label = qitem_labels_lang.loc[ql]['page_title']
                                if label == '': label = qitem_labels_lang.loc[ql]['label']
                            except:
                                label = qitem_labels_lang.loc[ql]['label']

                            text+= '['+label+']'+'('+'http://'+languagecode+'.wikipedia.org/wiki/'+ label.replace(' ','_')+')'
                        except: 
                            try:
                                try:
                                    label = qitem_labels_en.loc[ql]['page_title']
                                    if label == '': label = qitem_labels_en.loc[ql]['label']
                                except:
                                    label = qitem_labels_en.loc[ql]['label']

                                text+= '['+label+' (en)'+']'+'('+'http://en.wikipedia.org/wiki/'+ label.replace(' ','_')+')'

                            except:
                                label = ql
                                text+= '['+label+']'+'('+'https://www.wikidata.org/wiki/'+ label+')'

                        if i<c:
                            text+=', '

                    df_row.append(dcc.Markdown(text))


                elif col == language+' CCC':
#                    print (rows['Title'],rows['CCC'])
                    if rows['CCC'] == 1:
                        df_row.append('yes')
                    else:
                        df_row.append('')

                else:
                    df_row.append(rows[col])

            if k <= limit:
                df_list.append(df_row)


        # print(str(datetime.timedelta(seconds=time.time() - functionstartTime))+' after htmls')
        # print (len(df_list))


        # RESULTS PAGE
        title = 'Recent Changes Diversity'
        df1 = pd.DataFrame(df_list)
        dash_app18.title = title+title_addenda

        # LAYOUT
        layout = html.Div([
            
            html.H3(title, style={'textAlign':'center'}),
#            html.Br(),

            dcc.Markdown(
                text_default.replace('  ', '')),
            html.Br(),


            # HERE GOES THE INTERFACE
            # LINE 
            html.Br(),
            html.H5('Select the source'),

            interface_row1,
            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='lang',
                options=[{'label': i, 'value': language_names[i]} for i in sorted(language_names)],
                value='none',
                placeholder="Select a source language",
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),
    #        dcc.Link('Query',href=""),

            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='editstype',
                options=[{'label': i, 'value': editstype_dict[i]} for i in editstype_dict],
                value='none',
                placeholder="Select the type of edits",           
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),

            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='editortype',
                options=[{'label': i, 'value': editortype_dict[i]} for i in editortype_dict],
                value='none',
                placeholder="Select the type of editors",           
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),


            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='diversitycategory',
                options=[{'label': i, 'value': diversitycategory_dict[i]} for i in diversitycategory_dict],
                value='none',
                placeholder="Select the type of editors",           
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),



            # LINE 
            html.Br(),
            interface_row2,
            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='orderby',
                options=[{'label': i, 'value': features_dict[i]} for i in sorted(features_dict)],
                value='none',
                placeholder="Order by (optional)",           
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),

            html.Div(
            apply_default_value(params)(dcc.Input)(
                id='timeframe',                    
                placeholder='Enter a value...',
                type='text',
                value='10',
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),

            html.Div(
            apply_default_value(params)(dcc.Input)(
                id='limit',                    
                placeholder='Enter a value...',
                type='text',
                value='300',
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
            dcc.Graph(
                id='example-graph',
                figure=fig
            ),
            html.Br(),
            html.H6('Table'),
            html.Table(
            # Header
            [html.Tr([html.Th(col) for col in columns])] +
            # Body
            [html.Tr([
                html.Td(
                    (df_row[x]),
                    style={'font-size':"12px"} # 'background-color':"lightblue"}
                    )
                for x in range(len(columns))
            ]) for df_row in df_list]),

        ], className="container")

        # print(str(datetime.timedelta(seconds=time.time() - functionstartTime))+' before printing')
    else:

        # PAGE 1: FIRST PAGE. NOTHING STARTED YET.
        layout = html.Div([
            
            html.H3('Recent Changes Diversity', style={'textAlign':'center'}),
            html.Br(),
            dcc.Markdown(text_default.replace('  ', '')),

            # HERE GOES THE INTERFACE
            # LINE 
            html.Br(),
            html.H5('Select the source'),

            interface_row1,
            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='lang',
                options=[{'label': i, 'value': language_names[i]} for i in sorted(language_names)],
                value='ca',
                placeholder="Select a source language",
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),
    #        dcc.Link('Query',href=""),

            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='editstype',
                options=[{'label': i, 'value': editstype_dict[i]} for i in editstype_dict],
                value='none',
                placeholder="Select the type of edits",           
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),

            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='editortype',
                options=[{'label': i, 'value': editortype_dict[i]} for i in editortype_dict],
                value='none',
                placeholder="Select the type of editors",           
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),


            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='diversitycategory',
                options=[{'label': i, 'value': diversitycategory_dict[i]} for i in diversitycategory_dict],
                value='none',
                placeholder="Select the type of editors",           
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),



            # LINE 
            html.Br(),
            interface_row2,
            html.Div(
            apply_default_value(params)(dcc.Dropdown)(
                id='orderby',
                options=[{'label': i, 'value': features_dict[i]} for i in sorted(features_dict)],
                value='none',
                placeholder="Order by (optional)",           
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),

            html.Div(
            apply_default_value(params)(dcc.Input)(
                id='timeframe',                    
                placeholder='Enter a value...',
                type='text',
                value='24',
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),

            html.Div(
            apply_default_value(params)(dcc.Input)(
                id='limit',                    
                placeholder='Enter a value...',
                type='text',
                value='500',
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),

            html.A(html.Button('Query Results!'),
                href=''),
           

        ], className="container")

    return layout





# callback update page layout
@dash_app18.callback(Output('page-content', 'children'),
              inputs=[Input('url', 'href')])
def page_load(href):
    if not href:
        return []
    state = parse_state(href)
    return dash_app18_build_layout(state)

# callback update URL
component_ids_app18 = ['lang','editstype', 'editortype','diversitycategory','orderby','timeframe','limit']
@dash_app18.callback(Output('url', 'search'),
              inputs=[Input(i, 'value') for i in component_ids_app18])
def update_url_state(*values):
    state = urlencode(dict(zip(component_ids_app18, values)))
    return '?'+state
#    return f'?{state}'

    
if __name__ == '__main__':
    dash_app18.run_server(debug=True)#,dev_tools_ui=False)
