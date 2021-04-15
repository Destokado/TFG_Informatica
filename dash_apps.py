import dash_html_components as html
import dash_bootstrap_components as dbc


last_period = '2020-05'


##### NAVBAR #####
#LOGO = "https://wcdo.wmflabs.org/assets/logo.png"
LOGO = "./assets/logo.png"
LOGO_foot = "./assets/wikimedia-logo.png"
# LOGO = app.get_asset_url('logo.png') # this would have worked. 

navbar = html.Div([
    html.Br(),
    dbc.Navbar(
        [ dbc.Collapse(
                dbc.Nav(
                    [
                    dbc.DropdownMenu(
                        [dbc.DropdownMenuItem("Top CCC Articles ", href="https://wcdo.wmflabs.org/top_ccc_articles/"),
                        dbc.DropdownMenuItem("Missing CCC ", href="https://wcdo.wmflabs.org/missing_ccc_articles/"),
                        dbc.DropdownMenuItem("Common CCC", href="https://wcdo.wmflabs.org/common_ccc_articles"),
                        dbc.DropdownMenuItem("Incomplete CCC", href="https://wcdo.wmflabs.org/incomplete_ccc_articles/"),
                        dbc.DropdownMenuItem("Search CCC ", href="https://wcdo.wmflabs.org/search_ccc_articles/"),
                        dbc.DropdownMenuItem("Visual CCC ", href="https://wcdo.wmflabs.org/visual_ccc_articles/"),
                        ],
                        label="Tools",
                        nav=True,
                    ),
                    dbc.DropdownMenu(
                        [dbc.DropdownMenuItem("Local Content / CCC", href="https://wcdo.wmflabs.org/cultural_context_content/"),
                        dbc.DropdownMenuItem("Cultural Gap (CCC Coverage)", href="https://wcdo.wmflabs.org/ccc_coverage/"),
                        dbc.DropdownMenuItem("Cultural Gap (CCC Spread)", href="https://wcdo.wmflabs.org/ccc_spread/"),
                        dbc.DropdownMenuItem("Geography Gap", href="https://wcdo.wmflabs.org/geography_gap/"),
                        dbc.DropdownMenuItem("Gender Gap", href="http://wcdo.wmflabs.org/gender_gap/"),
                        dbc.DropdownMenuItem("Topical Coverage", href="https://wcdo.wmflabs.org/topical_coverage/"),
                        dbc.DropdownMenuItem("Last Month Pageviews", href="https://wcdo.wmflabs.org/last_month_pageviews/"),
                        dbc.DropdownMenuItem("Diversity Over Time", href="https://wcdo.wmflabs.org/diversity_over_time/"),
                        dbc.DropdownMenuItem("Languages Top CCC Articles Coverage", href="https://wcdo.wmflabs.org/languages_top_ccc_articles_coverage/"),
                        dbc.DropdownMenuItem("Countries Top CCC Articles Coverage", href="https://wcdo.wmflabs.org/countries_top_ccc_articles_coverage/"),
                        dbc.DropdownMenuItem("Languages Top CCC Articles Spread", href="https://wcdo.wmflabs.org/languages_top_ccc_articles_spread/")],
                        label="Visualizations",
                        nav=True,
                    ),
                    html.A(
                    # Use row and col to control vertical alignment of logo / brand
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src=LOGO, height="35px")),
    #                        dbc.Col(dbc.NavbarBrand("Wikipedia Diversity Observatory", className="mb-5")),
                        ],
                        align="center",
                        no_gutters=True,
                    ),
                    href="https://meta.wikimedia.org/wiki/Wikipedia_Cultural_Diversity_Observatory", target= "_blank",
                style = {'margin-left':"5px"}),
                ], className="ml-auto", navbar=True),
                id="navbar-collapse2",
                navbar=True,
            ),
        ],
        color="white",
        dark=False,
        className="ml-2",
    ),
    ])


##### FOOTBAR #####
footbar = html.Div([
        html.Br(),
        html.Br(),
        html.Hr(),

        html.Div(
            dbc.Nav(
                [
                    dbc.NavLink("Diversity Observatory Meta-Wiki Page", href="https://meta.wikimedia.org/wiki/Wikipedia_Cultural_Diversity_Observatory", target="_blank", style = {'color': '#8C8C8C'}),
                    dbc.NavLink("View Source", href="https://github.com/marcmiquel/wcdo", style = {'color': '#8C8C8C'}),
                    dbc.NavLink("Datasets/Databases", href="https://meta.wikimedia.org/wiki/Wikipedia_Cultural_Diversity_Observatory/Cultural_Context_Content#Datasets", style = {'color': '#8C8C8C'}),
                    dbc.NavLink("Research", href="https://meta.wikimedia.org/wiki/Wikipedia_Cultural_Diversity_Observatory/Cultural_Context_Content#References", style = {'color': '#8C8C8C'}),
                ], className="ml-2"), style = {'textAlign': 'center', 'display':'inline-block' , 'width':'60%'}),

        html.Div(id = 'current_data', children=[        
            'Updated with dataset from: ',
            html.B(last_period)],
#            html.B(current_dataset_period_stats)],
            style = {'textAlign':'right','display': 'inline-block', 'width':'40%'}),
        html.Br(),
        html.Div([
            html.P('Hosted with ♥ on ',style = {'display':'inline-block'}),
            html.A('Wikimedia Cloud VPS',href='https://wikitech.wikimedia.org/wiki/Portal:Cloud_VPS', target="_blank", style = {'display':'inline-block'}),
            html.P('.',style = {'display':'inline-block', 'margin-right':"5px"}),
            html.A(html.Img(src=LOGO_foot, height="35px"),href='https://wikitech.wikimedia.org/wiki/Help:Cloud_Services_Introduction', target="_blank", style = {'display':'inline-block'}),

            ], style = {'textAlign':'right'}
            ),
        html.Br(),
    ])


