import sys

from dash_apps_dev import *

sys.path.insert(0, '/srv/wcdo/src_viz/apps_dev')

### DASH APP ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###
app = Dash(__name__, server=app_dev, url_base_pathname=webtype + '/map_of_gaps/',
           external_stylesheets=external_stylesheets, external_scripts=external_scripts)

app.config['suppress_callback_exceptions'] = True
title = "Map of Gaps"
app.title = title + title_addenda

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
])

source_lang_dict = {}
for languagecode in wikilanguagecodes:
    lang_name = languages.loc[languagecode]['languagename'] + ' (' + languagecode + ')'
    source_lang_dict[lang_name] = languagecode

topic_dict = {'All': 'all', 'Keywords': 'keywords', 'People': 'people', 'Women': 'women',
              'Men': 'men', 'Folk': 'folk', 'Earth': 'earth', 'Monuments and Buildings': 'monuments_and_buildings',
              'Music Creations and Organizations': 'music_creations_and_organizations',
              'Sports and Teams': 'sport_and_teams', 'Food': 'food', 'Paintings': 'paintings', 'GLAM': 'glam',
              'Books': 'books', 'Clothing and Fashion': 'clothing_and_fashion', 'Industry': 'industry',
              'Not people': 'not_people', 'CCC': 'ccc', 'CCC Not People': 'ccc_not_people', 'Medicine': 'medicine'}

target_langs_dict = language_names
#target_langs_dict = source_lang_dict MAYBE?
features_dict = {'Editors': 'num_editors', 'Edits': 'num_edits', 'Pageviews': 'num_pageviews', 'Inlinks': 'num_inlinks',
                 'References': 'num_references', 'Bytes': 'num_bytes', 'Outlinks': 'num_outlinks',
                 'Interwiki': 'num_interwiki', 'WDProperties': 'num_wdproperty', 'Discussions': 'num_discussions',
                 'Inlinks from CCC': 'num_inlinks_from_CCC',
                 'Outlinks to CCC': 'num_outlinks_to_CCC'}

features_dict_inv = {v: k for k, v in features_dict.items()}
show_gaps_dict = {'No language gaps': 'no-gaps', 'At least one gap': 'one-gap-min', 'Only gaps': 'only-gaps'}

## ----------------------------------------------------------------------------------------------------- ##

text_default = '''In this page you can visualize geolocated articles about different topics from Wikipedia language editions and check its availability in a specific Wikipedia.'''

## ----------------------------------------------------------------------------------------------------- ##


interface_row1 = html.Div([

    html.Div(
        [
            html.P(
                [
                    "Source ",
                    html.Span(
                        "language",
                        id="tooltip-target-sourcelanguage",
                        style={"textDecoration": "underline", "cursor": "pointer"},
                    ),
                ]
            ),
            dbc.Tooltip(
                html.P(
                    "Select the language editions from which you want to visualize the articles they have in common. You can retrieve a single language if you want. The relevance features will be according to the first language.",
                    style={"width": "42rem", 'font-size': 12, 'text-align': 'left', 'backgroundColor': '#F7FBFE',
                           'padding': '12px 12px 12px 12px'}
                ),
                target="tooltip-target-sourcelanguage",
                placement="bottom",
                style={'color': 'black', 'backgroundColor': 'transparent'},
            )],
        style={'display': 'inline-block', 'width': '200px'},
    ),

    html.Div(
        [
            html.P(
                [
                    "Target ",
                    html.Span(
                        "language",
                        id="tooltip-target-targetlanguages",
                        style={"textDecoration": "underline", "cursor": "pointer"},
                    ),
                ]
            ),
            dbc.Tooltip(
                html.P(
                    "Select the target Wikipedia language editions in which you want to check whether the resulting articles exist or not.",
                    style={"width": "42rem", 'font-size': 12, 'text-align': 'left', 'backgroundColor': '#F7FBFE',
                           'padding': '12px 12px 12px 12px'}
                ),
                target="tooltip-target-targetlanguages",
                placement="bottom",
                style={'color': 'black', 'backgroundColor': 'transparent'},
            )],
        style={'display': 'inline-block', 'width': '200px'},
    ),

])

interface_row2 = html.Div([

    html.Div(
        [
            html.P(
                [
                    html.Span(
                        "Topic",
                        id="tooltip-target-topic",
                        style={"textDecoration": "underline", "cursor": "pointer"},
                    ),
                ]
            ),
        ],
        style={'display': 'inline-block', 'width': '200px'},
    ),

    dbc.Tooltip(
        html.P('Select a Topic to filter the resulting articles to biographies, keywords or general topics.',
               style={"width": "47rem", 'font-size': 12, 'text-align': 'left', 'backgroundColor': '#F7FBFE',
                      'padding': '12px 12px 12px 12px'}
               ),
        target="tooltip-target-topic",
        placement="bottom",
        style={'color': 'black', 'backgroundColor': 'transparent'},
    ),

    html.Div(
        [
            html.P(
                [
                    "Order by ",
                    html.Span(
                        "feature",
                        id="tooltip-target-orderby",
                        style={"textDecoration": "underline", "cursor": "pointer"},
                    ),
                ]
            ),
            dbc.Tooltip(
                html.P(
                    "Select a feature to sort the results (by default the number of page views ).",
                    style={"width": "auto", 'font-size': 12, 'text-align': 'left', 'backgroundColor': '#F7FBFE',
                           'padding': '12px 12px 12px 12px'}
                ),
                target="tooltip-target-orderby",
                placement="bottom",
                style={'color': 'black', 'backgroundColor': 'transparent'},
            )],
        style={'display': 'inline-block', 'width': '200px'},
    ),

    html.Div(
        [
            html.P(
                [
                    "Show the ",
                    html.Span(
                        "gaps",
                        id="tooltip-target-exclude",
                        style={"textDecoration": "underline", "cursor": "pointer"},
                    ),
                ]
            ),
            dbc.Tooltip(
                html.P(
                    "Select Show the gaps to limit the results to only the articles that are missing in the target languages (Only Gaps), that are missing in at least one language (At least one gap) or that are not missing (No language gaps).",
                    style={"width": "42rem", 'font-size': 12, 'text-align': 'left', 'backgroundColor': '#F7FBFE',
                           'padding': '12px 12px 12px 12px'}
                ),
                target="tooltip-target-exclude",
                placement="bottom",
                style={'color': 'black', 'backgroundColor': 'transparent'},
            )],
        style={'display': 'inline-block', 'width': '200px'},
    ),

    html.Div(
        [
            html.P(
                [
                    "Limit the ",
                    html.Span(
                        "results",
                        id="tooltip-target-limit",
                        style={"textDecoration": "underline", "cursor": "pointer"},
                    ),
                ]
            ),
            dbc.Tooltip(
                html.P(
                    "Choose a number of results (by default 100)",
                    style={"width": "26rem", 'font-size': 12, 'text-align': 'left', 'backgroundColor': '#F7FBFE',
                           'padding': '12px 12px 12px 12px'}
                ),
                target="tooltip-target-limit",
                placement="bottom",
                style={'color': 'black', 'backgroundColor': 'transparent'},
            )],
        style={'display': 'inline-block', 'width': '200px'},
    )

])


def dash_app19_build_layout(params):
    # 'source_lang','target_langs','topic','order_by','show_gaps','limit'
    if len(params) != 0 and params['target_langs'].lower() != 'none' and params['source_lang'].lower() != 'none':
        # print (params)

        conn = sqlite3.connect(databases_path + 'wikipedia_diversity_production.db');
        cur = conn.cursor()

        # SOURCE lANGUAGE
        source_lang = params['source_lang'].lower()
        source_language = languages.loc[source_lang]['languagename']

        # TARGET LANGUAGES
        target_langs = params['target_langs'].lower()
        target_langs = target_langs.split(',')
        target_language = languages.loc[target_langs[0]]['languagename']

        # CONTENT
        if 'topic' in params:
            topic = params['topic']
        else:
            topic = 'none'

        # FILTER
        if 'order_by' in params:
            order_by = params['order_by']
        else:
            order_by = 'none'

        if 'limit' in params:
            try:
                limit = int(params['limit'])
            except:
                limit = 100
        else:
            limit = 100

        try:
            show_gaps = params['show_gaps']
        except:
            show_gaps = 'none'

        columns = ['num', 'qitem', 'page_title', 'num_editors', 'num_edits', 'num_pageviews', 'num_interwiki',
                   'num_bytes', 'date_created', 'geocoordinates']
        # CREATING THE QUERY FROM THE PARAMS
        columns, query = build_columns_and_query(columns, limit, order_by, source_lang, target_langs, topic, show_gaps)

        # print (query)
        # print (show_gaps)

        df = pd.read_sql_query(query, conn)  # , parameters)

        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(source_lang);

        df = wikilanguages_utils.get_interwikilinks_articles(source_lang, target_langs, df, mysql_con_read)

        if order_by == "none" or order_by == "None":
            df = df.sort_values(by='num_pageviews', ascending=False)
        else:
            df = df.sort_values(by=order_by, ascending=False)

        df = df.fillna('')

        columns_dict = {'num': 'Nº', 'page_title': source_language + ' Title', 'target_langs': 'Target Langs.',
                        'qitem': 'Qitem'}
        columns_dict.update(features_dict_inv)

        main_title = 'Map of geolocated articles retrieved from ' + source_language + ' Wikipedia and its coverage by the target languages'

        text_results = '''
        The following map shows the resulting list of articles in the source language ''' + source_language + ''', and its availability in the target languages.

        The Qitem column provides the id and a link to the Wikidata corresponding page. The column Title provides the title in the source language. The next columns (editors, edits, pageviews, interwiki, creation date) show the value for some features in the first source language. The column Geocoordinates tells the coordinates. The column Target Langs. provides links to the article version in each of the selected target languages. The last column shows the title in the first target language.
        '''

        # PAGE CASE 2: PARAMETERS WERE INTRODUCED AND THERE ARE NO RESULTS
        if len(df) == 0:
            layout = html.Div([
                navbar,
                html.H3('Map of Gaps', style={'textAlign': 'center'}),
                html.Br(),

                dcc.Markdown(
                    text_default.replace('  ', '')),

                # HERE GOES THE INTERFACE
                # LINE
                html.Br(),
                html.H5('Select the source'),
                interface_row1,

                html.Div(
                    dash_apps_dev.apply_default_value(params)(dcc.Dropdown)(
                        id='source_lang',
                        options=[{'label': i, 'value': source_lang_dict[i]} for i in sorted(source_lang_dict)],
                        value='en',
                        placeholder="Select languages",
                        style={'width': '190px'}
                    ), style={'display': 'inline-block', 'width': '200px'}),

                html.Div(
                    dash_apps_dev.apply_default_value(params)(dcc.Dropdown)(
                        id='target_langs',
                        options=[{'label': i, 'value': target_langs_dict[i]} for i in sorted(target_langs_dict)],
                        value=['en'],
                        multi=True,
                        placeholder="Select languages",
                        style={'width': '670px'}
                    ), style={'display': 'inline-block', 'width': '690px'}),

                # LINE
                html.Br(),
                interface_row2,
                html.Div(
                    dash_apps_dev.apply_default_value(params)(dcc.Dropdown)(
                        id='topic',
                        options=[{'label': i, 'value': topic_dict[i]} for i in sorted(topic_dict)],
                        value='none',
                        placeholder="Select a topic",
                        style={'width': '190px'}
                    ), style={'display': 'inline-block', 'width': '200px'}),

                html.Div(
                    dash_apps_dev.apply_default_value(params)(dcc.Dropdown)(
                        id='order_by',
                        options=[{'label': i, 'value': features_dict[i]} for i in sorted(features_dict)],
                        value='none',
                        placeholder="Order by (optional)",
                        style={'width': '190px'}
                    ), style={'display': 'inline-block', 'width': '200px'}),

                html.Div(
                    dash_apps_dev.apply_default_value(params)(dcc.Dropdown)(
                        id='show_gaps',
                        options=[{'label': i, 'value': show_gaps_dict[i]} for i in sorted(show_gaps_dict)],
                        value='none',
                        placeholder="Show the gaps",
                        style={'width': '190px'}
                    ), style={'display': 'inline-block', 'width': '200px'}),

                html.Div(
                    dash_apps_dev.apply_default_value(params)(dcc.Input)(
                        id='limit',
                        placeholder='Enter a value...',
                        type='text',
                        value='100',
                        style={'width': '90px'}
                    ), style={'display': 'inline-block', 'width': '100px'}),

                ###

                html.Div(
                    html.A(html.Button('Query Results!'),
                           href=''),
                    style={'display': 'inline-block', 'width': '200px'}),

                html.Br(),
                html.Br(),

                html.Hr(),
                html.H5('Results'),
                dcc.Markdown(results_text.replace('  ', '')),
                html.Br(),
                html.H6('There are no results. Unfortunately this list is empty for this language.'),

                footbar,

            ], className="container")

            return layout

        # PAGE CASE 3: PARAMETERS WERE INTRODUCED AND THERE ARE RESULTS

        # # PREPARE THE DATA
        df = df.rename(columns=columns_dict)
        # print (df.head(100))

        columns_ = []
        for x in columns:
            columns_.append(columns_dict[x])
        columns = columns_
        columns.append(target_language + ' Title')
        # print (columns)

        df_list = list()
        k = 0
        z = 0
        for rows in df.iterrows():
            df_row = list()

            for col in columns:
                if col == 'Nº':
                    k += 1
                    df_row.append(str(k))

                elif col == source_language + ' Title':
                    title = rows[source_language + ' Title']
                    if not isinstance(title, str):
                        title = title.iloc[0]
                    df_row.append(html.A(title.replace('_', ' '),
                                         href='https://' + source_lang + '.wikipedia.org/wiki/' + title.replace(' ',
                                                                                                                '_'),
                                         target="_blank", style={'text-decoration': 'none'}))

                elif col == target_language + ' Title':

                    t_title = rows['page_title_1']
                    if isinstance(t_title, str):
                        df_row.append(html.A(t_title.replace('_', ' '), href='https://' + target_langs[
                            0] + '.wikipedia.org/wiki/' + t_title.replace(' ', '_'), target="_blank",
                                             style={'text-decoration': 'none'}))


                elif col == 'Interwiki':
                    df_row.append(html.A(rows['Interwiki'], href='https://www.wikidata.org/wiki/' + rows['Qitem'],
                                         target="_blank", style={'text-decoration': 'none'}))

                elif col == 'Bytes':
                    value = round(float(int(rows[col]) / 1000), 1)
                    df_row.append(str(value) + 'k')

                elif col == 'Outlinks' or col == 'References' or col == 'Images':
                    title = rows[source_language + ' Title']
                    df_row.append(html.A(rows[col],
                                         href='https://' + target_langs[0] + '.wikipedia.org/wiki/' + title.replace(' ',
                                                                                                                    '_'),
                                         target="_blank", style={'text-decoration': 'none'}))

                elif col == 'Inlinks':
                    df_row.append(html.A(rows['Inlinks'],
                                         href='https://' + source_lang + '.wikipedia.org/wiki/Special:WhatLinksHere/' +
                                              rows[source_language + ' Title'].replace(' ', '_'), target="_blank",
                                         style={'text-decoration': 'none'}))

                elif col == 'Inlinks from CCC':
                    df_row.append(html.A(rows['Inlinks from CCC'],
                                         href='https://' + source_lang + '.wikipedia.org/wiki/Special:WhatLinksHere/' +
                                              rows[source_language + ' Title'].replace(' ', '_'), target="_blank",
                                         style={'text-decoration': 'none'}))

                elif col == 'Outlinks from CCC':
                    df_row.append(html.A(rows['Outlinks from CCC'],
                                         href='https://' + source_lang + '.wikipedia.org/wiki/' + rows[
                                             source_language + ' Title'].replace(' ', '_'), target="_blank",
                                         style={'text-decoration': 'none'}))

                elif col == 'Editors':
                    df_row.append(html.A(rows['Editors'],
                                         href='https://' + source_lang + '.wikipedia.org/w/index.php?title=' + rows[
                                             source_language + ' Title'].replace(' ', '_') + '&action=history',
                                         target="_blank", style={'text-decoration': 'none'}))

                elif col == 'Edits':
                    df_row.append(html.A(rows['Edits'],
                                         href='https://' + source_lang + '.wikipedia.org/w/index.php?title=' + rows[
                                             source_language + ' Title'].replace(' ', '_') + '&action=history',
                                         target="_blank", style={'text-decoration': 'none'}))

                elif col == 'Discussions':
                    df_row.append(html.A(rows['Discussions'],
                                         href='https://' + source_lang + '.wikipedia.org/wiki/Talk:' + rows[
                                             source_language + ' Title'].replace(' ', '_'), target="_blank",
                                         style={'text-decoration': 'none'}))

                elif col == 'Wikirank':
                    df_row.append(html.A(rows['Wikirank'], href='https://wikirank.net/' + source_lang + '/' + rows[
                        source_language + ' Title'], target="_blank", style={'text-decoration': 'none'}))

                elif col == 'Pageviews':
                    df_row.append(html.A(rows['Pageviews'],
                                         href='https://tools.wmflabs.org/pageviews/?project=' + source_lang + '.wikipedia.org&platform=all-access&agent=user&range=latest-20&pages=' +
                                              rows[source_language + ' Title'].replace(' ', '_') + '&action=history',
                                         target="_blank", style={'text-decoration': 'none'}))

                elif col == 'Wikidata Properties':
                    df_row.append(
                        html.A(rows['Wikidata Properties'], href='https://www.wikidata.org/wiki/' + rows['qitem'],
                               target="_blank", style={'text-decoration': 'none'}))

                elif col == 'Discussions':
                    title = rows[source_lang + ' Title']
                    df_row.append(html.A(str(rows[col]),
                                         href='https://' + source_lang + '.wikipedia.org/wiki/' + title.replace(' ',
                                                                                                                '_'),
                                         target="_blank", style={'text-decoration': 'none'}))

                elif col == 'Creation Date':
                    date = rows['Creation Date']
                    if date == 0 or date == '' or date == None:
                        date = ''
                    else:
                        date = str(time.strftime("%Y-%m-%d", time.strptime(str(int(date)), "%Y%m%d%H%M%S")))
                    df_row.append(date)

                elif col == 'GeoCoordinates':
                 df_row.append(#GoogleMaps
                    html.A(rows['GeoCoordinates'], href='https://www.google.com/maps/search/' + rows['GeoCoordinates'],
                           target="_blank",
                           style={'text-decoration': 'none'}))
                 #df_row.append(#OpenStreetMaps
                 #   html.A(rows['GeoCoordinates'], href='https://nominatim.openstreetmap.org/ui/search.html?q=' + rows['GeoCoordinates'],
                 #          target="_blank",
                 #          style={'text-decoration': 'none'}))

                #LAT,LON
               # df_row.append(rows['GeoCoordinates'])
                elif col == 'Target Langs.':
                    z=0
                    for i,lang in enumerate(target_langs):
                       cur_title = rows['page_title_' + i]
                       if cur_title  == '': z += 1
                       if(cur_title) != None and cur_title != '' and cur_title != 0 and cur_title != 'NULL':
                        if i>0: #In the first lang we dont put the comma separator
                            text = ', '
                            text += '[' +lang + ']' + '(' + 'http://' + lang + '.wikipedia.org/wiki/' + cur_title.replace(' ', '_') + ')'
                     df_row.append(dcc.Markdown(text))



                elif col == 'Qitem':
                    df_row.append(
                        html.A(rows['Qitem'], href='https://www.wikidata.org/wiki/' + rows['Qitem'], target="_blank",
                               style={'text-decoration': 'none'}))



                else:
                    df_row.append(rows[col])

            # print (rows)
            # print (len(rows))
            # print (len(df_row))

            if show_gaps == 'one-gap-min' and z == 0:
                continue
            elif show_gaps == 'only-gaps' and z < len(target_langs_titles):
                continue
            elif show_gaps == 'no-gaps' and z > 0:
                continue

            if k <= limit:
                df_list.append(df_row)

        # RESULTS
        title = 'Map of Articles'
        df1 = pd.DataFrame(df_list)
        app.title = title + title_addenda

        # LAYOUT
        layout = html.Div([
            navbar,
            html.H3(title, style={'textAlign': 'center'}),
            html.Br(),
            dcc.Markdown(
                text_default.replace('  ', '')),

            # HERE GOES THE INTERFACE
            # LINE
            html.Br(),
            html.H5('Select the source'),
            interface_row1,

            html.Div(
                dash_apps_dev.apply_default_value(params)(dcc.Dropdown)(
                    id='source_lang',
                    options=[{'label': i, 'value': source_lang_dict[i]} for i in sorted(source_lang_dict)],
                    value='en',
                    placeholder="Select languages",
                    style={'width': '190px'}
                ), style={'display': 'inline-block', 'width': '200px'}),

            html.Div(
                dash_apps_dev.apply_default_value(params)(dcc.Dropdown)(
                    id='target_langs',
                    options=[{'label': i, 'value': target_langs_dict[i]} for i in sorted(target_langs_dict)],
                    value=['en'],
                    multi=True,
                    placeholder="Select languages",
                    style={'width': '670px'}
                ), style={'display': 'inline-block', 'width': '690px'}),

            # LINE
            html.Br(),
            interface_row2,
            html.Div(
                dash_apps_dev.apply_default_value(params)(dcc.Dropdown)(
                    id='topic',
                    options=[{'label': i, 'value': topic_dict[i]} for i in sorted(topic_dict)],
                    value='none',
                    placeholder="Select a topic",
                    style={'width': '190px'}
                ), style={'display': 'inline-block', 'width': '200px'}),

            html.Div(
                dash_apps_dev.apply_default_value(params)(dcc.Dropdown)(
                    id='order_by',
                    options=[{'label': i, 'value': features_dict[i]} for i in sorted(features_dict)],
                    value='none',
                    placeholder="Order by (optional)",
                    style={'width': '190px'}
                ), style={'display': 'inline-block', 'width': '200px'}),

            html.Div(
                dash_apps_dev.apply_default_value(params)(dcc.Dropdown)(
                    id='show_gaps',
                    options=[{'label': i, 'value': show_gaps_dict[i]} for i in sorted(show_gaps_dict)],
                    value='none',
                    placeholder="Show the gaps",
                    style={'width': '190px'}
                ), style={'display': 'inline-block', 'width': '200px'}),

            html.Div(
                dash_apps_dev.apply_default_value(params)(dcc.Input)(
                    id='limit',
                    placeholder='Enter a value...',
                    type='text',
                    value='100',
                    style={'width': '90px'}
                ), style={'display': 'inline-block', 'width': '100px'}),

            html.A(html.Button('Query Results!'),
                   href=''),

            # here there is the table
            html.Br(),
            html.Br(),

            html.Hr(),
            html.H5('Results'),
            dcc.Markdown(text_results.replace('  ', '')),

            html.Br(),
            html.H6(main_title, style={'textAlign': 'center'}),

            html.Table(
                # Header
                [html.Tr([html.Th(col) for col in columns])] +
                # Body
                [html.Tr([
                    html.Td(
                        (df_row[x]),
                        style={'font-size': "12px"}  # 'background-color':"lightblue"}
                    )
                    for x in range(len(columns))
                ]) for df_row in df_list]),

            footbar,

        ], className="container")
    #        print(str(datetime.timedelta(seconds=time.time() - functionstartTime))+' before printing')

    else:

        # PAGE 1: FIRST PAGE. NOTHING STARTED YET.
        layout = html.Div([
            navbar,
            html.H3('Map of Articles', style={'textAlign': 'center'}),
            html.Br(),
            dcc.Markdown(text_default.replace('  ', '')),

            # HERE GOES THE INTERFACE
            # LINE
            html.Br(),
            html.H5('Select the source'),
            interface_row1,

            html.Div(
                dash_apps_dev.apply_default_value(params)(dcc.Dropdown)(
                    id='source_lang',
                    options=[{'label': i, 'value': source_lang_dict[i]} for i in sorted(source_lang_dict)],
                    value='fr',
                    placeholder="Select languages",
                    style={'width': '190px'}
                ), style={'display': 'inline-block', 'width': '200px'}),
            #        dcc.Link('Query',href=""),

            html.Div(
                dash_apps_dev.apply_default_value(params)(dcc.Dropdown)(
                    id='target_langs',
                    options=[{'label': i, 'value': target_langs_dict[i]} for i in sorted(target_langs_dict)],
                    value=['es', 'ca'],
                    multi=True,
                    placeholder="Select languages",
                    style={'width': '670px'}
                ), style={'display': 'inline-block', 'width': '690px'}),

            # LINE
            html.Br(),
            interface_row2,
            html.Div(
                dash_apps_dev.apply_default_value(params)(dcc.Dropdown)(
                    id='topic',
                    options=[{'label': i, 'value': topic_dict[i]} for i in sorted(topic_dict)],
                    value='none',
                    placeholder="Select a topic",
                    style={'width': '190px'}
                ), style={'display': 'inline-block', 'width': '200px'}),

            html.Div(
                dash_apps_dev.apply_default_value(params)(dcc.Dropdown)(
                    id='order_by',
                    options=[{'label': i, 'value': features_dict[i]} for i in sorted(features_dict)],
                    value='none',
                    placeholder="Order by (optional)",
                    style={'width': '190px'}
                ), style={'display': 'inline-block', 'width': '200px'}),

            html.Div(
                dash_apps_dev.apply_default_value(params)(dcc.Dropdown)(
                    id='show_gaps',
                    options=[{'label': i, 'value': show_gaps_dict[i]} for i in sorted(show_gaps_dict)],
                    value='none',
                    placeholder="Show the gaps",
                    style={'width': '190px'}
                ), style={'display': 'inline-block', 'width': '200px'}),

            html.Div(
                dash_apps_dev.apply_default_value(params)(dcc.Input)(
                    id='limit',
                    placeholder='Enter a value...',
                    type='text',
                    value='100',
                    style={'width': '90px'}
                ), style={'display': 'inline-block', 'width': '100px'}),

            html.A(html.Button('Query Results!'),
                   href=''),
            footbar,
        ], className="container")

    return layout


def build_columns_and_query(columns, limit, order_by, source_lang, target_langs, topic, show_gaps):
    query = 'SELECT '
    query += 'r.qitem, r.page_id as page_id, r.page_title as page_title, r.num_editors, r.num_edits, r.num_pageviews, r.num_interwiki, r.num_bytes, r.date_created, '

    if order_by in ['num_outlinks', 'num_inlinks', 'num_wdproperty', 'num_discussions', 'num_inlinks_from_CCC',
                    'num_outlinks_to_CCC', 'num_references']:
        query += 'r.' + order_by + ', '
        columns = columns + [order_by]
    columns = columns + ['target_langs']
    # ADD title of each target lang
    for lang in target_langs:
        query += '{}wiki.page_title as {}title, '.format(lang,lang)
        columns = columns+[lang+'title']
    query += 'r.geocoordinates '

    query += ' FROM ' + source_lang + 'wiki r '
    # LEFT JOIN IF GAPS
    if show_gaps == 'one-gap-min' or show_gaps == 'only-gaps':
        for lang in target_langs:
            query += 'LEFT JOIN {}wiki ON r.qitem ={}wiki.qitem '.format(lang, lang)
    # Inner JOIN if NO GAPS
    if(show_gaps == 'no-gaps'):
        for lang in target_langs:
            query += 'INNER JOIN {}wiki ON r.qitem ={}wiki.qitem '.format(lang, lang)

    # WHERE
    query += 'WHERE r.geocoordinates IS NOT NULL  '
    if show_gaps == 'one-gap-min' or show_gaps == 'only-gaps':
        query += 'AND( '

        for i, lang in enumerate(target_langs):
            if i > 0:  # First iteration we dont add the AND/OR clause
                if (show_gaps == 'one-gap-min'):
                    query += ' OR '
                elif (show_gaps == 'only-gaps'):
                    query += ' AND '
            query += lang + '.qitem IS NULL '

        query += ') '

    if topic != "none" and topic != "None" and topic != "all":

        if topic == 'keywords':
            query += 'AND r.keyword_title IS NOT NULL '
        elif topic == 'medicine':
            query += 'AND r.medicine IS NOT NULL '
        elif topic == 'men':  # male
            query += 'AND r.gender = "Q6581097" '
        elif topic == 'women':  # female
            query += 'AND r.gender = "Q6581072" '
        elif topic == 'people':
            query += 'AND r.gender IS NOT NULL '
        elif topic == 'not_people':
            query += 'AND r.gender IS NULL '
        elif topic == 'ccc':
            query += 'AND r.ccc_binary = 1 AND percent_outlinks_to_CCC > 0.15 '
        elif topic == 'ccc_not_people':
            query += 'AND r.ccc_binary = 1 AND percent_outlinks_to_CCC > 0.15 AND r.gender IS NULL '
        else:
            query += 'AND r.' + topic + ' IS NOT NULL '
    # ORDER BY
    if order_by == "none" or order_by == "None":
        query += 'ORDER BY r.num_pageviews DESC '
    elif order_by in ['num_outlinks', 'num_wdproperty', 'num_discussions', 'num_inlinks_from_CCC',
                      'num_outlinks_to_CCC', 'num_references']:
        query += 'ORDER BY r.' + order_by + ' DESC '
    # LIMIT
    if limit != "none":
        query += 'LIMIT ' + str(limit * 10) + ';'
    else:
        query += 'LIMIT 500;'
    return columns, query


# callback update URL
component_ids_app19 = ['source_lang', 'target_langs', 'topic', 'order_by', 'show_gaps', 'limit']


@app.callback(Output('url', 'search'),
              inputs=[Input(i, 'value') for i in component_ids_app19])
def update_url_state(*values):
    #    print (values)

    if not isinstance(values[1], str):
        values = values[0], ','.join(values[1]), values[2], values[3], values[4], values[5]

    state = urlencode(dict(zip(component_ids_app19, values)))
    return '?' + state


#    return f'?{state}'

# callback update page layout
@app.callback(Output('page-content', 'children'),
              inputs=[Input('url', 'href')])
def page_load(href):
    if not href:
        return []
    state = dash_apps_dev.parse_state(href)
    return dash_app19_build_layout(state)
