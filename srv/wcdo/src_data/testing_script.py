# -*- coding: utf-8 -*-

# script
import wikilanguages_utils
from wikilanguages_utils import *
# time
import time
import datetime
from dateutil import relativedelta
import calendar
# system
import os
import sys
import shutil
import re
import random
# databases
import MySQLdb as mdb, MySQLdb.cursors as mdb_cursors
import sqlite3
# files
import gzip
import zipfile
import bz2
import json
import csv
import codecs
import unidecode
# requests and others
import requests
import urllib
from urllib.parse import urlparse, parse_qsl, urlencode
import webbrowser
import reverse_geocoder as rg
import numpy as np
# data
import pandas as pd
# classifier
from sklearn import svm, linear_model
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import gc

import xlsxwriter




def dash_app7_build_layout(params):
    features_dict = {'Number of Editors':'num_editors','Number of Edits':'num_edits','Number of Images':'num_images','Wikirank':'wikirank','Number of Pageviews':'num_pageviews','Number of Inlinks':'num_inlinks','Number of References':'num_references','Number of Bytes':'num_bytes','Number of Outlinks':'num_outlinks','Number of Interwiki':'num_interwiki','Number of WDProperties':'num_wdproperty','Number of Discussions':'num_discussions','Creation Date':'date_created','Number of Inlinks from CCC':'num_inlinks_from_CCC'}

    lists_dict = {'Editors':'editors','Featured':'featured','Geolocated':'geolocated','Keywords':'keywords','Women':'women','Men':'men','Created First Three Years':'created_first_three_years','Created Last Year':'created_last_year','Pageviews':'pageviews','Discussions':'discussions','Edits':'edits', 'Edited Last Month':'edited_last_month', 'Images':'images', 'WD Properties':'wdproperty_many', 'Interwiki':'interwiki_many', 'Least Interwiki Most Editors':'interwiki_editors', 'Least Interwiki Most WD Properties':'interwiki_wdproperty', 'Wikirank':'wikirank', 'Wiki Loves Earth':'earth', 'Wiki Loves Monuments':'monuments_and_buildings', 'Wiki Loves Sports':'sport_and_teams', 'Wiki Loves GLAM':'glam', 'Wiki Loves Folk':'folk', 'Wiki Loves Music':'music_creations_and_organizations', 'Wiki Loves Food':'food', 'Wiki Loves Paintings':'paintings', 'Wiki Loves Books':'books', 'Wiki Loves Clothing and Fashion':'clothing_and_fashion', 'Wiki Loves Industry':'industry', 'Wiki Loves Religion':'religion', 'Religious Group':'religious_group','LGBT+':'sexual_orientation','Ethnic Group':'ethnic_group'}


    list_dict_inv = {v: k for k, v in lists_dict.items()}


    if len(params)!=0 and params['source_lang'].lower()!='none' and params['target_lang']!='none':


        if params['list'].lower()=='none':
            list_name='editors'
        else:
            list_name=params['list'].lower()
    
        source_lang=params['source_lang'].lower()
        target_lang=params['target_lang'].lower()

        if 'source_country' in params:
            country=params['source_country'].upper()
            if country == 'NONE' or country == 'ALL': country = 'all'
        else:
            country = 'all'

        if 'exclude' in params:
            exclude_articles=params['exclude'].lower()
        else:
            exclude_articles='none'

        if 'order_by' in params:
            order_by=params['order_by']#.lower()
        else:
            order_by='none'

        source_language = languages.loc[source_lang]['languagename']
        target_language = languages.loc[target_lang]['languagename']


    #    lists = ['editors','featured','geolocated','keywords','women','men','created_first_three_years','created_last_year','pageviews','discussions']

        conn = sqlite3.connect(databases_path + 'top_diversity_articles_production.db'); cur = conn.cursor()

        columns_dict = {'position':'Nº','page_title_original':'Article Title','num_editors':'Editors','num_edits':'Edits','num_pageviews':'Pageviews','num_bytes':'Bytes','num_images':'Images','wikirank':'Wikirank','num_references':'References','num_inlinks':'Inlinks','num_wdproperty':'Wikidata Properties','num_interwiki':'Interwiki Links','featured_article':'Featured Article','num_discussions':'Discussions','date_created':'Creation Date','num_inlinks_from_CCC':'Inlinks from CCC','related_languages':'Related Languages','page_title_target':' Article Title'}

        columns_dict_abbr = {'References':'Refs.', 'Pageviews':'PV', 'Editors':'Edtrs','num_inlinks':'Inlinks','Wikidata Properties':'WD.P.','Interwiki Links':'IW.L.','Featured Article':'F.A.','Creation Date':'Created','Inlinks from CCC':'IL CCC','Related Languages':'Rel. Lang.','Ethnic Group':'Ethnia','Religious Group':'Religion'}

        # falten introduïr les columnes de sexual orientation, ethnic group i religious group.

        # COLUMNS
        query = 'SELECT r.qitem, f.page_title_original, '
        columns = ['Nº','Article Title']

        if list_name == 'editors': 
            query+= 'f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'featured': 
            query+= 'f.featured_article, f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki,  '
            columns+= ['Featured Article','Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'geolocated': 
            query+= 'f.num_inlinks, f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Inlinks','Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'keywords': 
            query+= 'f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.featured_article, f.num_wdproperty, f.num_interwiki,  '
            columns+= ['Editors','Pageviews','Bytes','References','Featured Article','Wikidata Properties','Interwiki Links']

        if list_name == 'women': 
            query+= 'f.num_edits, f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Edits','Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'men': 
            query+= 'f.num_edits, f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Edits','Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'sexual_orientation': 

            query+= 'f.num_edits, f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_interwiki, f.sexual_orientation, '
            columns+= ['Edits','Editors','Pageviews','Bytes','References','Interwiki Links','LGBT+']

        if list_name == 'ethnic_group': 

            query+= 'f.num_edits, f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_interwiki, f.ethnic_group, '
            columns+= ['Edits','Editors','Pageviews','Bytes','References','Interwiki Links', 'Ethnic Group']

        if list_name == 'religious_group': 

            query+= 'f.num_edits, f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_interwiki, f.religious_group, '
            columns+= ['Edits','Editors','Pageviews','Bytes','References','Interwiki Links', 'Religious Group']

        if list_name == 'created_first_three_years': 
            query+='f.num_editors, f.num_pageviews, f.num_edits, f.num_references, f.featured_article, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Edits','References','Featured Article','Wikidata Properties','Interwiki Links']

        if list_name == 'created_last_year': 
            query+='f.num_editors, f.num_pageviews, f.num_edits, f.num_references, f.featured_article, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Edits','References','Featured Article','Wikidata Properties','Interwiki Links']

        if list_name == 'pageviews': 
            query+='f.num_pageviews, f.num_edits, f.num_bytes, f.num_references, f.featured_article, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Pageviews','Edits','Bytes','References','Featured Article','Wikidata Properties','Interwiki Links']

        if list_name == 'discussions': 
            query+='f.num_discussions, f.num_pageviews, f.num_edits, f.num_bytes, f.num_references, f.featured_article, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Discussions','Pageviews','Edits','Bytes','References','Featured Article','Wikidata Properties','Interwiki Links']

        if list_name == 'edits': 
            query+='f.num_edits, f.num_bytes, f.num_discussions, f.num_pageviews, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Edits','Discussions','Bytes','Pageviews','References','Wikidata Properties','Interwiki Links']

        if list_name == 'edited_last_month': 
            query+='f.num_edits, f.num_bytes, f.num_discussions, f.num_pageviews, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Edits','Bytes','Discussions','Pageviews','References','Wikidata Properties','Interwiki Links']

        if list_name == 'images': 
            query+='f.num_images, f.num_bytes, f.num_edits, f.num_pageviews, f.num_references, f.featured_article, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Images','Bytes','Edits','Pageviews','References','Featured Article','Wikidata Properties','Interwiki Links']

        if list_name == 'wdproperty_many': 
            query+= 'f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'interwiki_many': 
            query+= 'f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'interwiki_editors': 
            query+= 'f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'interwiki_wdproperty': 
            query+= 'f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'wikirank': 
            query+= 'f.wikirank, f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Wikirank','Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'earth': 
            query+= 'f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'monuments_and_buildings': 
            query+= 'f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'sport_and_teams': 
            query+= 'f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'glam': 
            query+= 'f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'folk': 
            query+= 'f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'music_creations_and_organizations': 
            query+= 'f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'food': 
            query+= 'f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'paintings': 
            query+= 'f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'books': 
            query+= 'f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'clothing_and_fashion': 
            query+= 'f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'industry': 
            query+= 'f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']

        if list_name == 'religion': 
            query+= 'f.num_editors, f.num_pageviews, f.num_bytes, f.num_references, f.num_wdproperty, f.num_interwiki, '
            columns+= ['Editors','Pageviews','Bytes','References','Wikidata Properties','Interwiki Links']



        if order_by != 'none':
            feat = columns_dict[order_by]
            if feat not in columns:
                columns+= [feat]
                query+= 'f.'+order_by+', '

#        print (columns)

        # NEW LISTS
        query += 'f.num_inlinks_from_CCC, f.date_created, p.page_title_target, p.generation_method, p0.page_title_target pt0, p0.generation_method pg0, p1.page_title_target pt1, p1.generation_method pg1, p2.page_title_target pt2, p2.generation_method pg2, p3.page_title_target pt3, p3.generation_method pg3 '

        if 'Inlinks from CCC' not in columns: columns+= ['Inlinks from CCC']
        columns+= ['Creation Date']
        columns+= ['Related Languages',' Article Title']
#        columns= list(dict.fromkeys(columns))

        query += 'FROM '+source_lang+'wiki_top_articles_lists r '
        query += 'LEFT JOIN '+target_lang+'wiki_top_articles_page_titles p USING (qitem) '
        query += 'LEFT JOIN '+closest_langs[target_lang][0]+'wiki_top_articles_page_titles p0 USING (qitem) '
        query += 'LEFT JOIN '+closest_langs[target_lang][1]+'wiki_top_articles_page_titles p1 USING (qitem) '
        query += 'LEFT JOIN '+closest_langs[target_lang][2]+'wiki_top_articles_page_titles p2 USING (qitem) '
        query += 'LEFT JOIN '+closest_langs[target_lang][3]+'wiki_top_articles_page_titles p3 USING (qitem) '
        query += 'INNER JOIN '+source_lang+'wiki_top_articles_features f USING (qitem) '
        query += "WHERE r.list_name = '"+list_name+"' "
        if country: query += 'AND r.country IS "'+country+'" '

        if exclude_articles == 'existing': 
            query += 'AND p.generation_method != "sitelinks" '
        elif exclude_articles == 'non-existing':
            query += 'AND p.generation_method = "sitelinks" '


        if order_by != 'none':
            query += 'ORDER BY f.'+order_by+' DESC;'
        else:
            query += 'ORDER BY r.position ASC;'


        # print (query)
        # print (columns)

        df = pd.read_sql_query(query, conn)#, parameters)
        df = df.fillna(0)
        # print (df.columns)

        if country == 'all':
            main_title = source_language + ' Top CCC articles list "'+list_dict_inv[list_name]+'" and its coverage by '+target_language+' Wikipedia'

            source_country = ' '
        else:
            source_country = country_names[country]

            main_title = source_language + ' Top CCC articles list "'+list_dict_inv[list_name]+'" related to '+source_country+' and its coverage by '+target_language+' Wikipedia'
            source_country = '('+source_country+')'

        results_text = '''
        The following table shows the Top 500 articles list '''+list_dict_inv[list_name] + ''' from '''+source_language+''' CCC '''+source_country+''' and its article availability in '''+target_language+''' Wikipedia. The columns present complementary features that are explicative of the article relevance (number of editors, edits, pageviews, Bytes, Wikidata properties or Interwiki links). In particular, number of Inlinks from CCC (incoming links from the CCC group of articles) highlights the article importance in terms of how much it is required by other articles. The column named Related Languages present Interwiki links to the article version when available in the four languages closer to the target language (those that cover best this language and therefore it is likely their editors consult it).

        The table's last column shows the article title in its target language, in ***blue*** when it exists, in ***red*** as a proposal generated with the Wikimedia Content Translation tool or as an existing Wikidata label in the same language, and ***empty*** when the article does not exist or there is no title proposal available. This column is *updated once per day* with the new articles created.
        '''    



        closest_languages = closest_langs[target_lang]
        page_titles_target = ['pt0','pt1','pt2','pt3']
        generation_method_target = ['pg0','pg1','pg2','pg3']
        cl = len(closest_languages)




        k = 0
        # print (df.columns)

        df=df.rename(columns=columns_dict)



        conn = sqlite3.connect(databases_path + 'wikipedia_diversity_production.db'); cur = conn.cursor()
        qitems = df.qitem.tolist()
        page_asstring = ','.join( ['?'] * len(qitems) )
        query = 'SELECT qitem, page_id FROM '+source_lang+'wiki WHERE qitem IN (%s);' % page_asstring
        dfx = pd.read_sql_query(query, conn, params = qitems)#, parameters)
        dfx = dfx.set_index('qitem')
        qitems_page_ids = dfx.to_dict()['page_id']

        df['page_id'] = df['qitem'].map(qitems_page_ids).fillna(0)
        df['page_id'] = df['page_id'].astype(int)

        target_languages = closest_languages
        target_languages.insert(0,target_lang)
        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(source_lang); mysql_cur_read = mysql_con_read.cursor()
        df = wikilanguages_utils.get_interwikilinks_articles(source_lang, target_languages, df, mysql_con_read)






        # group labels
        if list_name in ('sexual_orientation', 'ethnic_group', 'religious_group'):
            if list_name != sexual_orientation: list_name+='s'

            qitem_labels_target_lang = group_labels.loc[(group_labels["lang"] == target_lang) & (group_labels["category_label"] == list_name)][['qitem','label','lang']]
            qitem_labels_en = group_labels.loc[(group_labels["lang"] == "en") & (group_labels["category_label"] == list_name)][['qitem','label','lang']]

            qitem_labels_en = qitem_labels_en.set_index('qitem')
            qitem_labels_target_lang = qitem_labels_target_lang.set_index('qitem')

            qitem_labels_en = qitem_labels_en['label'].str.replace('_',' ')
            qitem_labels_target_lang = qitem_labels_target_lang['label'].str.replace('_',' ')

            # print (len(qitems_labels))
            # print (qitems_labels.head(10))

        tl = target_lang.replace('_','-')

        df_list = list()

        df_list_wt = list()
        for index, rows in df.iterrows():
            df_row = list()
            df_row_wt = list()

            for col in columns:

                l = columns_excel[columns.index(col)]
                pos = l+str(k)

                if col == 'Nº':
                    k+=1
                    df_row.append(str(k))
                    df_row_wt.append(str(k))

                elif col == 'Featured Article': 
                    fa = rows['Featured Article']
                    if fa == 0:
                        df_row.append('No')
                        df_row_wt.append('No')
                        worksheet.write(pos, u'No')

                    else:
                        df_row.append('Yes')
                        df_row_wt.append('Yes')
                        worksheet.write(pos, u'Yes')

                elif col == 'Interwiki Links':
                    df_row.append(html.A( rows['Interwiki Links'], href='https://www.wikidata.org/wiki/'+rows['qitem'], target="_blank", style={'text-decoration':'none'}))
                    df_row_wt.append('[[wikidata:'+rows['qitem']+'|'+str(rows['Interwiki Links'])+']]')
                    worksheet.write_url(pos, 'https://www.wikidata.org/wiki/'+str(rows['qitem']), string=str(rows['Interwiki Links']))

                elif col == 'Inlinks':
                    df_row.append(html.A( rows['Inlinks'], href='https://'+source_lang+'.wikipedia.org/wiki/Special:WhatLinksHere/'+rows['Article Title'].replace(' ','_'), target="_blank", style={'text-decoration':'none'}))
                    df_row_wt.append('[[:'+source_lang+':Special:WhatLinksHere/'+rows['Article Title'].replace(' ','_')+'|'+str(rows['Inlinks'])+']]')
                    worksheet.write_url(pos, 'https://'+source_lang+'.wikipedia.org/wiki/Special:WhatLinksHere/'+rows['Article Title'].replace(' ','_'), string=str(rows['Inlinks']))

                elif col == 'Inlinks from CCC':
                    df_row.append(html.A( rows['Inlinks from CCC'], href='https://'+source_lang+'.wikipedia.org/wiki/Special:WhatLinksHere/'+rows['Article Title'].replace(' ','_'), target="_blank", style={'text-decoration':'none'}))
                    df_row_wt.append('[[:'+source_lang+':Special:WhatLinksHere/'+rows['Article Title'].replace(' ','_')+'|'+str(rows['Inlinks from CCC'])+']]')
                    worksheet.write_url(pos, 'https://'+source_lang+'.wikipedia.org/wiki/Special:WhatLinksHere/'+rows['Article Title'].replace(' ','_'), string=str(rows['Inlinks from CCC']))


                elif col == 'Editors':
                    df_row.append(html.A( rows['Editors'], href='https://'+source_lang+'.wikipedia.org/w/index.php?title='+rows['Article Title'].replace(' ','_')+'&action=history', target="_blank", style={'text-decoration':'none'}))
                    df_row_wt.append('[[:'+source_lang+':'+rows['Article Title'].replace(' ','_')+'|'+str(rows['Editors'])+']]')

                    worksheet.write_url(pos, 'https://'+source_lang+'.wikipedia.org/w/index.php?title='+rows['Article Title'].replace(' ','_')+'&action=history', string=str(rows['Editors']))

                elif col == 'Edits':
                    df_row.append(html.A( rows['Edits'], href='https://'+source_lang+'.wikipedia.org/w/index.php?title='+rows['Article Title'].replace(' ','_')+'&action=history', target="_blank", style={'text-decoration':'none'}))

                    df_row_wt.append('[[:'+source_lang+':'+rows['Article Title'].replace(' ','_')+'|'+str(rows['Edits'])+']]')
                    worksheet.write_url(pos, 'https://'+source_lang+'.wikipedia.org/w/index.php?title='+rows['Article Title'].replace(' ','_')+'&action=history', string=str(rows['Edits']))

                elif col == 'Discussions':
                    df_row.append(html.A( rows['Discussions'], href='https://'+source_lang+'.wikipedia.org/wiki/Talk:'+rows['Article Title'].replace(' ','_'), target="_blank", style={'text-decoration':'none'}))
                    df_row_wt.append('[[:'+source_lang+':'+rows['Article Title'].replace(' ','_')+'|'+str(rows['Discussions'])+']]')

                    worksheet.write_url(pos, 'https://'+source_lang+'.wikipedia.org/wiki/Talk:'+rows['Article Title'].replace(' ','_'), string=str(rows['Discussions']))


                elif col == 'Wikirank':
                    df_row.append(html.A( rows['Wikirank'], href='https://wikirank.net/'+source_lang+'/'+rows['Article Title'], target="_blank", style={'text-decoration':'none'}))
                    df_row_wt.append(str(rows['Wikirank']))
                    worksheet.write_url(pos, 'https://wikirank.net/'+source_lang+'/'+rows['Article Title'], string=str(rows['Wikirank']))

                elif col == 'Pageviews':
                    df_row.append(html.A( rows['Pageviews'], href='https://tools.wmflabs.org/pageviews/?project='+source_lang+'.wikipedia.org&platform=all-access&agent=user&range=latest-20&pages='+rows['Article Title'].replace(' ','_')+'&action=history', target="_blank", style={'text-decoration':'none'}))
                    df_row_wt.append(str( int(rows['Pageviews'])))
                    worksheet.write_url(pos, 'https://tools.wmflabs.org/pageviews/?project='+source_lang+'.wikipedia.org&platform=all-access&agent=user&range=latest-20&pages='+rows['Article Title'].replace(' ','_')+'&action=history', string=str(rows['Pageviews']))


                elif col == 'Wikidata Properties':
                    df_row.append(html.A( rows['Wikidata Properties'], href='https://www.wikidata.org/wiki/'+rows['qitem'], target="_blank", style={'text-decoration':'none'}))
                    df_row_wt.append('[[wikidata:'+rows['qitem']+'|'+str(rows['Wikidata Properties'])+']]')
                    worksheet.write_url(pos, 'https://www.wikidata.org/wiki/'+str(rows['qitem']), string=str(rows['Wikidata Properties']))

                elif col == 'LGBT+' or col == 'Ethnic Group' or col == 'Religious Group':

                    if col == 'LGBT+':
                        qit = str(rows['sexual_orientation'])
                    elif col == 'Religious Group':
                        qit = str(rows['religious_group'])
                    elif col == 'Ethnic Group':
                        qit = str(rows['ethnic_group'])

                    if ';' in qit:
                        qlist = qit.split(';')
                    else:
                        qlist = [qit]

                    c = len(qlist)

                    text = ''
                    text_ex = ''
                    text_wt = ''

                    i = 0
                    for ql in qlist:
                        i+= 1
                        try:
                            label = qitem_labels_target_lang.loc[ql]
                            text+= '['+label+']'+'('+'http://'+target_lang+'.wikipedia.org/wiki/'+ label.replace(' ','_')+')'
                            text_wt+= '[[:'+tl+':|'+label.replace(' ','_')+']]'
                        except:                            
                            try:
                                label = qitem_labels_en.loc[ql]
                                text+= '['+label+' (en)'+']'+'('+'http://en.wikipedia.org/wiki/'+ label.replace(' ','_')+')'
                                text_wt+= '[[:'+tl+':|'+label.replace(' ','_')+']]'

                            except:
                                label = ql
                                text+= '['+label+']'+'('+'https://www.wikidata.org/wiki/'+ label+')'
                                text_wt+= '[[wikidata:'+label+'|'+label+']]'

                        if i<c:
                            text+=', '
                            text_ex+=', '
                            text_wt+=', '

                    df_row.append(dcc.Markdown(text))
                    df_row_wt.append(text_wt)
                    worksheet.write(pos, text_ex)

                elif col == 'Related Languages':
                    i = 0
                    text = ''
                    text_ex = ''
                    text_wt = ''

                    for x in range(cl):
                        cur_generation_method = rows[generation_method_target[x]]
                        if cur_generation_method != 'sitelinks': continue
                        cur_title = rows[page_titles_target[x]]
                        try:
                            cur_title = cur_title.decode('utf-8')
                        except:
                            pass

                        if cur_title!= 0:
                            if i!=0 and i!=cl:
                                text+=', '
                                text_ex+=', '
                                text_wt+=', '

                            text+= '['+closest_languages[x]+']'+'('+'http://'+closest_languages[x]+'.wikipedia.org/wiki/'+ cur_title.replace(' ','_')+')'
                            text_wt+= '[[:'+closest_languages[x]+':'+cur_title.replace(' ','_')+'|'+closest_languages[x]+']]'

                            #+'{:target="_blank"}'
                            text_ex+= closest_languages[x]
                            i+=1


                    df_row.append(dcc.Markdown(text))
                    df_row_wt.append(text_wt)
                    worksheet.write(pos, text_ex)

                elif col == 'Bytes':
#                    print (rows[col])
                    value = round(float(int(rows[col])/1000),1)
                    df_row.append(str(value)+'k')
                    df_row_wt.append('[[:'+source_lang+':'+rows['Article Title'].replace(' ','_')+'|'+str(value)+'k]]')
                    worksheet.write(pos, str(value)+'k')

                elif col == 'Images':
                    title = rows['Article Title']
                    df_row.append(html.A(str(rows[col]), href='https://'+source_lang+'.wikipedia.org/wiki/'+title.replace(' ','_'), target="_blank", style={'text-decoration':'none'}))
                    df_row_wt.append('[[:'+source_lang+':'+title+'|'+str(rows[col])+']]')
                    worksheet.write_url(pos, 'https://'+source_lang+'.wikipedia.org/wiki/'+title.replace(' ','_'), string=str(rows['Images']))


                elif col == 'Creation Date':
                    date = rows[col]
                    if date == 0: 
                        date = ''
                    else:
                        date = str(time.strftime("%Y-%m-%d", time.strptime(str(int(date)), "%Y%m%d%H%M%S")))
                    df_row.append(date)
                    df_row_wt.append(date)
                    worksheet.write(pos, date)

                elif col == 'Article Title':
                    title = rows['Article Title']
                    df_row.append(html.A(title.replace('_',' '), href='https://'+source_lang+'.wikipedia.org/wiki/'+title.replace(' ','_'), target="_blank", style={'text-decoration':'none'}))
                    df_row_wt.append('[[:'+source_lang+':'+title+'|'+title.replace('_',' ')+']]')
                    worksheet.write_url(pos, 'https://'+source_lang+'.wikipedia.org/wiki/'+title.replace(' ','_'), string=title)

                elif col == ' Article Title':
                    cur_title = rows[' Article Title']
                    if cur_title != 0:
                        try:
                            cur_title = cur_title.decode('utf-8')
                        except:
                            pass
                        cur_title = cur_title.replace('_',' ')
                        if rows['generation_method'] == 'sitelinks':
                            df_row.append(html.A(cur_title, href='https://'+target_lang+'.wikipedia.org/wiki/'+cur_title.replace(' ','_'), target="_blank", style={'text-decoration':'none'}))
                            df_row_wt.append('[[:'+tl+':'+cur_title+'|'+cur_title+']]')
                            worksheet.write_url(pos, 'https://'+target_lang+'.wikipedia.org/wiki/'+cur_title.replace(' ','_'), string=cur_title)
                        else:
                            df_row.append(html.A(cur_title+' ('+rows['generation_method']+')',href='https://'+target_lang+'.wikipedia.org/wiki/'+cur_title.replace(' ','_'), target="_blank", style={'text-decoration':'none',"color":"#ba0000"}))
                            df_row_wt.append('[[:'+tl+':'+cur_title+'|'+cur_title+']]')

                    else:
                        df_row.append('')
                        df_row_wt.append('')


                else:
                    df_row.append(rows[col])
                    # print (col)
                    # print (rows[col])
                    df_row_wt.append(rows[col])
                    worksheet.write(pos,rows[col])

            df_list.append(df_row)

            # print (df_row_wt)
            # print (len(df_row_wt))
            df_list_wt.append(df_row_wt)


        workbook.close()

        col_len = len(columns)
        columns[1]=source_language+' '+columns[1]
        columns[col_len-1]=target_language+columns[col_len-1]


        df1 = pd.DataFrame(df_list_wt)
        df1.columns = columns
        todelete = ['Nº','IL CCC']
        if 'Wikidata Properties' in columns: todelete.append('WD.P.')
        df1=df1.rename(columns=columns_dict_abbr)
        df1=df1.drop(columns=todelete)







# MAIN
def main():



    # target_lang=ca&source_country=none&list=women&order_by=none&exclude=none&source_lang=ro

    params = {'source_lang': 'ro', 'source_country':'none', 'target_lang': 'ca', 'order_by': 'none', 'exclude': 'none', 'list':'women', 'limit': '100'}

    dash_app7_build_layout(params)

    input('')
    input('')
    input('')



    params = {'source_lang': 'fr', 'target_langs': 'es,ast,br,eu', 'topic': 'none', 'order_by': 'none', 'show_gaps': 'none', 'limit': '100'}

    print (params)

    conn = sqlite3.connect(databases_path + 'wikipedia_diversity_production.db'); cur = conn.cursor()

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


    # CREATING THE QUERY FROM THE PARAMS
    query = 'SELECT '
    query += 'r.qitem, '

#        query += 'REPLACE(r.page_title,"_"," ") as r.page_title, '
    query += 'r.page_id as page_id, r.page_title as page_title, '

    query += 'r.num_editors, r.num_edits, r.num_pageviews, r.num_interwiki, r.num_bytes, r.date_created, '

    columns = ['num','qitem','page_title','num_editors','num_edits','num_pageviews','num_interwiki','num_bytes','date_created','lgbt_topic']

    if order_by in ['num_outlinks','num_inlinks','num_wdproperty','num_discussions','num_inlinks_from_CCC','num_outlinks_to_CCC','num_references']: 
        query += 'r.'+order_by+', '
        columns = columns + [order_by]

    query += 'r.lgbt_topic '

    query += ' FROM '+source_lang+'wiki r '
    query += 'WHERE r.lgbt_topic > 0 '


    if topic != "none" and topic != "None" and topic != "all":
        if topic == 'keywords':
            query += 'AND r.lgbt_keyword_title IS NOT NULL '
        elif topic == 'geolocated':
            query += 'AND (r.geocoordinates IS NOT NULL OR r.location_wd IS NOT NULL) '
        elif topic == 'men': # male
            query += 'AND r.gender = "Q6581097" '
        elif topic == 'women': # female
            query += 'AND r.gender = "Q6581072" '
        elif topic == 'people':
            query += 'AND r.gender IS NOT NULL '
        elif topic == 'not_people':
            query += 'AND r.gender IS NULL '
        else:
            query += 'AND r.'+topic+' IS NOT NULL '


    if order_by == "none" or order_by == "None":
#            pass
        query += 'ORDER BY r.lgbt_topic DESC '

    elif order_by in ['num_outlinks','num_wdproperty','num_discussions','num_inlinks_from_CCC','num_outlinks_to_CCC','num_references','num_pageviews']: 
        query += 'ORDER BY r.'+order_by+' DESC '

    if limit == "none":
        query += 'LIMIT 500;'
    else:
        query += 'LIMIT 500;'
        # query += 'LIMIT '+str(limit)+';'


    columns = columns + ['target_langs']
    print (query)


    df = pd.read_sql_query(query, conn)#, parameters)
    print (df.head(10))


    df = df.head(limit)
    mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(source_lang); mysql_cur_read = mysql_con_read.cursor()
    df = wikilanguages_utils.get_interwikilinks_articles(source_lang, target_langs, df, mysql_con_read)
    print (df.head(100))



    df.to_csv('lgbt.csv')

    input('')

    df = pd.read_csv(databases_path + 'lgbt.csv')

    print (df.head(10))
    print(str(datetime.timedelta(seconds=time.time() - functionstartTime))+' after queries.')





    """
    df = df.head(limit)
    mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(source_lang); mysql_cur_read = mysql_con_read.cursor()
    df = wikilanguages_utils.get_interwikilinks_articles(sourcelang, target_langs, df, mysql_con_read)
    """



    input('')



    functionstartTime = time.time()
    languagecode = 'en'
    edittypes = 'all_edits'
    editortypes = 'all_editors'
    periodhours = 1
    resultslimit = 50000
    category = 'ccc_binary'
    df_rc = get_recent_articles_recent_edits(languagecode, edittypes, editortypes, periodhours, resultslimit)
    print (len(df_rc))

    df_rc_categories = get_articles_diversity_categories_wikipedia_diversity_db(languagecode, df_rc)
#    df_rc_categories.to_csv('df_rc_categories_sample.csv')
    df = df_rc_categories

    print (len(df))
    print (df.head(10))
    print(str(datetime.timedelta(seconds=time.time() - functionstartTime))+' after queries.')





################################################################
# Get me the recent created articles or recent edits (Filter: Bot, New)
def get_recent_articles_recent_edits(languagecode, edittypes, editortypes, periodhours, resultslimit):
    functionstartTime = time.time()
    print (languagecode, edittypes, editortypes, periodhours, resultslimit)

    def conditions(s):
        if (s['rc_bot'] == 1):
            return 'bot'
        elif (s['rev_actor'] == 'NULL'):
            return 'anonymous'
        else:
            return 'editor'


    query = 'SELECT CONVERT(rc_title USING utf8mb4) as page_title, rc_cur_id as page_id, CONVERT(rc_timestamp USING utf8mb4) as rc_timestamp, rc_bot, rev_actor, rc_new_len as Bytes, CONVERT(actor_name USING utf8mb4) as actor_name FROM recentchanges rc INNER JOIN revision rv ON rc.rc_timestamp = rv.rev_timestamp INNER JOIN actor a ON rv.rev_actor = a.actor_id WHERE rc_namespace = 0 '
#    query = 'SELECT CONVERT(rc_title USING utf8mb4) as page_title, rc_cur_id as page_id, rc_new, rc_type, rc_deleted, rc_bot, CONVERT(rc_timestamp USING utf8mb4) as rc_timestamp FROM recentchanges WHERE rc_namespace = 0 '

    if edittypes == 'new_articles': 
        query += 'AND rc_new = 1 '

    if edittypes == 'wikidata_edits': 
        query += 'AND rc_type = 5 '

    if editortypes == 'no_bots':
        query+= 'AND rc_bot = 0 '

    if editortypes == 'bots_edits':
        query+= 'AND rc_bot = 1 '

    if editortypes == 'anonymous_edits':
        query+= 'AND actor_user IS NULL '

    if editortypes == 'editors_edits':
        query+= 'AND rc_bot = 0 '
        query+= 'AND actor_user IS NOT NULL '


    timelimit = datetime.datetime.now() - datetime.timedelta(hours=int(periodhours))
    timelimit_string = datetime.datetime.strftime(timelimit,'%Y%m%d%H%M%S') 
    query+= 'AND rc_timestamp > "'+timelimit_string+'" '

    query+= 'ORDER BY rc_timestamp DESC'

    query+= ' LIMIT '+str(resultslimit)

    # print (query)
    mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()
    df = pd.read_sql(query, mysql_con_read);

    df['Editor Edit Type'] = df.apply(conditions, axis=1)
    df=df.drop(columns=['rev_actor','rc_bot'])

    # print (df.head(100))
    # print (len(df))
    # print(str(datetime.timedelta(seconds=time.time() - functionstartTime))+' after queries.')
    return df



# Get me the articles that are also in the wikipedia_diversity_production.db and the diversity categories it belongs to.
def get_articles_diversity_categories_wikipedia_diversity_db(languagecode, df_rc):

    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()
    df_rc = df_rc.set_index('page_title')

    page_titles = df_rc.index.tolist()
    page_asstring = ','.join( ['?'] * len(page_titles) )
    df_categories = pd.read_sql_query('SELECT page_title, qitem, iso3166, iso31662, region, gender, ethnic_group, sexual_orientation, ccc_binary, num_editors, num_pageviews, date_created, num_inlinks, num_outlinks, num_inlinks_from_CCC, num_outlinks_to_CCC, num_inlinks_from_women, num_outlinks_to_women, num_references, num_discussions, num_bytes, num_wdproperty, num_interwiki, num_images, wikirank from '+languagecode+'wiki WHERE page_title IN ('+page_asstring+');', conn, params = page_titles)

    df_categories = df_categories.set_index('page_title')
    df_rc_categories = df_rc.merge(df_categories, how='left', on='page_title')

    print (df_rc_categories.head(100))
    print (len(df_rc_categories))

    return df_rc_categories



#######################################################################################

class Logger_out(object): # this prints both the output to a file and to the terminal screen.
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("testing_script"+".out", "w")
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
    def flush(self):
        pass
class Logger_err(object): # this prints both the output to a file and to the terminal screen.
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("testing_script"+".err", "w")
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
    def flush(self):
        pass


### MAIN:
if __name__ == '__main__':

    script_name = 'testing_script.py'

    sys.stdout = Logger_out()
    sys.stderr = Logger_err()

    cycle_year_month = wikilanguages_utils.get_current_cycle_year_month()
#    check_time_for_script_run(script_name, cycle_year_month)
    startTime = time.time()

   
    territories = wikilanguages_utils.load_wikipedia_languages_territories_mapping()
    languages = wikilanguages_utils.load_wiki_projects_information();

    wikilanguagecodes = sorted(languages.index.tolist())

    # print ('checking languages Replicas databases and deleting those without one...')
    # # Verify/Remove all languages without a replica database
    # for a in wikilanguagecodes:
    #     if wikilanguages_utils.establish_mysql_connection_read(a)==None:
    #         wikilanguagecodes.remove(a)


    print (wikilanguagecodes)

    languageswithoutterritory=['eo','got','ia','ie','io','jbo','lfn','nov','vo']
    # Only those with a geographical context
    for languagecode in languageswithoutterritory: wikilanguagecodes.remove(languagecode)



    wikipedialanguage_numberarticles = wikilanguages_utils.load_wikipedia_language_editions_numberofarticles(sorted(languages.index.tolist()),'production')
    closest_langs = wikilanguages_utils.obtain_closest_for_all_languages(wikipedialanguage_numberarticles, wikilanguagecodes, 4)



    main()
#    main_with_exception_email()
#    main_loop_retry()
    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))


