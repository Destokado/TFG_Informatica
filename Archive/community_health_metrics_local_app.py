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
import numpy as np
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
    f = open(databases_path+'dict.txt','w')
    f.write(str(dic))
    f.close()

def load_dict_from_file():
    f = open(databases_path+'dict.txt','r')
    data=f.read()
    f.close()
    return eval(data)

##### RESOURCES GENERAL #####
title_addenda = ' - Wikipedia Diversity Observatory (WCDO)'

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

lang_groups = list()
lang_groups += ['Top 5','Top 10', 'Top 20', 'Top 30', 'Top 40']#, 'Top 50']
lang_groups += territories['region'].unique().tolist()
lang_groups += territories['subregion'].unique().tolist()

#wikipedialanguage_numberarticles = wikilanguages_utils.load_wikipedia_language_editions_numberofarticles(wikilanguagecodes,'')
#print (wikipedialanguage_numberarticles)
#save_dict_to_file(wikipedialanguage_numberarticles)
wikipedialanguage_numberarticles = load_dict_from_file()
for languagecode in wikilanguagecodes:
   if languagecode not in wikipedialanguage_numberarticles: wikilanguagecodes.remove(languagecode)

# --------------------------------------------------------------------------------------------



metric_name_dict = {"Monthly Edits": "monthly_edits", "Monthly Avg. Seconds Between Edits" : "monthly_average_seconds_between_edits", "Edit Count 24h after first edit" : "edit_count_24h", "Edit Count 7 days after first edit" : "edit_count_7d", "Edit Count 30 days after first edit" : "edit_count_30d", "Edit Count 60 days after first edit" : "edit_count_60d", "Edit Count in User Page 24h after first edit" : "user_page_edit_count_24h", "Edit Count in User Page 1 month after first edit" : "user_page_edit_count_1month", "Edit Count in User Page Talk Page 24h after first edit" : "user_page_talk_page_edit_count_24h", "Edit Count in User Page Talk Page 1 month after first edit" : "user_page_talk_page_edit_count_1month", "Edit Count ns0 Main" : "edit_count_ns0_main", "Edit Count ns1 Talk Pages" : "edit_count_ns1_talk", "Edit Count ns2 User Pages" : "edit_count_ns2_user", "Edit Count ns3 User Talk Pages" : "edit_count_ns3_user_talk", "Edit Count ns4 Project Pages" : "edit_count_ns4_project", "Edit Count ns5 Project Talk Pages" : "edit_count_ns5_project_talk", "Edit Count ns6 File Pages" : "edit_count_ns6_file", "Edit Count ns7 File Talk Pages" : "edit_count_ns7_file_talk", "Edit Count ns8 Mediawiki Pages" : "edit_count_ns8_mediawiki", "Edit Count ns9 Mediawiki Talk Pages" : "edit_count_ns9_mediawiki_talk", "Edit Count ns10 Template Pages" : "edit_count_ns10_template", "Edit Count ns11 Template Talk Pages" : "edit_count_ns11_template_talk", "Edit Count ns12 Help Pages" : "edit_count_ns12_help", "Edit Count ns13 Help Talk Pages" : "edit_count_ns13_help_talk", "Edit Count ns14 Category Pages" : "edit_count_ns14_category", "Edit Count ns15 Category Talk Pages" : "edit_count_ns15_category_talk", "Edit Count" : "edit_count", "Edit Count Bin" : "edit_count_bin", "Max. Inactive Months in a Row" : "max_inactive_months_row", "Total Active Months" : "active_months", "Total Months in Lifetime" : "total_months", "Months Since Last Edit" : "months_since_last_edit", "Inactive Periods" : "inactivity_periods", "Over Personal Personal Drop-off Thresold" : "over_personal_drop_off_threshold", "Personal Drop-off Threshold" : "personal_drop_off_threshold", "Over Edit Count Bin Drop-Off Threshold" : "over_edit_count_bin_drop_off_threshold"}

metric_name_dict_inv = {v: k for k, v in metric_name_dict.items()}


metric_names = list(metric_name_dict.keys())

 
#### ARTICLES DATA ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 

conn = sqlite3.connect(databases_path + 'community_health_metrics.db'); cursor = conn.cursor() # stats_prova_amb_indexs

query = 'SELECT distinct year_month FROM cawiki_editor_metrics;'
df = pd.read_sql_query(query, conn)
year_months = sorted(df.year_month.tolist(),reverse=True)
default_year_month = year_months[1]


# # PIVOT EXAMPLE

# languagecode = 'ca'
# names = ["Marcmiquel", "Toniher", "Kippelboy", "KRLS", "MuRe"]
# metrics = ["edit_count_24h", "edit_count_60d", "edit_count_ns2_user"]
# params = metrics+names

# query = 'SELECT user_name, metric_name, abs_value FROM '+languagecode+'wiki_editor_metrics WHERE metric_name IN ('+','.join( ['?'] * len(metrics) )+') AND user_name IN ('+','.join( ['?'] * len(names) )+');'
# df = pd.read_sql_query(query, conn, params = params)
# df = df.pivot(index='user_name', columns='metric_name')

# print (df.head(10))
# # b = df.pivot(index='user_name',columns='metric_name', values = 'abs_value')

# # IF I WANT TO PICK METRICS FROM cawiki_editors, I need to merge dataframes, but not do inner joins.


# metrics = ['user_flag','registration_date','survived60d','lifetime_days','days_since_last_edit']
# query = 'SELECT user_name, '+','.join(metrics)+' FROM '+languagecode+'wiki_editors WHERE user_name IN ('+','.join( ['?'] * len(names) )+');'
# df = pd.read_sql_query(query, conn, params = names)

# print (df.head(10))



languagecode = 'ca'

### --------------------------------------------------------------------------------

amical = ["Gomà","Josepnogue","Cdani","Paucabot","KRLS","Leptictidium","Vriullop","Pallares","Toniher","Mzamora2","RR","Barcelona","Enric","MuRe","Papapep","Góngora","SMP","Amadalvarez","Simonjoan","Imartin6","Aries","Xtv","Beusson","Castor","Dvdgmz","Arnaugir","Lilaroja","Pacopac","Jsalescabre","Pitxiquin","Mgclapé","Kippelboy","Ferrangb","Marcmiquel","Davidpar","Lluis tgn","Al Lemos","Laurita","Catgirl","Esenabre","MALLUS","F3RaN","Joan Subirats","Auró","Galazan","Coet","Antoni Salvà","Joancreus","Oriol Dubreuil","El Caro","ESM","Marionaaragay","QuimGil","Vàngelisvillar","Ivan bea","Tituscat","Docosong","Flamenc","Jey","Julià Minguillón","Pau Colominas","Unapersona","Anskar","Laura.Girona","Planvi","Medol","Marcoil","M.Angels Massip","Carles Riba","Dnogue","Guillem Nogué","Mikicat","FranSisPac","TaronjaSatsuma","Xavier Dengra","Gerardduenas","Tiputini","Quelet","Alibey","Townie","Eaibar","Llumeureka","Tsdgeos","Kette~cawiki","Mariusmm","19Tarrestnom65","B25es","Paputx","Nenagamba","Bgasco","Vallue","Dorieo","Amper2","Pere Orga","Xavier sistach","Julio Meneses","Joan Bover","Sorenike","Brinerustle","Ponscor","Jove","Ignacio.torres","Jordi G","Jlamadorjr","Josep Gibert","Departament de Matemàtiques UAB","Albertdg","AlbertRA","Xaviaranda","Galderich","Aniol","Voraviu","Unapeça"]
for x in ['Julio Meneses', 'M.Angels Massip', 'Joan Bover', 'Departament de Matemàtiques UAB', 'Joan Subirats', 'Guillem Nogué']: amical.remove(x)


# EDITORS CHARACTERISTICS AND METRICS (ACCUMULATED)

metrics = ["user_page_edit_count_1month", "user_page_edit_count_24h", "user_page_talk_page_edit_count_1month", "user_page_talk_page_edit_count_24h", "edit_count", "edit_count_24h", "edit_count_30d", "edit_count_60d", "edit_count_7d", "edit_count_bin", "edit_count_editor_user_page", "edit_count_editor_user_page_talk_page", "edit_count_edits_ns6_file", "edit_count_ns0_main", "edit_count_ns1_talk", "edit_count_ns2_user", "edit_count_ns3_user_talk", "edit_count_ns4_project", "edit_count_ns5_project_talk", "edit_count_ns7_file_talk", "edit_count_ns8_mediawiki", "edit_count_ns9_mediawiki_talk", "edit_count_ns10_template", "edit_count_ns11_template_talk", "edit_count_ns12_help", "edit_count_ns13_help_talk", "edit_count_ns14_category", "edit_count_ns15_category_talk", "inactivity_periods", "active_months", "max_active_months_row", "max_inactive_months_row", "months_since_last_edit", "total_months", "over_edit_count_bin_personal_drop_off_threshold", "over_personal_personal_drop_off_threshold", "personal_drop_off_threshold"]

query = 'SELECT user_name, user_id , metric_name, abs_value FROM '+languagecode+'wiki_editor_metrics WHERE metric_name IN ('+','.join( ['?'] * len(metrics) )+');'
df = pd.read_sql_query(query, conn, params = metrics)

df1 = df.pivot(index='user_name', columns='metric_name')
cols = []
for v in df1.columns.tolist(): cols.append(v[1]) 
df1.columns = cols

query = 'SELECT user_name, user_id, bot, user_flag, registration_date, year_month_registration, first_edit_timestamp, year_month_first_edit, survived60d, last_edit_timestamp, lifetime_days, days_since_last_edit, seconds_between_last_two_edits FROM '+languagecode+'wiki_editors;'
df2 = pd.read_sql_query(query, conn)
df2 = df2.set_index('user_name')
df3 = pd.concat([df1, df2], axis=1, sort=False)
df3['amical'] = 0
df3['amical'].loc[amical] = 1
df3 = df3.fillna(0)
df3.to_csv(databases_path + languagecode+'wiki_editors_characteristics_metrics_accumulated.csv')

print  (df3.head(10))
print ('end1')


### --------------------------------------------------------------------------------

# EDITORS CHARACTERISTICS AND METRICS (OVER TIME)
metrics = ["monthly_edits", "monthly_edits_ns0_main", "monthly_edits_ns10_template", "monthly_edits_ns11_template_talk", "monthly_edits_ns12_help", "monthly_edits_ns13_help_talk", "monthly_edits_ns14_category", "monthly_edits_ns15_category_talk", "monthly_edits_ns1_talk", "monthly_edits_ns2_user", "monthly_edits_ns3_user_talk", "monthly_edits_ns4_project", "monthly_edits_ns5_project_talk", "monthly_edits_ns6_file", "monthly_edits_ns7_file_talk", "monthly_edits_ns8_mediawiki", "monthly_edits_ns9_mediawiki_talk", "monthly_user_page_edit_count", "monthly_user_page_talk_page_edit_count", "monthly_average_seconds_between_edits"]
query = 'SELECT user_name, year_month, metric_name, abs_value FROM '+languagecode+'wiki_editor_metrics WHERE metric_name IN ('+','.join( ['?'] * len(metrics) )+');'


df = pd.read_sql_query(query, conn, params = metrics)
df1 = pd.pivot_table(df, index=['year_month','user_name'], columns='metric_name', values = 'abs_value')
df1 = df1.reset_index()

df1 = df1.set_index('user_name')
df1['amical'] = 0
df1['amical'].loc[amical] = 1
df1 = df1.fillna(0)
df1.to_csv(databases_path + languagecode+'wiki_editors_characteristics_metrics_over_time.csv')

print  (df1.head(10))
print ('end2')


### --------------------------------------------------------------------------------

# COMMUNITY METRICS (OVER TIME)
query = 'SELECT metric_name, abs_value, year_month FROM '+languagecode+'wiki_community_metrics'
df = pd.read_sql_query(query, conn)
df1 = df.pivot(index='year_month', columns='metric_name')

cols = []
for v in df1.columns.tolist(): cols.append(v[1]) 
df1.columns = cols

df1 = df1.fillna(0)
df1.to_csv(databases_path + languagecode+'wiki_community_metrics.csv')

print  (df1.head(10))
print ('end3')
input('')



###############################################################################################


### DASH APP ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 

# dash_app13 = Dash(__name__, server = app, url_base_pathname= webtype + '/diversity_over_time/', external_stylesheets=external_stylesheets, external_scripts=external_scripts)
dash_app13 = Dash()
dash_app13.config['suppress_callback_exceptions']=True



title = "Wikipedia Community Health"
dash_app13.title = title+title_addenda
text_heatmap = ''

dash_app13.layout = html.Div([
#    navbar,
    html.H3(title, style={'textAlign':'center'}),
    dcc.Markdown('''
        This page shows stastistics and graphs that explain Wikipedia Community Health.
       '''),
    html.Br(),

# ###

    dcc.Tabs([

# --------------------------------------------------------------------------------------------

        dcc.Tab(label='Editor Engagement', children=[

            # 1 EDITOR ENGAGEMENT TREEMAP AND TABLE
            html.Br(),

            html.Div(
            html.P('Select a Wikipedia'),
            style={'display': 'inline-block','width': '200px'}),

            html.Div(
            html.P('Select Metric'),
            style={'display': 'inline-block','width': '250px'}),

            html.Div(
            html.P('Select a year and month'),
            style={'display': 'inline-block','width': '200px'}),


            html.Br(),
            html.Div(
            dcc.Dropdown(
                id='lang_dropdown_treemap',
                options = [{'label': k, 'value': k} for k in language_names_list],
                value = 'Catalan (ca)',
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),

            html.Div(
            dcc.Dropdown(
                id='metric_names_treemap',
                options = [{'label': k, 'value': k} for k in metric_names],
                value = 'Edit Count 24h after first edit',
                style={'width': '240px'}
             ), style={'display': 'inline-block','width': '250px'}),

            html.Div(
            dcc.Dropdown(
                id='time_aggregation_treemap',
                options = [{'label': k, 'value': k} for k in year_months],
                value = None, # default_year_month
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),


            dcc.Graph(id = 'specificmonth_treemap'),
            #html.Hr(),

        ]),

# --------------------------------------------------------------------------------------------




        # dcc.Tab(label='Community Health', children=[

        #     # 2 OVER TIME TIME SERIES
        #     html.Br(),

        #     html.Div(
        #     html.P('Select a group of Wikipedias'),
        #     style={'display': 'inline-block','width': '200px'}),

        #     html.Div(
        #     html.P('You can add or remove languages:'),
        #     style={'display': 'inline-block','width': '500px'}),

        #     html.Br(),

        #     html.Div(
        #     dcc.Dropdown(
        #         id='langgroup_dropdown_timeseries',
        #         options = [{'label': k, 'value': k} for k in lang_groups],
        #         disabled =False,
        #         style={'width': '190px'}
        #      ), style={'display': 'inline-block','width': '200px'}),

        #     html.Div(
        #     dcc.Dropdown(
        #         id='langgroup_box_timeseries',
        #         options = [{'label': k, 'value': k} for k in language_names_list],
        #         value = 'English (en)',
        #         multi=False,
        #         style={'width': '790px'}
        #      ), style={'display': 'inline-block','width': '800px'}),

        #     html.Br(),

        #     html.Div(
        #     html.P('Select a Metric names'),
        #     style={'display': 'inline-block','width': '200px'}),

        #     html.Div(
        #     html.P('You can add or remove metrics:'),
        #     style={'display': 'inline-block','width': '500px'}),
        #     html.Br(),



        #     html.Div(
        #     dcc.Dropdown(
        #         id='metric_names_timeseries',
        #         options = [{'label': k, 'value': k} for k in ['Entire Wikipedia']+metric_names],
        #         value = 'Regions',
        #         style={'width': '190px'}
        #      ), style={'display': 'inline-block','width': '200px'}),

        #     html.Div(
        #     dcc.Dropdown(
        #         id='metrics_box_timeseries',
        #         options = [{'label': k, 'value': j} for k,j in metrics_list],
        #         multi=True,
        #         style={'width': '790px'}
        #      ), style={'display': 'inline-block','width': '800px'}),
        #     html.Br(),

        #     html.Div(
        #     html.P('Show absolute or relative values'),
        #     style={'display': 'inline-block','width': '210px'}),

        #     html.Div(
        #     html.P('Compare metrics in language / metrics by language'),
        #     style={'display': 'inline-block','width': '400px'}),

        #     html.Br(),

        #     html.Div(
        #     dcc.RadioItems(
        #         id='show_absolute_relative_radio_timeseries',
        #         options=[{'label':'Absolute','value':'Absolute'},{'label':'Relative','value':'Relative'}],
        #         value='Absolute',
        #         labelStyle={'display': 'inline-block', "margin": "0px 5px 0px 0px"},
        #         style={'width': '200px'}
        #      ), style={'display': 'inline-block','width': '210px'}),

        #     html.Div(
        #     dcc.RadioItems(
        #         id='show_compare_timeseries',
        #         options=[{'label':'Limit 1 language','value':'1Language'},{'label':'Limit 1 metric','value':'1metric'}],
        #         value='1Language',
        #         labelStyle={'display': 'inline-block', "margin": "0px 5px 0px 0px"},
        #         style={'width': '390px'}
        #      ), style={'display': 'inline-block','width': '400px'}),

        #     html.Br(),

        #     dcc.Graph(id = 'monthly_timeseries1'),
        #     dcc.Graph(id = 'monthly_timeseries2'),


        #     dcc.Markdown('''The time series / line chart graphs shows for a group of selected Wikipedia language editions and for specific metrics their value over time. The graphs allow selecting either one Wikipedia language edition and more than one metric from a Metric names or one single metric from a Metric names and more than one Wikipedia language edition in order to compare them over time.

        #     Time is presented in the x-axis and it is possible to select the year_months in which articles are aggregated (Yearly, Quarterly and Monthly). The lines can be presented in the y-axis as a result of the number of aggregated articles for that year_month of time or the extent they take according to the total created or accumulated articles for that Metric names. The graph contains a range-slider on the bottom to select a specific year_month of time especially useful when the time aggreation is set to quarterly. It is possible to use predefined specific time selections by clicking on the labels 6M, 1Y, 5Y, 10Y and ALL (last six months, last year, last five years, last ten years and all the time). The graph provides additional information on each point by hovering as well as it allows selecting a specific language and exclude the rest by clicking on it on the legend.
        #      '''.replace('  ', '')),


        #     ]),

# --------------------------------------------------------------------------------------------

    ]),

#    footbar,

], className="container")

### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###



#### FUNCTIONS AND CALLBACKS ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 

# TREEMAP
@dash_app13.callback(
    Output('specificmonth_treemap', 'figure'),
    [Input('lang_dropdown_treemap', 'value'), Input('metric_names_treemap', 'value'), Input('time_aggregation_treemap', 'value')])
def update_specific_month_treemap(language, metric_name_size1, year_month):

    conn = sqlite3.connect(databases_path + 'community_health_metrics.db'); cursor = conn.cursor()

    try:
        language = language_names[language]
    except:
        language = None


    if language != None and metric_name_size1 != None: 

        metric_name_size1_real = metric_name_dict[metric_name_size1]

        query = 'SELECT user_name as Editor, abs_value, rel_value, metric_name as Metric, year_month FROM '+language+'wiki_editor_metrics WHERE metric_name IN ("'+metric_name_size1_real+'") '

        if year_month != None:
            query += 'AND year_month = "'+year_month+'"'
    

        query += ' ORDER BY abs_value DESC limit 100;'




        print (query)
        df = pd.read_sql_query(query, conn).round(1)
        df = df.replace({'Metric':metric_name_dict_inv})

        print (df.head(10))
        print (len(df))



    """ Aquí s'hauria d'agafar el nombre d'elements per fer el 90% i el 10% restant ajuntar-los com a others """

    """ S'hauria de fer una interfície perquè es pogués limitar el nombre d'editors en funció d'unes característiques i condicions de cawiki_editors """


    """ S'hauria de fer una interfície que permetés seleccionar un límit d'editors """


    fig = go.Figure()
    fig = make_subplots(
        cols = 2, rows = 1,
        column_widths = [0.45, 0.45],
#        subplot_titles = ('Accumulated Articles'+'<br />&nbsp;<br />', 'Created Articles'+'<br />&nbsp;<br />'),
        specs = [[{'type': 'treemap', 'rowspan': 1}, {'type': 'treemap'}]])


    parents = list()
    for x in df.index:
        parents.append('')

    # parents2 = list()
    # for x in df.index:
    #     parents2.append('')

    fig.add_trace(go.Treemap(
        parents = parents,
        labels = df['Editor'],
        values = df['abs_value'],
        customdata = df['abs_value'],
        text = df['Metric'],
        texttemplate = "<b>%{label} </b><br>%{text}: %{value}<br>",
        hovertemplate='<b>%{label} </b><br>%{text}: %{value}<extra></extra>',
        ),
            row=1, col=1)



    # fig.add_trace(go.Treemap(
    #     parents = parents,
    #     labels = df['user_name'],
    #     values = df['abs_value'],
    #     # customdata = df['abs_value'],
    #     # text = df['metric_name'],
    #     texttemplate = "<b>%{label} </b><br>"+metric_name_size1+": %{customdata}%<br>Articles: %{value}<br>",
    #     hovertemplate='<b>%{label} </b><br>'+metric_name_size1+': %{customdata}%<br>Articles: %{value}<br>%{text}<br><extra></extra>',
    #     ),
    #         row=1, col=2)

    extra = ""


    fig.update_layout(
        autosize=True,
#        width=700,
        height=900,
        title_font_size=12,
        title_text="X (Left) and X (Right)"+extra,
        title_x=0.5,
    )

    return fig

########################








"""




def create_fig_timeseries(created_accumulated, df, metric_name, absolute_relative):
    fig = go.Figure()

    if absolute_relative == 'Absolute':
        customdata = 'Extent Articles (%)'
        y = 'Articles'
        hovertemplate_extent = '<br>Extent Articles: %{customdata}%'
        hovertemplate_articles = '<br>Articles: %{y}'
        yaxis = 'Number of Articles ' + created_accumulated
    else:
        customdata = 'Articles'
        y = 'Extent Articles (%)'
        hovertemplate_extent = '<br>Extent Articles: %{y}%'
        hovertemplate_articles = '<br>Articles: %{customdata}'
        yaxis = 'Percentage of Articles ' + created_accumulated

    fig = go.Figure()
    for metric_name in list(df["metric (Wiki)"].unique()):
#        print (metric_name)
        d = df.loc[(df["metric (Wiki)"] == metric_name)]

        fig.add_trace(go.Scatter(
            customdata=d[customdata],
            y = d[y],
            x=d['year_month'],
            name=metric_name,
            hovertemplate=str(metric_name)+hovertemplate_articles+hovertemplate_extent+'<br>year_month: %{x}<br><extra></extra>'
        ))

    fig.update_layout(
        xaxis=dict(
            title='Time (Monthly)',
            titlefont_size=18,
            tickfont_size=16,

            rangeselector=dict(
                buttons=list([
                    dict(count=6,
                         label="6m",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="1y",
                         step="year",
                         stepmode="backward"),
                    dict(count=5,
                         label="5y",
                         step="year",
                         stepmode="backward"),
                    dict(count=10,
                         label="10y",
                         step="year",
                         stepmode="backward"),
                    dict(step="all")
                        ])
                    ),
                    rangeslider=dict(
                        visible=False
                    ),
                    type="date"

        ),
        yaxis=dict(
            title=yaxis,
            titlefont_size=16,
            tickfont_size=14,
        ),

        title_font_size=18,
        title_text=created_accumulated+' Articles on '+metric_name,
        legend = dict(
            font=dict(
#                family="sans-serif",
                size=14
#                color="black"
            ),
            traceorder="normal"
            ),
        autosize=True,
        height = 450,
        width=800)

    return fig


# MONTHLY TIME SERIES
@dash_app13.callback(
    [Output('monthly_timeseries1', 'figure'), Output('monthly_timeseries2', 'figure')],
    [Input('langgroup_box_timeseries', 'value'),
    Input('metric_names_timeseries', 'value'), 
    Input('metrics_box_timeseries', 'value'), 
    Input('show_absolute_relative_radio_timeseries','value')])
def update_monthly_time_series(languages, metric_name, metrics, absolute_relative):

    if metrics == None:
        metrics = []
    if languages == None:
        languages = []

#    print (languages, metric_name, metrics, absolute_relative, 'update_monthly_time_series')
    langs = []
    if type(languages) != str:
        for x in languages: langs.append(language_names[x])
    else:
        langs.append(language_names[languages])

    ents = []
    if type(metrics) != str:
        try:
            for x in metrics: ents.append(language_name_wiki[x])
        except:
            ents = metrics
    else:
        try:
            ents = [language_name_wiki[metrics]]
        except:
            ents = [metrics]



    ct = metric_name_dict[metric_name]
    conn = sqlite3.connect(databases_path + 'editor_engagement.db'); cursor = conn.cursor() #

    query, params = params_to_df(langs, ct, None, 'monthly')
    df_created = pd.read_sql_query(query, conn, params = params).round(1)
    df_created = df_extended(df_created, ct)

    query, params = params_to_df(langs, ct, None, 'accumulated')
    df_accumulated = pd.read_sql_query(query, conn, params = params).round(1)
    df_accumulated = df_extended(df_accumulated, ct)

    # # ACCUMULATED
    # df_accumulated = pd.DataFrame()
    # df_accumulated = df_accumulated_dict[metric_name]
    # df_accumulated = df_accumulated.loc[(df_accumulated['Wiki'].isin(langs)) & (df_accumulated['metric'].isin(ents))]
    df_accumulated = df_accumulated.loc[(df_accumulated['metric'].isin(ents))]

    # # CREATED
    # df_created = pd.DataFrame()
    # df_created = df_created_dict[metric_name]
    # df_created = df_created.loc[(df_created['Wiki'].isin(langs)) & (df_created['metric'].isin(ents))]
    df_created = df_created.loc[(df_created['metric'].isin(ents))]

    df_accumulated["metric (Wiki)"] = df_accumulated["metric"]+" ("+df_accumulated["Wiki"]+")"
    df_created["metric (Wiki)"] = df_created["metric"]+" ("+df_created["Wiki"]+")"

    fig = create_fig_timeseries('Accumulated', df_accumulated, metric_name, absolute_relative)
    fig2 = create_fig_timeseries('Created', df_created, metric_name, absolute_relative)

    return fig, fig2


########################


# Enable metrics options
# Dropdown metrics
def metrics_group_options(selected_group):

    if selected_group == 'Countries': metrics_list = country_names_inv

    if selected_group == 'Subregions': metrics_list = subregions_dict

    if selected_group == 'Regions': metrics_list = regions_dict

    if selected_group == 'Languages CCC': metrics_list = language_names

    if selected_group == 'Top CCC Lists': metrics_list = lists_dict

    if selected_group == 'Gender': metrics_list = people_dict

    if selected_group == 'Entire Wikipedia': metrics_list = {'Entire Wikipedia':'Entire Wikipedia'}

    if len(metrics_list) <= 10:
        selected_metrics = random.sample(list(metrics_list.keys()),len(metrics_list))
    else:
        selected_metrics = []

    if len(metrics_list) > 9:
        sample = 9
    else:
        sample = len(metrics_list)

    if selected_group != None:
        selected_metrics = random.sample(list(metrics_list.keys()),sample)
    else:
        selected_metrics = []

    metrics_list = [{'label': k, 'value': k} for k,j in metrics_list.items()]

    return metrics_list, selected_metrics


@dash_app13.callback(
    [Output('metrics_box_timeseries', 'options'),
    Output('metrics_box_timeseries', 'value')],
    [Input('metric_names_timeseries', 'value'),
    Input('show_compare_timeseries','value')
    ])
def set_metrics_group_options_given_timeseries(selected_group, compare):
    metrics_list, selected_metrics = metrics_group_options(selected_group)




    print (metrics_list, selected_metrics)
    print (compare)
    if compare == '1metric': selected_metrics = []

    return metrics_list, selected_metrics


# Dropdown languages and metrics
@dash_app13.callback(
    [Output('langgroup_box_timeseries','multi'), 
    Output('metrics_box_timeseries','multi'),
    Output('langgroup_dropdown_timeseries', 'value'),
    Output('langgroup_dropdown_timeseries', 'disabled')
    ],
    [Input('show_compare_timeseries','value')])
def limit_langs_metrics(compare):

    if compare == '1Language':
        languages = False
        metrics = True
        group_disabled = True
    else:
        metrics = False
        languages = True
        group_disabled = False

    return (languages,metrics,[],group_disabled)


# Dropdown languages
@dash_app13.callback(
    Output('langgroup_box_timeseries', 'value'),
    [Input('langgroup_dropdown_timeseries', 'value'), 
    Input('show_compare_timeseries','value')])
def set_langs_group_options_time_series(selected_group, compare):

#    print (selected_group, compare, 'set_langs_group_options_time_series')
    if compare == '1Language':
        return []

    if compare == '1metric' and selected_group != None and len(selected_group)!=0:
        langolist, langlistnames = wikilanguages_utils.get_langs_group(selected_group, None, None, None, wikipedialanguage_numberarticles, territories, languages)
        available_options = [{'label': i, 'value': i} for i in langlistnames.keys()]
        list_options = []
        for item in available_options: list_options.append(item['label'])

        return sorted(list_options,reverse=False)
#        return ['Catalan (ca)','French (fr)', 'German (de)', 'Italian (it)', 'Polish (pl)']





"""







# ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

if __name__ == '__main__':
    dash_app13.run_server(debug=True)