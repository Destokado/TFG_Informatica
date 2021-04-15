
from dash import Dash
import dash_core_components as dcc
import dash_html_components as html


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