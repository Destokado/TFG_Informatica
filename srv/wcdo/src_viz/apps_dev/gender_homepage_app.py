import sys

sys.path.insert(0, '/srv/wcdo/src_viz/apps_dev')
from dash_apps_dev import *
from gender_homepage_visibility_metrics import get_gendercount_by_lang, get_last_data_update

########################################################
############DATA COMPUTATION############################
territories = wikilanguages_utils.load_wikipedia_languages_territories_mapping()
languages = wikilanguages_utils.load_wiki_projects_information()

gender_dict = {'Q6581097': 'male', 'Q6581072': 'female', 'Q1052281': 'transgender female', 'Q1097630': 'intersex',
               'Q1399232': "fa'afafine", 'Q17148251': 'travesti', 'Q19798648': 'unknown value', 'Q207959': 'androgyny',
               'Q215627': 'person', 'Q2449503': 'transgender male', 'Q27679684': 'transfeminine',
               'Q27679766': 'transmasculine',
               'Q301702': 'two-Spirit', 'Q303479': 'hermaphrodite', 'Q3177577': 'muxe', 'Q3277905': 'māhū',
               'Q430117': 'Transgene', 'Q43445': 'female non-human organism', 'Q189125': 'Transgender person', 'Q48270':'non-binary'}

lang_groups = ['Top 5', 'Top 10', 'Top 20', 'Top 30', 'Top 40']  # , 'Top 50']
lang_groups += territories['region'].unique().tolist()
lang_groups += territories['subregion'].unique().tolist()

### DASH APP ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###
# dash_app23 = Dash(__name__, server = app, url_base_pathname = webtype + '/search_ccc_articles/', external_stylesheets=external_stylesheets ,external_scripts=external_scripts)
title_addenda = ' - Wikipedia Diversity Observatory (WDO)'
title = 'Home Page Gender Visibility'

app = dash.Dash(server=app_dev, url_base_pathname=webtype + '/gender_homepage_gap/',
                external_stylesheets=external_stylesheets, external_scripts=external_scripts)
app.config['suppress_callback_exceptions'] = True
app.title = title + title_addenda


def serve_layout():
    return html.Div([
        navbar,
        html.H3(title, style={'textAlign': 'center'}),
        dcc.Markdown('''
        This page shows stastistics and graphs that illustrate the gender gap in Wikipedia language editions Main Page, 
        the most viewed page. 
        For a detailed analysis on the evolution of gender gap over time or the pageviews women articles receive, 
        you can check [Diversity Over Time](http://wcdo.wmflabs.org/diversity_over_time) and
         [Last Month Pageviews](https://wcdo.wmflabs.org/last_month_pageviews/). <br>NOTE: If the gender count is 0 for 
         a selected Wikipedia in a given period of time, it won't appear in the graph.
        '''),
        dcc.Markdown('''* **What is the gender gap in the Main Page of specific groups of Wikipedia language 
    editions?**'''.replace('  ', '')),
        html.Div(
            html.P('Select a group of Wikipedias'),
            style={'display': 'inline-block', 'width': '200px'}),
        html.Br(),
        html.Div(
            dcc.Dropdown(
                id='grouplangdropdown',
                options=[{'label': k, 'value': k} for k in lang_groups],
                value='Top 10',
                style={'width': '190px'}
            ), style={'display': 'inline-block', 'width': '200px'}),
        html.Br(),
        html.Div(
            html.P('You can add or remove languages:'),
            style={'display': 'inline-block', 'width': '500px'}),

        dcc.Dropdown(id='sourcelangdropdown_homepage_gender_gap',
                     options=[{'label': k, 'value': k} for k in language_names_list],
                     multi=True),
        html.Br(),
        html.Div(
            html.P('Select a date range'),
            style={'display': 'inline-block', 'width': '200px'}),
        dcc.DatePickerRange(
            id='date_picker_range',
            min_date_allowed=datetime.date(2021, 5, 5),
            max_date_allowed= datetime.timedelta(days=1) + datetime.datetime.utcfromtimestamp(get_last_data_update()).date(),
            start_date= datetime.datetime.utcfromtimestamp( get_last_data_update()).date(),
            end_date= datetime.timedelta(days=1) + datetime.datetime.utcfromtimestamp(get_last_data_update()).date(),
            initial_visible_month=datetime.datetime.utcfromtimestamp(get_last_data_update()).date()
        ), html.Div(id='output_container_date_picker_range'),
        dcc.Graph(id='language_homepage_gendergap_barchart'),
        footbar,

    ], className="container")


app.layout = serve_layout  # This updates the layout on page load. NOTE THAT IT DOESNT NEED serve_layout(), JUST serve_layout

def newLegend(fig, newNames):
    for item in newNames:
        for i, elem in enumerate(fig.data[0].labels):
            if elem == item:
                fig.data[0].labels[i] = newNames[item]
    return(fig)
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

#### CALLBACKS ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###


# GENDER GAP Dropdown languages
@app.callback(
    Output(component_id='sourcelangdropdown_homepage_gender_gap', component_property='value'),
    [Input('grouplangdropdown', 'value')])
def set_langs_options_spread(selected_group):
    langolist, langlistnames = wikilanguages_utils.get_langs_group(selected_group, None, None, None,
                                                                   wikipedialanguage_numberarticles, territories,
                                                                   languages)
    available_options = [{'label': i, 'value': i} for i in langlistnames.keys()]
    list_options = []
    for item in available_options:
        list_options.append(item['label'])
    re = sorted(list_options, reverse=False)
    return re


# return ['ca','es','it']


# GENDER HOMEPAGE GAP Barchart
@app.callback(
    Output(component_id='language_homepage_gendergap_barchart', component_property='figure'),
    [Input('sourcelangdropdown_homepage_gender_gap', 'value'),
     Input('date_picker_range', 'start_date'),
     Input('date_picker_range', 'end_date')])
def update_barchart(langlist, startdate, enddate):
    print('langlist')
    print(langlist)
    langcodes = []  # get the langcodes out of the selection
    for l in langlist:
        code = l[l.find("(") + 1:l.find(")")]
        langcodes.append(code)
    print('Langcodes')
    print(langcodes)
    stimestamp = datetime.datetime.strptime(startdate, "%Y-%m-%d").timestamp()
    etimestamp = datetime.datetime.strptime(enddate, "%Y-%m-%d").timestamp()
    print(stimestamp, etimestamp)
    data = get_gendercount_by_lang(langcodes, float(stimestamp), float(etimestamp))
    print('Data')
    print(data)
    df = pd.DataFrame.from_records(data, columns=['Language', 'Gender', 'Count', 'Total'])
   # df = df.replace(gender_dict)  # Change the name from QXXX to Genderlabel
    df['Percentage'] = round((df['Count'] / df['Total']) * 100, 2)
    print('Dataframe')
    print(df)

    fig = px.bar(df, x='Percentage', y='Language', color='Gender', orientation='h', barmode='stack', text='Count',
                    width=700)
    display_time = datetime.datetime.utcfromtimestamp(get_last_data_update()).strftime("%-d %B, %Y at %H:%M UTC")
    fig.layout.title = 'Last data update: ' + display_time
    fig.update_layout(
        xaxis=dict(
            title_text="Gender %",
            ticktext=["0%", "20%", "40%", "60%", "80%", "100%"],
            tickvals=[0, 20, 40, 60, 80, 100],
            tickmode="array"),
        legend=dict(
            legend_title_text='Gender of the biographies linked at the Home Page'
        ))
    newLegendFig = newLegend(fig = fig, newNames = gender_dict)
    return newLegendFig

# if __name__ == '__main__':
# app.run_server(debug=True)
