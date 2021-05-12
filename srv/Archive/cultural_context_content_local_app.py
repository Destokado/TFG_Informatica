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



def save_dict_to_file(dic):
    f = open('databases/'+'dict.txt','w')
    f.write(str(dic))
    f.close()

def load_dict_from_file():
    f = open('databases/'+'dict.txt','r')
    data=f.read()
    f.close()
    return eval(data)


last_period = '2020-05'

##### RESOURCES GENERAL #####
title_addenda = ' - Wikipedia Diversity Observatory (WDO)'

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

# wikipedialanguage_numberarticles = wikilanguages_utils.load_wikipedia_language_editions_numberofarticles(wikilanguagecodes,'')
# print (wikipedialanguage_numberarticles)
# save_dict_to_file(wikipedialanguage_numberarticles) # using this is faster than querying the database for the number of articles in each table.
wikipedialanguage_numberarticles = load_dict_from_file()
for languagecode in wikilanguagecodes:
   if languagecode not in wikipedialanguage_numberarticles: wikilanguagecodes.remove(languagecode)




### DATA ###

# source_lang = 'en'

# conn = sqlite3.connect(databases_path + 'stats.db'); cursor = conn.cursor()

# # Coverage of other languages CCC by Arabic Wikipedia
# # set1, set1descriptor, set2, set2descriptor
# # set1 (all languages), wp, ccc, wp
# # CCC
# query = 'SELECT set1 as languagecode, set2descriptor as Qitem, abs_value as CCC_articles, ROUND(rel_value,2) CCC_percent FROM wdo_intersections_accumulated WHERE set1descriptor = "ccc" AND set2 = "ccc" AND content = "articles" AND period IN (SELECT MAX(period) FROM wdo_intersections_accumulated) ORDER BY set1, set2descriptor DESC;'
# df1 = pd.read_sql_query(query, conn)


# dfx = df1[['languagecode','Qitem','CCC_articles','CCC_percent']]

# columns = ['territoryname','territorynameNative','country','ISO3166','ISO31662','subregion','region']
# territoriesx = list()
# for index in dfx.index.values:
#     qitem = dfx.loc[index]['Qitem']
#     languagecode = dfx.loc[index]['languagecode']
#     languagename = languages.loc[languagecode]['languagename']
#     current = []
#     try:
#         current = territories.loc[territories['QitemTerritory'] == qitem].loc[languagecode][columns].values.tolist()
#         current.append(languagename)
#     except:
#         current = ['Not Assigned',None,None,None,None,None,None,languagename]
#         pass
#     territoriesx.append(current)
# columns.append('languagename')
# all_territories = pd.DataFrame.from_records(territoriesx, columns=columns)

# df = pd.concat([dfx, all_territories], axis=1)

# # columns_dict = {'languagename':'Language','languagecode':'Wiki','Qitem':'Qitem','CCC_articles':'CCC art.','CCC_percent':'CCC %','CCC_articles_GL':'CCC GL art.','CCC_percent_GL':'CCC GL %','CCC_articles_KW':'CCC art. KW','CCC_percent_KW':'CCC KW %','territoryname':'Territory name','territorynameNative':'Territory name (native)','country':'country','ISO3166':'ISO3166','ISO31662':'ISO3166-2','subregion':'subregion','region':'region'}
# # df=df.rename(columns=columns_dict)

# df = df.set_index('languagecode')
# df = df.loc[source_lang]

# labels = df.territoryname.tolist()
# values = df.CCC_percent.tolist()
# values = df.CCC_articles.tolist()






#### CCC DATA
conn = sqlite3.connect(databases_path + 'stats.db'); cursor = conn.cursor()

df = pd.DataFrame(wikilanguagecodes)
df = df.set_index(0)
reformatted_wp_numberarticles = {}
df['wp_number_articles']= pd.Series(wikipedialanguage_numberarticles)

# CCC %
query = 'SELECT set1, abs_value, rel_value FROM wdo_intersections_accumulated WHERE set1descriptor = "wp" AND set2descriptor = "ccc" AND content = "articles" AND set1=set2 AND period ="'+last_period+'" ORDER BY abs_value DESC;'
rank_dict = {}; i=1
lang_dict = {}
abs_rel_value_dict = {}
abs_value_dict = {}
for row in cursor.execute(query):
    lang_dict[row[0]]=languages.loc[row[0]]['languagename']
    abs_rel_value_dict[row[0]]=round(row[2],2)
    abs_value_dict[row[0]]=int(row[1])
    rank_dict[row[0]]=i
    i=i+1  
df['Language'] = pd.Series(lang_dict)
df['Nº'] = pd.Series(rank_dict)

df['ccc_percent'] = pd.Series(abs_rel_value_dict)
df['ccc_number_articles'] = pd.Series(abs_value_dict)

df['Continent']=languages.region
for x in df.index.values.tolist():
    try:
        if ';' in df.loc[x]['Continent']: df.at[x, 'Continent'] = df.loc[x]['Continent'].split(';')[0]
    except:
        print (x+' ccc test.')


df['Subcontinent']=languages.subregion
for x in df.index.values.tolist():
    if ';' in df.loc[x]['Subcontinent']: df.at[x, 'Subcontinent'] = df.loc[x]['Subcontinent'].split(';')[0]


# CCC (GL %) 
query = 'SELECT set1, abs_value, rel_value FROM wdo_intersections_accumulated WHERE set1descriptor = "ccc" AND set2descriptor = "ccc_geolocated" AND content = "articles" AND set1=set2 AND period ="'+last_period+'" ORDER BY rel_value DESC;'
abs_rel_value_dict = {}
for row in cursor.execute(query): abs_rel_value_dict[row[0]]= round(row[2],2)# ' '+str('{:,}'.format(int(row[1]))+' '+'<small>('+str(round(row[2],2))+'%)</small>')
df['geolocated_number_articles'] = pd.Series(abs_rel_value_dict)

# CCC KW %
query = 'SELECT set1, abs_value, rel_value FROM wdo_intersections_accumulated WHERE set1descriptor = "ccc" AND set2descriptor = "ccc_keywords" AND content = "articles" AND set1=set2 AND period ="'+last_period+'" ORDER BY rel_value DESC;'
abs_rel_value_dict = {}
for row in cursor.execute(query):
    abs_rel_value_dict[row[0]]= round(row[2],2)#' '+str('{:,}'.format(int(row[1]))+' '+'<small>('+str(round(row[2],2))+'%)</small>')
df['keyword_title'] = pd.Series(abs_rel_value_dict)

# CCC People %
query = 'SELECT set1, abs_value, rel_value FROM wdo_intersections_accumulated WHERE set1descriptor = "wp" AND set2descriptor = "ccc_people" AND content = "articles" AND set1=set2 AND period ="'+last_period+'" ORDER BY rel_value DESC;'
abs_rel_value_dict = {}
for row in cursor.execute(query):
    abs_rel_value_dict[row[0]]= round(row[2],2)#' '+str('{:,}'.format(int(row[1]))+' '+'<small>('+str(round(row[2],2))+'%)</small>')
df['people_ccc_wp_percent'] = pd.Series(abs_rel_value_dict)

# CCC Female %
query = 'SELECT set1, abs_value, rel_value FROM wdo_intersections_accumulated WHERE set1descriptor = "ccc" AND set2descriptor = "female" AND content = "articles" AND set1=set2  AND period ="'+last_period+'" ORDER BY rel_value DESC;'
female_abs_value_dict = {}
for row in cursor.execute(query):
    female_abs_value_dict[row[0]]=row[1]
df['female_ccc'] = pd.Series(female_abs_value_dict)

# CCC Male %
query = 'SELECT set1, abs_value, rel_value FROM wdo_intersections_accumulated WHERE set1descriptor = "ccc" AND set2descriptor = "male" AND content = "articles" AND set1=set2 AND period ="'+last_period+'" ORDER BY rel_value DESC'
male_abs_value_dict = {}
for row in cursor.execute(query):
    male_abs_value_dict[row[0]]=row[1]
df['male_ccc'] = pd.Series(male_abs_value_dict)


people_CCC = {}
female_male_CCC={}
for x in df.index.values.tolist():
    fccc = 0
    mccc = 0
    mccc = df.loc[x]['male_ccc']

    try:
        mccc = df.loc[x]['male_ccc']
    except:
        mccc = 0

#    fccc = df.loc[x]['female_ccc']
    try:
        fccc = df.loc[x]['female_ccc']
    except:
        fccc = 0

#    print (mccc,fccc)
    sumpeople = mccc+fccc
#    print (sumpeople)

    try:
        female_male_CCC[x] = round(100*int(fccc)/sumpeople,1)
    except:
        female_male_CCC[x] = 0

    try:
        people_CCC[x] = round(100*float(sumpeople/df.loc[x]['ccc_number_articles']),1)
    except:
        people_CCC[x] = 0

df['female-male_ccc'] = pd.Series(female_male_CCC)
df['people_ccc_percent'] = pd.Series(people_CCC)



columns_dict = {'wp_number_articles':'Articles','ccc_number_articles':'CCC art.','ccc_percent':'CCC %','geolocated_number_articles':'CCC (GL %)','keyword_title':'CCC (KW Title %)','female-male_ccc':'CCC People (Women %)','people_ccc_percent':'CCC (People %)'}
df = df.rename(columns=columns_dict)
df = df.reset_index()

df = df.rename(columns={0: 'Wiki'})
df = df.rename(columns=columns_dict)

df = df.fillna('')

df['id'] = df['Language']
df.set_index('id', inplace=True, drop=False)

df = df.fillna('')

columns = ['Nº','Language','Wiki','Articles','CCC art.','CCC %','CCC (GL %)','CCC (KW Title %)','CCC (People %)','CCC People (Women %)','Subcontinent','Continent']
df = df[columns] # selecting the parameters to export
df = df.loc[(df['Language']!='')]

df = df.sort_values(by=['CCC art.'], ascending = False)

df['CCC %'] = pd.to_numeric(df['CCC %'])

bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100] 
df['CCC % bins'] = pd.cut(df['CCC %'], bins) 



#### TERRITORIES CCC DATA
# CCC
query = 'SELECT set1 || " " || set2descriptor as id, set1 as languagecode, set2descriptor as Qitem, abs_value as CCC_articles, ROUND(rel_value,2) CCC_percent FROM wdo_intersections_accumulated WHERE set1descriptor = "ccc" AND set2 = "ccc" AND content = "articles" AND period ="'+last_period+'" ORDER BY set1, set2descriptor DESC;'
df1 = pd.read_sql_query(query, conn)
df1 = df1.set_index('id')

# GL
query = 'SELECT set1 || " " || set2descriptor as id, set1 as languagecode2, set2descriptor as Qitem2, abs_value as CCC_articles_GL, ROUND(rel_value,2) CCC_percent_GL FROM wdo_intersections_accumulated WHERE set1descriptor = "ccc" AND set2 = "ccc_geolocated" AND content = "articles" AND period ="'+last_period+'" ORDER BY set1, set2descriptor DESC;'
df2 = pd.read_sql_query(query, conn)
df2 = df2.set_index('id')

# KW
query = 'SELECT set1 || " " || set2descriptor as id, set1 as languagecode3, set2descriptor as Qitem3, abs_value as CCC_articles_KW, ROUND(rel_value,2) CCC_percent_KW FROM wdo_intersections_accumulated WHERE set1descriptor = "ccc" AND set2 = "ccc_keywords" AND content = "articles" AND period ="'+last_period+'" ORDER BY set1, set2descriptor DESC;'
df3 = pd.read_sql_query(query, conn)
df3 = df3.set_index('id')

dfx = pd.concat([df1, df3, df2], axis=1, sort=True)

dfx = dfx.fillna('')
dfx = dfx.reset_index()

dfx = dfx[['languagecode','Qitem','CCC_articles','CCC_percent','CCC_articles_GL','CCC_percent_GL','CCC_articles_KW','CCC_percent_KW']]

columns = ['territoryname','territorynameNative','country','ISO3166','ISO31662','subregion','region']
territoriesx = list()
for index in dfx.index.values:
    qitem = dfx.loc[index]['Qitem']
    languagecode = dfx.loc[index]['languagecode']
    languagename = languages.loc[languagecode]['languagename']
    current = []
    try:
        current = territories.loc[territories['QitemTerritory'] == qitem].loc[languagecode][columns].values.tolist()
        current.append(languagename)
    except:
        current = ['Not Assigned',None,None,None,None,None,None,languagename]
        pass
    territoriesx.append(current)
columns.append('languagename')
all_territories = pd.DataFrame.from_records(territoriesx, columns=columns)

df_territories = pd.concat([dfx, all_territories], axis=1, sort=True)



columns_dict = {'languagename':'Language','languagecode':'Wiki','Qitem':'Qitem','CCC_articles':'CCC art.','CCC_percent':'CCC %','CCC_articles_GL':'CCC GL art.','CCC_percent_GL':'CCC (GL %)','CCC_percent_KW':'CCC (KW %)', 'CCC_articles_KW':'CCC art. KW','territoryname':'Territory name','territorynameNative':'Territory name (native)','country':'country','ISO3166':'ISO3166','ISO31662':'ISO3166-2','subregion':'Subcontinent','region':'Continent'}
df_territories=df_territories.rename(columns=columns_dict)


columns_territory = ['Qitem','Territory name','Language','Wiki','CCC art.','CCC %','CCC GL art.','CCC (KW %)','ISO3166','ISO3166-2','Subcontinent','Continent']
df_territories = df_territories[columns_territory]
df_territories = df_territories.fillna('')
df_territories['Territory name wiki'] = df_territories['Territory name']+' ('+df_territories['Wiki']+')'
dft = df_territories




### CCC OVERLAP
query = 'SELECT set1, set2, abs_value, rel_value, period FROM wdo_intersections_accumulated WHERE content="articles" AND set1descriptor="ccc" AND set2descriptor = "ccc" AND period IN (SELECT MAX(period) FROM wdo_intersections_accumulated) AND rel_value > 5 AND abs_value > 10 ORDER BY set1, abs_value DESC;'
df_overlap = pd.read_sql_query(query, conn)

columns_dict = {'set1':'Language CCC', 'set2': 'Overlapping Language CCC', 'abs_value':'Articles', 'rel_value':'Overlapped CCC %'}
df_overlap = df_overlap.rename(columns=columns_dict)


print ('data loaded.')




### DASH APP ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 
dash_app = Dash()
dash_app.config['suppress_callback_exceptions']=True

title = "Wikipedia Language Editions' CCC"
dash_app.title = title+title_addenda
text_treemap_territories = ''

dash_app.layout = html.Div([
        html.H3(title, style={'textAlign':'center'}),

        

        html.H5('Treemap'),

        dcc.Dropdown(
            id='source_lang',
            options=[{'label': i, 'value': language_names[i]} for i in sorted(language_names)],
            value='en',
            placeholder="Select a source language",           
            style={'width': '190'}
         ),
        dcc.Graph(id = 'treemap_territories'),


        html.H5('Scatterplot'),
        dcc.Graph(id = 'scatterplot'),


        html.H5('Barchart'),
        dcc.Graph(id = 'barchart'),

        html.H5('Barchart2'),
        dcc.Graph(id = 'barchart2'),

        dcc.Graph(id = 'scattermapbox'),


    ])



# TREEMAP_territories
@dash_app.callback(
    Output('treemap_territories', 'figure'),
    [Input('source_lang', 'value')])
def update_treemap_territories(value):
    source_lang = value

    # values = ["11", "12", "13", "14", "15", "20", "30"]
    # labels = ["A1", "A2", "A3", "A4", "A5", "B1", "B2"]

    # print (value)
    # print (df_territories.columns.tolist())
    # print (df_territories.head(10))


    # labels = dft.territoryname.tolist()
    # values = dft.CCC_percent.tolist()
    # values = dft.CCC_articles.tolist()


    # parents = list()
    # for x in labels:
    #     parents.append('')

    fig = px.treemap(
        dft.set_index('Wiki').loc[source_lang],
        labels = 'territoryname',
        values = 'CCC_percent',
        parents = 'CCC_articles',
        textinfo = "label+value+percent entry",
        color_continuous_scale='RdBu')

    return fig



# scatterplot
@dash_app.callback(
    Output('scatterplot', 'figure'),
    [Input('source_lang', 'value')])
def update_scatterplot(value):

    # print (dft.head(10))
    source_lang = value

    # values = ["11", "12", "13", "14", "15", "20", "30"]
    # labels = ["A1", "A2", "A3", "A4", "A5", "B1", "B2"]
    fig = px.scatter(df, x="CCC %", y="Articles", color="Continent",
                 size='CCC %',log_y=True,text="Language", hover_data=['Language'])

    fig.update_traces(textposition='top center')

    return fig



# barchart
@dash_app.callback(
    Output('barchart', 'figure'),
    [Input('source_lang', 'value')])
def update_barchart(value):

    fig = px.bar(df, x="Language", y="CCC % bins", color="medal", title="CCC Buckets")

    return fig


# barchart
@dash_app.callback(
    Output('barchart2', 'figure'),
    [Input('source_lang', 'value')])
def update_barchart2(value):

    fig = px.bar(df_overlap, x="Language CCC", y="Overlapped CCC %", color="Overlapping Language CCC", title="CCC Overlapped")

    return fig


# scattermapbox
@dash_app.callback(
    Output('scattermapbox', 'figure'),
    [Input('source_lang', 'value')])
def update_scattermapbox(value):
    source_lang = value

    conn2 = sqlite3.connect(databases_path + 'wikipedia_diversity.db'); cursor2 = conn2.cursor() 

    query = "SELECT geocoordinates, ISO3166, REPLACE(page_title,'_', ' ') as page_title, num_edits, num_editors, num_pageviews FROM "+source_lang+"wiki WHERE geocoordinates is not null AND ccc_binary = 1 ORDER BY num_pageviews DESC LIMIT 10000;"

    df = pd.read_sql_query(query, conn2)

    df['Latitude'], df['Longitude'] = df['geocoordinates'].str.split(',', 1).str
    df['Latitude'] = df['Latitude'].astype(float)
    df['Longitude'] = df['Longitude'].astype(float)

    df = df.fillna(0)

    print (df.head(10))
    print (len(df))

    fig = px.scatter_mapbox(df, lat=df.Latitude, lon=df.Longitude, color=df.num_editors, size=df.num_pageviews,color_continuous_scale=px.colors.diverging.Portland, size_max=25,   hover_name="page_title", 
  hover_data=["page_title","num_edits","num_pageviews","num_editors"], zoom=5) # 
    fig.update_layout(mapbox_style="stamen-toner") # mapbox_center_lon=180
    fig.update_layout(height=800, width=1000,
                  title='The first 10000 articles by number of editors in '+source_lang+'wiki')


    return fig




### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

if __name__ == '__main__':
    dash_app.run_server(debug=True)
