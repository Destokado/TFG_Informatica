import json

import dash
import dash_core_components as dcc
from dash import dependencies
import pandas as pd
import plotly.express as px
from dash.dependencies import Output,Input

import wikilanguages_utils
from dash_apps import *
#########################################################
#########################################################
#########################################################

########################################################
############DATA COMPUTATION############################
#territories = wikilanguages_utils.load_wikipedia_languages_territories_mapping()
#languages = wikilanguages_utils.load_wiki_projects_information()
from gender_homepage_visibility import get_gendercount_by_lang

with open('languagecode_mainpage.json', encoding="utf8") as f:
    file = json.load(f)

wikilanguagecodes = file.keys()
language_names_list = wikilanguagecodes

lang_groups = list()
lang_groups += ['Top 5','Top 10', 'Top 20', 'Top 30', 'Top 40']#, 'Top 50']
#lang_groups += territories['region'].unique().tolist()
#lang_groups += territories['subregion'].unique().tolist()





#######################################################
dict = {"es": {'male': 1, 'female': 23},
                   "ca": {'male': 3, 'female': 12},
                   "it": {'male': 15, 'female': 10}}





#df = pd.DataFrame.from_dict(dict,orient='index')

### DASH APP ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###
# dash_app23 = Dash(__name__, server = app, url_base_pathname = webtype + '/search_ccc_articles/', external_stylesheets=external_stylesheets ,external_scripts=external_scripts)
title_addenda = ' - Wikipedia Diversity Observatory (WDO)'
external_stylesheets = ['https://wcdo.wmflabs.org/assets/bWLwgP.css']
app = dash.Dash(url_base_pathname='/homepage_gender_visibility/', external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions'] = True
title = 'Home Page Gender Visibility'
app.title = title+title_addenda

app.layout= html.Div([
    navbar,
    html.H3(title, style={'textAlign':'center'}),
    dcc.Markdown('''
        This page shows stastistics and graphs that illustrate the gender gap in Wikipedia language editions Main Page. For a detailed analysis on the evolution of gender gap over time or the pageviews women articles receive, you can check [Diversity Over Time](http://wcdo.wmflabs.org/diversity_over_time) and [Last Month Pageviews](https://wcdo.wmflabs.org/last_month_pageviews/).
        '''),

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

    dcc.Dropdown(id='sourcelangdropdown_homepage_gender_gap',
        options = [{'label': k, 'value': k} for k in language_names_list],
        multi=True),


    dcc.Graph(id = 'language_homepage_gendergap_barchart'),
    footbar,

], className="container")


### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

#### CALLBACKS ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###


# GENDER GAP Dropdown languages
@app.callback(
    Output(component_id='sourcelangdropdown_homepage_gender_gap', component_property='value'),
    [Input('grouplangdropdown', 'value')])
def set_langs_options_spread(selected_group):
    #langolist, langlistnames = wikilanguages_utils.get_langs_group(selected_group, None, None, None, wikipedialanguage_numberarticles, territories, languages)
    #available_options = [{'label': i, 'value': i} for i in langlistnames.keys()]
    #list_options = []
    #for item in available_options:
    #    list_options.append(item['label'])
    #re = sorted(list_options,reverse=False)
    #return re

   return ['ca','es','it']


#GENDER HOMEPAGE GAP Barchart
@app.callback(
    Output(component_id='language_homepage_gendergap_barchart',component_property='figure'),[Input('sourcelangdropdown_homepage_gender_gap','value')])
def update_barchart(langlist):
    data = get_gendercount_by_lang(langlist)

    df = pd.DataFrame.from_records(data,columns=['Language','Gender','Count'])
    print(df)
    newfig = px.bar(df, x='Language', y='Count', color='Gender')

    return newfig

if __name__ == '__main__':
    app.run_server(debug=True)
