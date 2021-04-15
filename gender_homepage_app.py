import json

import dash
import dash_core_components as dcc
import pandas as pd
import plotly.express as px
import wikilanguages_utils
from dash_apps import *
#########################################################
#########################################################
#########################################################

########################################################
############DATA COMPUTATION############################
#territories = wikilanguages_utils.load_wikipedia_languages_territories_mapping()
#languages = wikilanguages_utils.load_wiki_projects_information()
with open('languagecode_mainpage.json', encoding="utf8") as f:
    file = json.load(f)

wikilanguagecodes = file.keys()


language_names_list = []
lang_groups = list()
lang_groups += ['Top 5','Top 10', 'Top 20', 'Top 30', 'Top 40']#, 'Top 50']
#lang_groups += territories['region'].unique().tolist()
#lang_groups += territories['subregion'].unique().tolist()





#######################################################
dict = {"es": {'male': 1, 'female': 23},
                   "ca": {'male': 3, 'female': 12},
                   "it": {'male': 15, 'female': 10}}
df = pd.DataFrame.from_dict(dict,orient='index')

fig = px.bar(df, barmode='stack')
fig.layout.title='Gender count of people articles appearing in the Main Page by wikipedia'
### DASH APP ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###
# dash_app23 = Dash(__name__, server = app, url_base_pathname = webtype + '/search_ccc_articles/', external_stylesheets=external_stylesheets ,external_scripts=external_scripts)
title_addenda = ' - Wikipedia Diversity Observatory (WDO)'
external_stylesheets = ['https://wcdo.wmflabs.org/assets/bWLwgP.css']
app = dash.Dash(url_base_pathname='/homepage_gender_visibility/', external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions'] = True
title = 'HP Gender Visibility'
app.title = title+title_addenda

#app.layout = \
#    html.Div([
#    dcc.Location(id='url', refresh=False),
#    html.H1(id='header', children='Gender Visibility for each language edition'),
#    html.Div(id='page-content'),
#    dcc.Graph(
#        id='example-graph',
#        figure=fig
#    )
#])
app.layout=html.Div([
    navbar,
    html.H3(title, style={'textAlign':'center'}),
    dcc.Markdown('''
        This page shows stastistics and graphs that illustrate the gender gap in Wikipedia language editions Main Page. For a detailed analysis on the evolution of gender gap over time or the pageviews women articles receive, you can check [Diversity Over Time](http://wcdo.wmflabs.org/diversity_over_time) and [Last Month Pageviews](https://wcdo.wmflabs.org/last_month_pageviews/).
        '''),

    # html.H5('Gender Gap in Wikipedia Language Editions'),

    dcc.Markdown('''* **What is the gender gap in the Main Page of specific groups of Wikipedia language editions?**'''.replace('  ', '')),


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


    dcc.Graph(id = 'language_gendergap_barchart', figure=fig),
    footbar,

], className="container")



if __name__ == '__main__':
    app.run_server(debug=True)
