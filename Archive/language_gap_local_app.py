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
lang_groups.remove('')

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
conn2 = sqlite3.connect(databases_path + 'wikipedia_diversity.db'); cursor2 = conn2.cursor() 


# SPREAD DATA
ccc_percent_wp = {}
ccc_art_wp = {}
query = 'SELECT set1, abs_value, rel_value FROM wdo_intersections_accumulated WHERE content="articles" AND set1 = set2 AND set1descriptor="wp" AND set2descriptor = "ccc" AND period IN (SELECT MAX(period) FROM wdo_intersections_accumulated);'
for row in cursor.execute(query):
    value = row[1]
    value2 = row[2]
    if value == None: value = 0
    if value2 == None: value2 = 0
    ccc_art_wp[row[0]]=value
    ccc_percent_wp[row[0]]=value2


# Spread of each Wikipedia language (%) in all Wikipedia language editions
# set1, set1descriptor, set2, set2descriptor
query = 'SELECT set2, set1, rel_value, abs_value FROM wdo_intersections_accumulated WHERE period IN (SELECT MAX(period) FROM wdo_intersections_accumulated) AND content="articles" AND set1descriptor="wp" AND set2descriptor = "ccc" ORDER BY set2, abs_value DESC;'
df_langs_map_spread = pd.read_sql_query(query, conn)

# Spread of each Wikipedia language in all Wikidata article qitems.
query = 'SELECT set2, abs_value, rel_value FROM wdo_intersections_accumulated WHERE period IN (SELECT MAX(period) FROM wdo_intersections_accumulated) AND content="articles" AND set2descriptor="ccc" AND set1 = "wikidata_article_qitems" ORDER BY set2, abs_value DESC;'
df_langs_wikidata_spread = pd.read_sql_query(query, conn)
#print (df_langs_wikidata_spread.head(10))

# Spread of each Wikipedia language in all languages CCC articles.
query = 'SELECT set2, abs_value, rel_value FROM wdo_intersections_accumulated WHERE period IN (SELECT MAX(period) FROM wdo_intersections_accumulated) AND content="articles" AND set2descriptor="ccc" AND set1 = "all_ccc_articles" ORDER BY set2, abs_value DESC;'
df_langs_all_ccc_spread = pd.read_sql_query(query, conn)
#print (df_langs_all_ccc_spread.head(10))


# SPREAD FUNCTIONS
def heatmapspread_values(lang_list,df_langs_map_spread):
    lang_list2 = []
    for lg in lang_list:
        lgcode = language_names[lg]
        if lgcode in ccc_art_wp:
            lang_list2.append(lgcode)
    lang_list = sorted(lang_list2, reverse=False)

    if lang_list != None:
        df_langs_map_spread2 = df_langs_map_spread.loc[df_langs_map_spread['set1'].isin(lang_list)]
        df_langs_map_spread2 = df_langs_map_spread2.loc[df_langs_map_spread2['set2'].isin(lang_list)]
    else:
        df_langs_map_spread2 = df_langs_map_spread

    x = sorted(list(df_langs_map_spread2.set1.unique()), reverse=False)
#    x = sorted(lang_list)
    y = sorted(x,reverse=True)
    lang_list = x

    for lang in x:
        df_langs_map_spread2 = df_langs_map_spread2.append(pd.Series([lang,lang,'',''], index=df_langs_map_spread2.columns ), ignore_index=True)

    df_langs_map_spread2 = df_langs_map_spread2.sort_values(by=['set2', 'set1'])
    df_langs_map_spread2 = df_langs_map_spread2.reset_index(drop=True)
    df_langs_map_spread2 = df_langs_map_spread2.set_index('set2')
    df_langs_map_spread2 = df_langs_map_spread2.fillna(0)

    z = list()
    z_text = list()
    z_text2 = list()
    for langx in lang_list:
        z_row = []
        z_textrow = []
        z_textrow2 = []
        try:
            df_langs_map_spread3 = df_langs_map_spread2.loc[langx]
            df_langs_map_spread3 = df_langs_map_spread3.set_index('set1')
        except:
            pass

        for langy in lang_list:
            if langx == langy:
                rel_value = round(ccc_percent_wp[langx],2)
                abs_value = ccc_art_wp[langx]
            else:
                try:
                    rel_value = round(df_langs_map_spread3.loc[langy].at['rel_value'],2)
                    abs_value = df_langs_map_spread3.loc[langy].at['abs_value']
                except:
                    abs_value = 0
                    rel_value = 0

            z_row.append(rel_value)
            z_textrow.append(str(abs_value)+ ' articles')
            z_textrow2.append(abs_value)

        z.append(z_row)
        z_text.append(z_textrow)
        z_text2.append(z_textrow2)

    z.reverse()
    z_text.reverse()
    z_text2.reverse()
    return x, y, z, z_text, z_text2


def treemapspread_allwp_allccc_values(df_langs_allccc_wikidata_spread):

    language_names_inv = {v: k for k, v in language_names.items()}
    df_langs_allccc_wikidata_spread['languagename'] = df_langs_allccc_wikidata_spread['set2'].map(language_names_inv)
    df_langs_allccc_wikidata_spread['languagename_full'] = df_langs_allccc_wikidata_spread['set2'].map(language_names_full)
    df_langs_allccc_wikidata_spread = df_langs_allccc_wikidata_spread.round(1)

    # print (df_langs_allccc_wikidata_spread.tail(10))
    # print (df_langs_allccc_wikidata_spread.head(10))
    return df_langs_allccc_wikidata_spread


def barchartcccspread_values(source_lang, df_langs_map_coverage):

    long_languagename = source_lang
    source_lang = language_names[source_lang]

    df_langs_map_coverage = df_langs_map_coverage.set_index('set1')
    df_langs_map_coverage2 = df_langs_map_coverage.loc[source_lang]

    df_langs_map_coverage2 = df_langs_map_coverage2.set_index('set2')


    df_langs_map_coverage2['Region']=languages.region
    for x in df_langs_map_coverage2.index.values.tolist():
        if ';' in df_langs_map_coverage2.loc[x]['Region']: df_langs_map_coverage2.at[x, 'Region'] = df_langs_map_coverage2.loc[x]['Region'].split(';')[0]

    df_langs_map_coverage2['Subregion']=languages.subregion
    for x in df_langs_map_coverage2.index.values.tolist():
        if ';' in df_langs_map_coverage2.loc[x]['Subregion']: df_langs_map_coverage2.at[x, 'Subregion'] = df_langs_map_coverage2.loc[x]['Subregion'].split(';')[0]

    df_langs_map_coverage2['Language']=languages.languagename

    df_langs_map_coverage2 = df_langs_map_coverage2.reset_index()

    df_langs_map_coverage2['Language (Wiki)'] = df_langs_map_coverage2['set2'].map(language_names_inv)
    df_langs_map_coverage2['Language'] = df_langs_map_coverage2['set2'].map(language_names_full)

#    df_langs_map_coverage2 = df_langs_map_coverage2.append({'set2':source_lang, 'rel_value':round(ccc_percent_wp[source_lang],2), 'abs_value':ccc_art_wp[source_lang], 'Language':long_languagename}, ignore_index = True)

    df_langs_map_coverage2 = df_langs_map_coverage2.round(1)

    df_langs_map_coverage2['Wikipedia Articles'] = df_langs_map_coverage2['set2'].map(wikipedialanguage_numberarticles)

    df_langs_map_coverage2 = df_langs_map_coverage2.rename(columns={"rel_value": "CCC Coverage Percentage", "abs_value": "Covered CCC Articles", "set2": "Covering Wikipedia Language Edition"})

    df_langs_map_coverage2 = df_langs_map_coverage2.loc[(df_langs_map_coverage2['Region']!='')]


    df_langs_map_coverage2 = df_langs_map_coverage2.sort_values(by=['Covered CCC Articles'], ascending=False)
    df_langs_map_coverage2 = df_langs_map_coverage2.head(25)

#    print (df_langs_map_coverage2.head(10))
    return df_langs_map_coverage2







### DASH APP ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 
# dash_app11 = Dash(__name__, server = app, url_base_pathname= webtype + '/language_gap/', external_stylesheets=external_stylesheets, external_scripts=external_scripts)
dash_app11 = Dash()
dash_app11.config['suppress_callback_exceptions']=True


# LAYOUT
title = "Wikipedia Languages Spread (Culture Gap)"
dash_app11.title = title+title_addenda
dash_app11.layout = html.Div([
    navbar,
    html.H3(title, style={'textAlign':'center'}),
    dcc.Markdown('''
        This page shows statistics and graphs that explain how well each Wikipedia language edition 
        [Cultural Context Content (CCC)](https://meta.wikimedia.org/wiki/Wikipedia_Cultural_Diversity_Observatory/Cultural_Context_Content) articles 
        are spread across languages.
        They illustrate the content culture gap between 
        language editions, that is the imbalances across languages editions in content representing each 
        language cultural context. They answer the following questions:
        * What is the extent of this group of Wikipedia languages editions CCC in each others content?
        * What is the extent of this language in other Wikipedia language editions?
        * What is the extent of the this language articles in the sum of all languages CCC?
        * What is the extent of the the sum of this language articles in all languages in the sum of all Wikipedia languages articles?
        * What is the extent of this language not spread to other language editions?

        '''),
    html.Br(),


    dcc.Tabs([

        dcc.Tab(label='Group of Wikipedia Lang. CCC Spread (Heatmap)', children=[

            html.H5("Languages CCC Spread Heatmap", style={'textAlign':'left'}),
            dcc.Markdown('''
                * **What is the extent of this group of Wikipedia languages editions CCC in each others content?**

                The following heatmap graph shows the extent of each Wikipedia languages' CCC in other Wikipedia language editions. The extent is calculated as the number of articles from a Wikipedia language (column) which are available in a Wikipedia language edition (row) divided by the total number of articles in the Wikipedia language edition (row). For an easy identification of values, cells are coloured being purple low extent and yellow high extent.

                In the following menu you can choose a group of Wikipedia language editions: Top 10, 20, 30 and 40 Wikipedias according to the number of articles they have, and specific continents and subcontinents. You can manually add a language edition to the list and see its CCC extent in the other Wikipedia language editions.

                '''.replace('  ', '')),
            html.Br(),

            html.Div(
            html.P('Select a group of Wikipedias'),
            style={'display': 'inline-block','width': '200px'}),

            html.Br(),

            html.Div(
            dcc.Dropdown(
                id='grouplangdropdown_spread',
                options=[{'label': k, 'value': k} for k in lang_groups],
                value='Top 10',
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),


            html.Br(),

            dcc.Dropdown(id='sourcelangdropdown_spreadheatmap',
                options = [{'label': k, 'value': k} for k in language_names_list],
                multi=True),

            html.Br(),
            html.Div(
            html.P('Show values in the cell'),
            style={'display': 'inline-block','width': '200px'}),
            html.Br(),
            
            html.Div(
            dcc.RadioItems(id='radio_articlespercentage_spread',
                options=[{'label':'Articles','value':'Articles'},{'label':'Percentage','value':'Percentage'}],
                value='Percentage',
                labelStyle={'display': 'inline-block', "margin": "0px 5px 0px 0px"},
                style={'width': '190px'}
             ), style={'display': 'inline-block','width': '200px'}),


            dcc.Graph(id = 'heatmap_spread'),
        ]),


        dcc.Tab(label='One Language Spread Across Languages (Barchart)', children=[

            html.H5('Language Spread in Other Wikipedia Language Editions Barchart'),
            dcc.Markdown('''* **What is the extent of this language in other Wikipedia language editions?**

                The following barchart graph shows for a selected Language the Wikipedia language editions that cover more articles and their total number of Wikipedia articles they contain. The color relates to the total number of Wikipedia articles.
             '''.replace('  ', '')),


            html.Div(html.P('Select a Language'), style={'display': 'inline-block','width': '200px'}),

            dcc.Dropdown(
                id='sourcelangdropdown_spread',
                options = [{'label': k, 'value': k} for k in language_names_list],
                value = 'English (en)',
                style={'width': '190px'}
             ),

            dcc.Graph(id = 'barchart_spread'),
#            html.Hr(),

        # ###----
        ]),


        dcc.Tab(label='Language Spread Treemap in All Content (Treemap)', children=[

            html.H5("Language Articles Spread Treemap", style={'textAlign':'left'}),
            dcc.Markdown('''* **What is the extent of the this language articles in the sum of all languages CCC?**
                * **What is the extent of the the sum of this language articles in all languages in the sum of all Wikipedia languages articles?**

                The following treemap graphs show (left) the extent of all languages CCC in the sum of all languages CCC articles and (right) the sum of the extent of all languages CCC in all Wikipedia language editions articles. The two graphs show the extent both in number of articles and percentage. To calculate the percentage of extent in the left graph we divide the number of articles of a language in by the sum of all languages CCC articles in their corresponding Wikipedia language editions. To calculate the percentage of extent in the right graph, for a language we count the total number of articles that exist across all the language editions and divide it by the sum of all Wikipedia language editions' articles.
                '''.replace('  ', '')),
            html.Br(),
            html.Div(id='none',children=[],style={'display': 'none'}),
            dcc.Graph(id = 'treemap_langccc_spreadtreemap'),
#            html.Hr(),

        ]),

        # ###----

        dcc.Tab(label='Languages CCC Without Interwiki (Scatterplot)', children=[

            html.H5('Languages CCC Without Interwiki Links Scatterplot'),

            dcc.Markdown('''* **What is the extent of this language not spread to other language editions?**

                The following scatterplot graph shows for all Wikipedia language editions on the Y-axis (log-scale) the number of articles in their CCC and on the X-axis the percentage of articles without any interwiki links. Wikipedia language editions are colored according to their world region (continent).
             '''.replace('  ', '')),

            dcc.Graph(id = 'scatterplot_nointerwiki'),

        ]),

        dcc.Tab(label='All Languages CCC Spread Across Languages (Table)', children=[
            html.H5("Summary Table", style={'textAlign':'left'}),
            dcc.Markdown('''
                The following table shows which language is more popular among all Wikipedia 
                language editions by counting in each language edition the number of CCC articles spread across the other languages. 

                Languages are sorted in alphabetic order by their Wikicode, and the columns present the following 
                statistics: (**CCC art.**) the number of CCC articles and the percentage it occupies in the language 
                computed in relation to their total number of articles, the percentage of articles in a language with no interwiki links (**CCC% Without Interwiki Links**), the **first five other languages** covering more 
                 articles from the language and the percentage they occupy in relation to their total number of articles, the relative spread (**R. Spread**) of a language across 
                all the other languages computed as the average of the percentage they occupy in each other language 
                edition, the total spread (**T. Spread**) of a CCC across all the other languages computed as the 
                percentage in relation to all languages articles (not counting the own), and finally, the total number 
                of language articles (**Spread Art.**) that exists across all the other language editions.'''.replace('  ', '')),

            dash_table.DataTable(
                id='datatable-cccspread',
                columns=[
                    {'name': i, 'id': i, 'deletable': True} for i in df_spread.columns
                    # omit the id column
                    if i != 'id'
                ],
                data=df_spread.to_dict('records'),
                editable=True,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                column_selectable="single",
                row_selectable="multi",
                row_deletable=True,
                selected_columns=[],
                selected_rows=[],
                page_action="native",
                page_current= 0,
                page_size= 10,
                style_data={
                    'whiteSpace': 'normal',
                    'height': 'auto'
                },
            ),
            html.Br(),
            html.Br(),
            html.Div(id='datatable-cccspread-container')

            ]),


        # ###----

    ]),

    footbar,

], className="container")



# CALLBACKS
# HEATMAP SPREAD Dropdown 
@dash_app11.callback(
    dash.dependencies.Output('sourcelangdropdown_spreadheatmap', 'value'),
    [dash.dependencies.Input('grouplangdropdown_spread', 'value')])
def set_langs_options_spread(selected_group):
    langolist, langlistnames = wikilanguages_utils.get_langs_group(selected_group, None, None, None, wikipedialanguage_numberarticles, territories, languages)

    available_options = [{'label': i, 'value': i} for i in langlistnames.keys()]
    list_options = []
    for item in available_options:
        list_options.append(item['label'])
    return sorted(list_options,reverse=False)


# HEATMAP SPREAD
@dash_app11.callback(
    Output('heatmap_spread', 'figure'),
    [Input('sourcelangdropdown_spreadheatmap', 'value'),dash.dependencies.Input('radio_articlespercentage_spread', 'value')])
def update_heatmap_spread(source_lang,articlespercentage):
#    print (source_lang)
    x, y, z, z_text, z_text2 = heatmapspread_values(sorted(source_lang,reverse=False),df_langs_map_spread)

    if articlespercentage=='Percentage':
        fig = ff.create_annotated_heatmap(z, x=x, y=y, annotation_text=z, text=z_text, colorscale='Viridis')
    else:
        fig = ff.create_annotated_heatmap(z, x=x, y=y, annotation_text=z_text2, text=z_text, colorscale='Viridis')

    fig.update_layout(
        autosize=True,
#        height=800,
        title_font_size=12,
        paper_bgcolor="White",
        title_text='Languages CCC extent (%) in Wikipedia Language editions',
        title_x=0.5,
    )

    for i in range(len(fig.layout.annotations)):
        fig.layout.annotations[i].font.size = 10
    return fig


# BARCHART CCC SPREAD
@dash_app11.callback(
    Output('barchart_spread', 'figure'),
    [Input('sourcelangdropdown_spread', 'value')])
def update_scatterplot(value):
    source_lang = value

    df_langs_map_coverage2 = barchartcccspread_values(source_lang, df_langs_map_coverage)

    fig = px.bar(df_langs_map_coverage2, x='Covering Wikipedia Language Edition', y='Covered CCC Articles',
                 hover_data=['Language','Covered CCC Articles', 'CCC Coverage Percentage', 'Region'], color='Wikipedia Articles', height=400)
    return fig


# TREEMAP CCC SPREAD ALL WP/ALL CCC
@dash_app11.callback(
    Output('treemap_langccc_spreadtreemap', 'figure'), [Input('none', 'children')])
def update_treemap_coverage_allccc_allwp(none):

    df_langs_all_ccc_spread2 = treemapspread_allwp_allccc_values(df_langs_all_ccc_spread)
    df_langs_wikidata_spread2 = treemapspread_allwp_allccc_values(df_langs_wikidata_spread)

#    print (df_spread.head(10))
    parents = list()
    for x in df_langs_wikidata_spread2.index:
        parents.append('')

#    fig = make_subplots(1, 2, subplot_titles=['Size Coverage', 'Size Extent'])
    fig = make_subplots(
        cols = 2, rows = 1,
        column_widths = [0.45, 0.45],
        # subplot_titles = ('CCC Coverage % (Size)<br />&nbsp;<br />', 'CCC Extent % (Size)<br />&nbsp;<br />'),
        specs = [[{'type': 'treemap', 'rowspan': 1}, {'type': 'treemap'}]]
    )

    fig.add_trace(go.Treemap(
        parents = parents,
        labels = df_langs_all_ccc_spread2['languagename_full'],
        values = df_langs_all_ccc_spread2['abs_value'],
        customdata = df_langs_all_ccc_spread2['rel_value'],
#        text = df_langs_all_ccc_spread2['rel_value'],
#        textinfo = "label+value+text",
        texttemplate = "<b>%{label} </b><br>%{customdata}%<br>%{value} Art.<br>",
        hovertemplate='<b>%{label} </b><br>Extent: %{customdata}%<br>Art.: %{value}<br><extra></extra>',
        marker_colorscale = 'Blues',
        ),
            row=1, col=1)

#     fig.add_trace(go.Treemap(
#         parents = parents,
#         labels = df_langs_wikidata_spread2['languagename_full'],
#         values = df_langs_wikidata_spread2['abs_value'],
#         customdata = df_langs_wikidata_spread2['rel_value'],
# #        text = df_langs_wikidata_spread2['rel_value'],
# #        textinfo = "label+value+text",
#         texttemplate = "<b>%{label} </b><br>%{customdata}%<br>%{value} Art.<br>",
#         hovertemplate='<b>%{label} </b><br>Extent: %{customdata}%<br>Art.: %{value}<br><extra></extra>',
#         marker_colorscale = 'Blues',
#         ),
#             row=1, col=2)

    fig.add_trace(go.Treemap(
        parents = parents,
        labels = df_spread['Language'],
        customdata = df_spread['T.Spread'],
        values = df_spread['Spread Art.'],
#        text = df_langs_wikidata_spread2['rel_value'],
        texttemplate = "<b>%{label} </b><br>%{customdata}%<br>%{value} Art.<br>",
#        textinfo = "label+value+text",
#        texttemplate = "<b>%{label} </b><br>%{value} Art.<br>",
        hovertemplate = "<b>%{label} </b><br>%{customdata}%<br>%{value} Art.<br><extra></extra>",
        marker_colorscale = 'Blues',
        ),
            row=1, col=2)

    fig.update_layout(
        autosize=True,
#        width=700,
        height=900,
        title_font_size=12,
#        paper_bgcolor="White",
        title_text='Sum of All Languages CCC (Left) and Sum of All Wikipedia Languages Articles (Right)',
        title_x=0.5,
    )

    return fig



# SCATTER LANGUAGES NO INTERWIKI
@dash_app11.callback(
    Output('scatterplot_nointerwiki', 'figure'), [Input('none', 'children')])
def update_scatterplot(none):

    df_s = df_spread.rename(columns={"CCC% no IW": "CCC% Without Interwiki Links", "CCC art.": "CCC articles"})
    fig = px.scatter(df_s, x="CCC% Without Interwiki Links", y="CCC articles", color="World Region", log_x=False, log_y=True,hover_data=['Language'],text="Wiki") #text="Wiki",size='Percentage of Sum of All CCC Articles',text="Wiki",
    fig.update_traces(
        textposition='top center')

    fig.update_layout(
        autosize=True,
#        width=700,
        height=700,
#        paper_bgcolor="White",
#        title_text='Languages CCC Extent % (Left) and Languages CCC Extent % (Right)',
        title_x=0.5,

    )

    return fig


### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

if __name__ == '__main__':
    dash_app11.run_server(debug=True)
