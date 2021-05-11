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
from navbar import * 

##### RESOURCES GENERAL #####


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

lang_groups = list()
lang_groups += ['Top 5','Top 10', 'Top 20', 'Top 30', 'Top 40']#, 'Top 50']
lang_groups += territories['region'].unique().tolist()
lang_groups += territories['subregion'].unique().tolist()
lang_groups.remove('')

#wikipedialanguage_numberarticles = wikilanguages_utils.load_wikipedia_language_editions_numberofarticles(wikilanguagecodes,'')
#print (wikipedialanguage_numberarticles)
#save_dict_to_file(wikipedialanguage_numberarticles)
wikipedialanguage_numberarticles = load_dict_from_file()
for languagecode in wikilanguagecodes:
   if languagecode not in wikipedialanguage_numberarticles: wikilanguagecodes.remove(languagecode)


cycle_year_month = '2019-05'



#### FUNCTIONS ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 

def params_to_df(langs, content_type):

    conn = sqlite3.connect(databases_path + 'stats.db'); cursor = conn.cursor() 
    # lang = language_names[lang]
    functionstartTime = time.time()
    if isinstance(langs,str): langs = [langs]
    lass = ','.join( ['?'] * len(langs) )


    if content_type == 'ccc':
        query = "SELECT set2 as Covered_Language, rel_value as Extent_Pageviews, abs_value as Pageviews FROM wcdo_intersections_monthly WHERE set1 IN ('"+lass+"') AND content='pageviews' AND set1descriptor='wp' AND set2descriptor='ccc' AND period = '"+cycle_year_month+"';"
        df_ccc_pv = pd.read_sql_query(query, conn, params = langs).round(1)

        query = "SELECT set2 as Covered_Language, rel_value Extent_Articles, abs_value as Articles FROM wcdo_intersections_accumulated WHERE content='articles' AND set1descriptor='wp' AND set2descriptor='ccc' AND set1 IN ('"+lass+"') AND period = '"+cycle_year_month+"';"
        df_ccc_articles = pd.read_sql_query(query, conn, params = langs).round(1)

        df_ccc_final = df_ccc_articles.merge(df_ccc_pv, on='Covered_Language', how='outer')
        df_ccc_final = df_ccc_final.fillna(0).round(1)
        df_ccc_final = df_ccc_final.rename(columns={'Extent_Articles':'Extent Articles (%)','Extent_Pageviews':'Extent Pageviews (%)'})

        df_ccc_final.Articles = df_ccc_final.Articles.astype(int)
        df_ccc_final.Pageviews = df_ccc_final.Pageviews.astype(int)

        df_ccc_final['Covered Language'] = df_ccc_final['Covered_Language'].map(language_names_full)
        df_ccc_final = df_ccc_final.loc[df_ccc_final['Covered_Language'] != 'simple']
        df = df_ccc_final


    if content_type == 'gender':

        query = "SELECT set1 || ':' || set2descriptor as id, set1 as Wiki, set2descriptor as Gender, abs_value as Pageviews, rel_value as Extent_Pageviews, content FROM wcdo_intersections_monthly WHERE Wiki IN ("+lass+") AND set1descriptor = 'wp' AND set2 = 'gender' AND Gender IN ('male','female') AND period = '"+cycle_year_month+"' AND content = 'pageviews'"
        df_gender_pageviews = pd.read_sql_query(query, conn, params = langs)

        query = "SELECT set1 || ':' || set2descriptor as id, set1 as Wiki, set2descriptor as Gender, abs_value as Articles, rel_value as Extent_Articles FROM wcdo_intersections_accumulated WHERE Wiki IN ("+lass+") AND content = 'articles'  AND set1descriptor = 'wp' AND Gender IN ('male','female') AND set2 = 'wikidata_article_qitems' AND period = '"+cycle_year_month+"';"
        df_gender_articles = pd.read_sql_query(query, conn, params = langs)


        df_gender_final = df_gender_articles.merge(df_gender_pageviews, on='id', how='outer')
        df_gender_final = df_gender_final.fillna(0).round(1)
        df_gender_final.Articles = df_gender_final.Articles.astype(int)
        df_gender_final.Pageviews = df_gender_final.Pageviews.astype(int)

        df_gender_final = df_gender_final.rename(columns={'Extent_Articles':'Extent Articles (%)', 'Extent_Pageviews':'Extent Pageviews (%)'})
        df_gender_final['Language'] = df_gender_final['Wiki_x'].map(language_names_full)
        df_gender_final['Language (Wiki)'] = df_gender_final['Language']+' ('+df_gender_final['Wiki_x']+')'
        df = df_gender_final


    if content_type == 'country':

        query = "SELECT set1 || ':' || set2descriptor as id, set1 as Wiki, set2descriptor, abs_value as Pageviews, rel_value as Extent_Pageviews FROM wcdo_intersections_monthly WHERE Wiki IN ("+lass+") AND set1descriptor = 'wp' AND set2 = 'country' AND period = '"+cycle_year_month+"' AND content = 'pageviews';"
        df_country_pageviews = pd.read_sql_query(query, conn, params = langs)
        df_country_pageviews = df_country_pageviews.rename(columns={'set2descriptor':'ISO 3166','Extent_Pageviews':'Extent Pageviews (%)'})
        df_country_pageviews['Country'] = df_country_pageviews['ISO 3166'].map(country_names)
        df_country_pageviews['Subregion'] = df_country_pageviews['ISO 3166'].map(subregions)
        df_country_pageviews['Region'] = df_country_pageviews['ISO 3166'].map(regions)
        df_country_pageviews = df_country_pageviews

        # articles geolocated
        query = "SELECT set1 || ':' || set2descriptor as id, set1 as Wiki, set2descriptor, abs_value as Articles, rel_value FROM wcdo_intersections_accumulated WHERE Wiki IN ("+lass+") AND set2 = 'countries' AND set1descriptor = 'geolocated' AND content = 'articles' AND period = '"+cycle_year_month+"' ORDER BY abs_value DESC;"
        df_country_articles = pd.read_sql_query(query, conn, params = langs)
        df_country_articles = df_country_articles.rename(columns={'rel_value':'Extent Articles (%)','set2descriptor':'ISO 3166'})

        df_country_final = df_country_articles.merge(df_country_pageviews, on='id', how='outer').fillna(0).round(1).dropna()
        df_country_final.Pageviews = df_country_final.Pageviews.astype(int)
        df = df_country_final.rename(columns={'Wiki_x':'Wiki','Region_y':'Region','Subregion_y':'Subregion','Country_y':'Country','ISO 3166_x':'ISO 3166'})


    if content_type == 'region':

        query = "SELECT set1 || ':' || set2descriptor as id, set1 as Wiki, set2descriptor as Region, abs_value as Pageviews, rel_value as Extent_Pageviews FROM wcdo_intersections_monthly WHERE Wiki IN ("+lass+") AND set1descriptor = 'wp' AND set2 = 'region' AND period = '"+cycle_year_month+"' AND content = 'pageviews';"
        df_region_pageviews = pd.read_sql_query(query, conn, params = langs)
        df_region_pageviews = df_region_pageviews.rename(columns={'Extent_Pageviews':'Extent Pageviews (%)'})


        query = "SELECT set1 || ':' || set2descriptor as id, set1 as Wiki, set2descriptor as Region, abs_value as Articles, rel_value FROM wcdo_intersections_accumulated WHERE Wiki IN ("+lass+") AND set2 = 'regions' AND set1descriptor = 'geolocated' AND content = 'articles' AND period = '"+cycle_year_month+"' ORDER BY abs_value DESC;"
        df_region_articles = pd.read_sql_query(query, conn, params = langs)
        df_region_articles = df_region_articles.rename(columns={'rel_value':'Extent Articles (%)'})

        df_region_final = df_region_articles.merge(df_region_pageviews, on='id', how='outer').fillna(0).round(1)
        df_region_final.Pageviews = df_region_final.Pageviews.astype(int)
        df = df_region_final.rename(columns={'Region_y':'Region','Wiki_x':'Wiki'})


    return df



#### PAGEVIEWS DATA ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 

conn = sqlite3.connect(databases_path + 'stats.db'); cursor = conn.cursor() 

functionstartTime = time.time()


# own_ccc_top_pageviews = {}
# own_ccc_top_pageviews_abs = {}
# query = "SELECT set1, rel_value, abs_value, period FROM wcdo_intersections_monthly WHERE period IN (SELECT MAX(period) FROM wcdo_intersections_monthly) AND content='pageviews' AND set1descriptor='ccc' AND set2='top_articles_lists' AND set2descriptor='pageviews' ORDER BY set1, rel_value DESC;"
# for row in cursor.execute(query):
#     own_ccc_top_pageviews[row[0]]=round(row[1],1)
#     own_ccc_top_pageviews_abs[row[0]]=row[2]

# df_own_top_ccc = pd.DataFrame.from_dict(own_ccc_top_pageviews, orient='index',columns=['Extent Pageviews (%)'])
# df_own_top_ccc = df_own_top_ccc.reset_index().rename(columns={'index':'Wiki'})
# df_own_top_ccc = df_own_top_ccc.set_index('Wiki')
# df_own_top_ccc['Region']=languages.region
# df_own_top_ccc = df_own_top_ccc.reset_index()
# df_own_top_ccc['Pageviews'] = df_own_top_ccc['Wiki'].map(own_ccc_top_pageviews_abs)
# df_own_top_ccc['Language'] = df_own_top_ccc['Wiki'].map(language_names_full)
# for x in df_own_top_ccc.index.values.tolist():
#     if ';' in df_own_top_ccc.loc[x]['Region']: df_own_top_ccc.at[x, 'Region'] = df_own_top_ccc.loc[x]['Region'].split(';')[0]
# df_own_top_ccc['Language (Wiki)'] = df_own_top_ccc['Language']+' ('+df_own_top_ccc['Wiki']+')'
# df_own_top_ccc = df_own_top_ccc.loc[(df_own_top_ccc['Region']!='')]
# # print (df_own_top_ccc.head(10))





### DASH APP ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 
dash_app6 = Dash()
dash_app6.config['suppress_callback_exceptions']=True

# dash_app6 = Dash(__name__, server = app, url_base_pathname= webtype + '/last_month_pageviews/', external_stylesheets=external_stylesheets, external_scripts=external_scripts)

title = "Last Month Pageviews"
dash_app6.title = title+title_addenda
text_heatmap = ''

dash_app6.layout = html.Div([
    html.H3(title, style={'textAlign':'center'}),
    dcc.Markdown('''
        This page shows stastistics and graphs that explain the distribution of pageviews in each Wikipedia language edition and for each types of articles. Different kinds of gaps also appear in the pageviews. 
        The graphs answer the following questions:
        * What is the extent of pageviews dedicated to each country and world region in each Wikipedia language edition?
        * What is the extent of pageviews dedicated to each language CCC in each Wikipedia language edition?
        * What is the extent of pageviews dedicated to each language edition Top CCC lists in relation to their language CCC?
        * What is the gender gap in pageviews in biographies in each Wikipedia language edition? 
       '''),
    html.Br(),
#    #html.Hr(),

###
    dcc.Tabs([
        dcc.Tab(label='Extent of Geolocated Entities in Pageviews (Treemap)', children=[
            html.Br(),

            html.H5('Extent of Geolocated Entities (Countries and Regions) in Pageviews Treemap'),
            dcc.Markdown('''* **What is the extent of pageviews dedicated to each country and world region in each Wikipedia language edition?**

                The following treemap graphs show for a selected Wikipedia language edition the extent of geographical entities (countries, subregions and world regions) in their geolocated articles. This can either be in terms of the number of articles or the pageviews they receive. The size of the tiles is according to the extent of the geographical entities take and the color simply represent the diversity of entities. When you hover on a tile you can compare both articles and pageviews extent in relative (percentage) and absolute (articles and pageviews).
             '''.replace('  ', '')),
            html.Br(),
            html.Div(
            html.P('Select a Wikipedia and a type of geographical entity'),
            style={'display': 'inline-block','width': '200px'}),
            html.Br(),

            html.Div(
            dcc.Dropdown(
                id='sourcelangdropdown_geolocated',
                options = [{'label': k, 'value': k} for k in language_names_list],
                value = 'English (en)',
                style={'width': '240px'}
             ), style={'display': 'inline-block','width': '250px'}),

            dcc.Dropdown(
                id='geolocateddropdown',
                options = [{'label': k, 'value': k} for k in ['Countries','Regions']],
                value = 'Countries',
                style={'width': '190px'}
             ),
            dcc.Graph(id = 'geolocated_treemap'),

        ]),

    ]),

], className="container")


### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###



#### CALLBACKS ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 

# GEOLOCATED TREEMAP
@dash_app6.callback(
    Output('geolocated_treemap', 'figure'),
    [Input('sourcelangdropdown_geolocated', 'value'),Input('geolocateddropdown', 'value')])
def update_treemap_geolocated(language,geographicalentity):
   
    languageproject = language; language = language_names[language]

    texttemplate = "<b>%{label} </b><br>Extent GL Pageviews: %{text}%<br>Pageviews: %{customdata}"
    hovertemplate = '<b>%{label} </b><br>Extent GL Pageviews: %{text}%<br>Pageviews: %{customdata}<br>Extent Total Pageviews: %{value}%<br><extra></extra>'

    texttemplate2 = "<b>%{label} </b><br>Extent GL Articles: %{value}%<br>Articles: %{customdata}"
    hovertemplate2 = '<b>%{label} </b><br>Extent GL Articles: %{value}%<br>Articles: %{customdata}<br>Extent GL Pageviews: %{text}%<br><extra></extra>'


    if geographicalentity == 'Countries':
        labels = "Country"
        df = params_to_df(language, 'country')

    if geographicalentity == 'Regions':
        labels = "Region"
        df = params_to_df(language, 'region')


    Total = df['Pageviews'].sum()
    df['Extent GL Pageviews (%)'] = 100*df['Pageviews']/Total
    df = df.round(1)

    parents = list()
    for x in df.index: parents.append('')


    fig = make_subplots(
        cols = 2, rows = 1,
        column_widths = [0.45, 0.45],
        # subplot_titles = ('CCC Coverage % (Size)<br />&nbsp;<br />', 'CCC Extent % (Size)<br />&nbsp;<br />'),
        specs = [[{'type': 'treemap', 'rowspan': 1}, {'type': 'treemap'}]]
    )

    fig.add_trace(go.Treemap(
        parents = parents,
        labels = df[labels],
        customdata = df['Articles'],
        values = df['Extent Articles (%)'],
        text = df['Extent GL Pageviews (%)'],
        texttemplate = texttemplate2,
        hovertemplate= hovertemplate2,
#        marker_colorscale = 'RdBu',
        ),
            row=1, col=1)

    fig.add_trace(go.Treemap(
        parents = parents,
        labels = df[labels],
        customdata = df['Pageviews'],
        values = df['Extent Pageviews (%)'],
        text = df['Extent GL Pageviews (%)'],
        texttemplate = texttemplate,
        hovertemplate= hovertemplate,
#        marker_colorscale = 'RdBu',
        ),
            row=1, col=2)

    fig.update_layout(
        autosize=True,
    #        width=700,
        height=900,
        paper_bgcolor="White",
        title_text=geographicalentity+" Extent in Geolocated Articles (Left) and "+geographicalentity+" Extent in Geolocated Articles' Pageviews (Right)",
        title_x=0.5,
    )

    return fig



# LANGUAGE CCC TREEMAP
@dash_app6.callback(
    Output('language_ccc_treemap', 'figure'),
    [Input('sourcelangdropdown_languageccc', 'value')])
def update_treemap_ccc(language):

    languageproject = language; language = language_names[language]
    # df = df_ccc_final.loc[df_ccc_final['Wiki_x'] == language]

    df = params_to_df(language, 'ccc')

    parents = list()
    for x in df.index:
        parents.append('')

#    print (df.head(10))

#    fig = make_subplots(1, 2, subplot_titles=['Size Coverage', 'Size Extent'])
    fig = make_subplots(
        cols = 2, rows = 1,
        column_widths = [0.45, 0.45],
        # subplot_titles = ('CCC Coverage % (Size)<br />&nbsp;<br />', 'CCC Extent % (Size)<br />&nbsp;<br />'),
        specs = [[{'type': 'treemap', 'rowspan': 1}, {'type': 'treemap'}]]
    )

    fig.add_trace(go.Treemap(
        parents = parents,
        labels = df['Covered Language'],
        values = df['Articles'],
        customdata = df['Extent Articles (%)'],
        texttemplate = "<b>%{label} </b><br>%{customdata}%<br>%{value} Art.<br>",
        hovertemplate='<b>%{label} </b><br>Extent: %{customdata}%<br>Art.: %{value}<br><extra></extra>',
#        marker_colorscale = 'Blues',
        ),
            row=1, col=1)


    fig.add_trace(go.Treemap(
        parents = parents,
        labels = df['Covered Language'],
        values = df['Pageviews'],
        customdata = df['Extent Pageviews (%)'],
        texttemplate = "<b>%{label} </b><br>%{customdata}%<br>%{value} Pv.<br>",
        hovertemplate='<b>%{label} </b><br>Extent: %{customdata}%<br>Pv.: %{value}<br><extra></extra>',
#        marker_colorscale = 'Blues',
        ),
            row=1, col=2)

    fig.update_layout(
        autosize=True,
#        width=700,
        height=900,
#        paper_bgcolor="White",
        title_text="Languages CCC Extent in "+languageproject+"Wikipedia Articles (Left) and Languages CCC Extent in "+languageproject+" Articles' Pageviews (Right)",
        title_x=0.5,
    )

    return fig




# GENDER GAP Dropdown languages
@dash_app6.callback(
    dash.dependencies.Output('sourcelangdropdown_gendergap', 'value'),
    [dash.dependencies.Input('grouplangdropdown', 'value')])
def set_langs_options_spread(selected_group):
    # langolist, langlistnames = wikilanguages_utils.get_langs_group(selected_group, None, None, None, wikipedialanguage_numberarticles, territories, languages)
    # available_options = [{'label': i, 'value': i} for i in langlistnames.keys()]
    # list_options = []
    # for item in available_options:
    #     list_options.append(item['label'])
    # re = sorted(list_options,reverse=False)

    return ['Cebuano (ceb)', 'Dutch (nl)', 'English (en)', 'French (fr)', 'German (de)', 'Italian (it)', 'Polish (pl)', 'Russian (ru)', 'Spanish (es)', 'Swedish (sv)']


# GENDER GAP BARCHART
@dash_app6.callback(
    Output('language_gendergap_barchart', 'figure'),
    [Input('sourcelangdropdown_gendergap', 'value')])
def update_barchart(langs):

    languagecodes = []
    for l in langs:
        languagecodes.append(language_names[l])

    df_gender_final = params_to_df(languagecodes, 'gender')

    df_gender_final_male = df_gender_final.loc[df_gender_final['Gender_x'] == 'male']
    df_gender_final_male = df_gender_final_male.set_index('Wiki_x')
    df_gender_final_female = df_gender_final.loc[df_gender_final['Gender_x'] == 'female']
    df_gender_final_female = df_gender_final_female.set_index('Wiki_x')

    for x in df_gender_final_male.index.values.tolist():
        try:
            male = df_gender_final_male.loc[x]['Articles']
        except:
            male = 0    
        try:
            female = df_gender_final_female.loc[x]['Articles']
        except:
            female = 0
        df_gender_final_male.at[x, 'Extent Articles (%)'] =  100*male/(male+female)
        df_gender_final_female.at[x, 'Extent Articles (%)'] =  100*female/(male+female)

        try:
            male = df_gender_final_male.loc[x]['Pageviews']
        except:
            male = 0    
        try:
            female = df_gender_final_female.loc[x]['Pageviews']
        except:
            female = 0

        pvsum = male+female
        if pvsum == 0:
            df_gender_final_male.at[x, 'Extent Pageviews (%)'] = 0
        else:
            df_gender_final_male.at[x, 'Extent Pageviews (%)'] = 100*male/pvsum

        if pvsum == 0:
            df_gender_final_male.at[x, 'Extent Pageviews (%)'] = 0
        else:
            df_gender_final_female.at[x, 'Extent Pageviews (%)'] =  100*female/pvsum

    df_gender_final_male = df_gender_final_male.reset_index().round(1)
    df_gender_final_female = df_gender_final_female.reset_index().round(1)

    df_gender_final_male['Language (Art.)'] = df_gender_final_male['Language'] + ' Art.'
    df_gender_final_female['Language (Art.)'] = df_gender_final_female['Language'] + ' Art.'

    df_gender_final_male['Language (Pv.)'] = df_gender_final_male['Language'] + ' Pv.'
    df_gender_final_female['Language (Pv.)'] = df_gender_final_female['Language'] + ' Pv.'


    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_gender_final_male['Language (Art.)'],
        y=df_gender_final_male['Extent Articles (%)'],
        name='Men Articles',
        marker_color='blue',
#        values = df2['Extent Articles (%)'],
        customdata = df_gender_final_male['Articles'],
        texttemplate='%{y}',
        hovertemplate='<br>Articles: %{customdata}<br>Extent Articles: %{y}%<br><extra></extra>',

    ))
    fig.add_trace(go.Bar(
        x=df_gender_final_female['Language (Art.)'],
        y=df_gender_final_female['Extent Articles (%)'],
        name='Women Articles',
        marker_color='red',
#        values = df2['Extent Articles (%)'],
        customdata = df_gender_final_female['Articles'],
        texttemplate='%{y}',
        hovertemplate='<br>Articles: %{customdata}<br>Extent Articles: %{y}%<br><extra></extra>',
    ))
    fig.add_trace(go.Bar(
        x=df_gender_final_male['Language (Pv.)'],
        y=df_gender_final_male['Extent Pageviews (%)'],
        name='Men Pageviews',
        marker_color='violet',
        customdata = df_gender_final_male['Pageviews'],
        texttemplate='<b>%{y}</b>',
        hovertemplate='<br>Pageviews: %{customdata}<br>Extent Pageviews: %{y}%<br><extra></extra>',

    ))
    fig.add_trace(go.Bar(
        x=df_gender_final_female['Language (Pv.)'],
        y=df_gender_final_female['Extent Pageviews (%)'],
        name='Women Pageviews',
        marker_color='orange',
        customdata = df_gender_final_female['Pageviews'],
        texttemplate='<b>%{y}</b>',
        hovertemplate='<br>Pageviews: %{customdata}<br>Extent Pageviews: %{y}%<br><extra></extra>',
    ))    
    fig.update_layout(barmode='stack')

    return fig





### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

if __name__ == '__main__':
    dash_app6.run_server(debug=True)
