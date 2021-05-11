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
import operator
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
# requests and others
import requests
import urllib
import webbrowser
import reverse_geocoder as rg
import numpy as np
from random import shuffle
# data
import pandas as pd
import gc



#databases_path = 'databases/'

#### ARTICLES DATA ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 



### --------------------------------------------------------------------------------


wikilanguages = ['ca','eu']
wikilanguages = ['is']
wikilanguages = ['gl','eu','gl']

wikilanguages = ['ca','it']
wikilanguages = ['it']

wikilanguages = ['gl','ca','eu']
wikilanguages = ['ca','es','eu','fr','it']



i = 0
for languagecode in wikilanguages:
    print (languagecode)

    conn = sqlite3.connect(databases_path + 'community_health_metrics.db'); cursor = conn.cursor() # stats_prova_amb_indexs


    current_base = 0
    upper_threshold = 0

    cursor.execute('SELECT MAX(user_id) FROM '+languagecode+'wiki_editors;')
    maxuser_id = cursor.fetchone()[0]

    print (maxuser_id)

    while upper_threshold < maxuser_id:

        upper_threshold = current_base + 200000


        # EDITORS CHARACTERISTICS AND METRICS (ACCUMULATED)
        metrics = ["user_page_edit_count_1month","user_page_edit_count_24h","user_page_talk_page_edit_count_1month","user_page_talk_page_edit_count_24h","edit_count","edit_count_24h","edit_count_30d","edit_count_60d","edit_count_7d","edit_count_bin","monthly_edit_count_bin","edit_count_editor_user_page","edit_count_editor_user_page_talk_page","edit_count_edits_ns6_file","edit_count_ns0_main","edit_count_ns1_talk","edit_count_ns2_user","edit_count_ns3_user_talk","edit_count_ns4_project","edit_count_ns5_project_talk","edit_count_ns7_file_talk","edit_count_ns8_mediawiki","edit_count_ns9_mediawiki_talk","edit_count_ns10_template","edit_count_ns11_template_talk","edit_count_ns12_help","edit_count_ns13_help_talk","edit_count_ns14_category","edit_count_ns15_category_talk","created_articles_count","deleted_articles_count","moved_articles_count","undeleted_articles_count","created_accounts_count","users_renamed_count","autoblocks_count","edits_reverted_count","reverts_made_count","inactivity_periods","active_months","max_active_months_row","max_inactive_months_row","total_months","over_monthly_edit_bin_average_past_max_inactive_months_row","over_edit_bin_average_past_max_inactive_months_row","over_past_max_inactive_months_row"]
        print (len(metrics))


#        metrics = ["edit_count_bin","monthly_edit_count_bin","inactivity_periods","active_months","total_months","max_active_months_row","max_inactive_months_row","months_since_last_edit","over_edit_bin_average_past_max_inactive_months_row","over_monthly_edit_bin_average_past_max_inactive_months_row","over_past_max_inactive_months_row"]



        query = 'SELECT user_id, metric_name, abs_value, year_month FROM '+languagecode+'wiki_editor_metrics WHERE metric_name IN ('+','.join( ['?'] * len(metrics) )+')'

        query += ' AND user_id BETWEEN '+str(current_base)+' AND '+str(upper_threshold)+';'

        df = pd.read_sql_query(query, conn, params = metrics)

        # print (df[df.duplicated('metric_name')].head(100))
        # print (df.loc[df.duplicated()])


        df1 = df.pivot(index='user_id', columns='metric_name', values = ['abs_value'])
        
        # print ('beggining')
        print (query)
        # print (len(df1.columns.tolist()))
        # print (df1.columns.tolist())

        cols = []
        for v in df1.columns.tolist(): cols.append(v[1]) 
        df1.columns = cols


        for m in metrics:
            if m not in df1:
                df1[m]=''

        df1 = df1.reindex(sorted(df1.columns), axis=1)


        # print (df1.head(10))
        # print (df1.columns.tolist())


        query = 'SELECT user_id, user_name, bot, user_flags, highest_flag, highest_flag_year_month, gender, primarybinary, primarylang, primarybinary_ecount, totallangs_ecount, numberlangs, registration_date, year_month_registration, first_edit_timestamp, year_month_first_edit, year_first_edit, lustrum_first_edit, survived60d, last_edit_timestamp, year_last_edit, lifetime_days, editing_days, percent_editing_days, days_since_last_edit, seconds_between_last_two_edits FROM '+languagecode+'wiki_editors '

        query += ' WHERE user_id BETWEEN '+str(current_base)+' AND '+str(upper_threshold)+';'


        df2 = pd.read_sql_query(query, conn)
        df2 = df2.set_index('user_id')
        df2['language'] = languagecode

        # if i == 0:
        #     df2.to_csv(databases_path + 'langwiki_editors.tsv')
        # else:
        #     df2.to_csv(databases_path + 'langwiki_editors.tsv', mode='a', header=False)


        df3 = pd.concat([df1, df2], axis=1, sort=False)
        df3 = df3.reset_index().rename(columns = {'index':'user_id'}).set_index('user_id')
        df3['language'] = languagecode

        df3 = df3.fillna(0)


        print (query)
        # print (len(df3.columns))
        # print (df3.head(10))

        df3['language-user_id'] = df3['language']+'-'+df3.index.astype(str)
       

        if i == 0:
            df3.to_csv(databases_path + 'langwiki_editors_characteristics_metrics_accumulated.tsv', sep='\t')
        else:
            df3.to_csv(databases_path + 'langwiki_editors_characteristics_metrics_accumulated.tsv', mode='a', header=False, sep='\t')

        print (len(df3))

        i += 1
        print (current_base)
        print ('end')
        current_base = upper_threshold

    print ('end lang: '+languagecode)
#    print  (df3.head(10))
print ('end1')


    ### --------------------------------------------------------------------------------


i = 0
for languagecode in wikilanguages:
    print (languagecode)

    conn = sqlite3.connect(databases_path + 'community_health_metrics.db'); cursor = conn.cursor() # 

    current_base = 0
    upper_threshold = 0

    cursor.execute('SELECT MAX(user_id) FROM '+languagecode+'wiki_editors;')
    maxuser_id = cursor.fetchone()[0]

    print (maxuser_id)

    while upper_threshold < maxuser_id:

        upper_threshold = current_base + 200000

        # EDITORS CHARACTERISTICS AND METRICS (OVER TIME)
        metrics = ["monthly_created_articles","monthly_deleted_articles","monthly_moved_articles","monthly_undeleted_articles","monthly_accounts_created","monthly_users_renamed","monthly_autoblocks","monthly_edits_reverted","monthly_reverts_made","monthly_editing_days","monthly_edits","monthly_edits_ns0_main","monthly_edits_ns10_template","monthly_edits_ns11_template_talk","monthly_edits_ns12_help","monthly_edits_ns13_help_talk","monthly_edits_ns14_category","monthly_edits_ns15_category_talk","monthly_edits_ns1_talk","monthly_edits_ns2_user","monthly_edits_ns3_user_talk","monthly_edits_ns4_project","monthly_edits_ns5_project_talk","monthly_edits_ns6_file","monthly_edits_ns7_file_talk","monthly_edits_ns8_mediawiki","monthly_edits_ns9_mediawiki_talk","monthly_user_page_edit_count","monthly_user_page_talk_page_edit_count","monthly_average_seconds_between_edits","monthly_edits_to_baseline","monthly_editing_days_to_baseline","monthly_edits_increasing_decreasing","month_since_last_edit","active_months_row","inactive_months_row"]


#        metrics = ["monthly_created_articles","monthly_deleted_articles","monthly_moved_articles","monthly_undeleted_articles","monthly_accounts_created","monthly_users_renamed","monthly_autoblocks","monthly_edits_reverted","monthly_reverts_made","monthly_editing_days","monthly_edits","monthly_edits_to_baseline","monthly_editing_days_to_baseline","monthly_edits_increasing_decreasing","month_since_last_edit","active_months_row","inactive_months_row"]


        query = 'SELECT user_name, user_id, year_month, metric_name, abs_value FROM '+languagecode+'wiki_editor_metrics WHERE metric_name IN ('+','.join( ['?'] * len(metrics) )+')'

        query += ' AND user_id BETWEEN '+str(current_base)+' AND '+str(upper_threshold)+';'

        print (current_base, upper_threshold)

        df = pd.read_sql_query(query, conn, params = metrics)
        df1 = pd.pivot_table(df, index=['year_month','user_id'], columns='metric_name', values = 'abs_value')

        df1 = df1.reset_index()
        df1 = df1.set_index('user_id')


        for m in metrics:
            if m not in df1:
                df1[m]=''


        df1 = df1.reindex(sorted(df1.columns), axis=1)
        df1 = df1.fillna(0)

        df1['language'] = languagecode
        df1['language-user_id'] = df1['language']+'-'+df1.index.astype(str)


        if i == 0:
            df1.to_csv(databases_path + 'langwiki_editors_metrics_over_time.tsv', sep='\t')
        else:
            df1.to_csv(databases_path + 'langwiki_editors_metrics_over_time.tsv', mode='a', header=False, sep='\t')


        i += 1
        current_base = upper_threshold


    print ('end lang: '+languagecode)
    # input('')

print ('end2')

