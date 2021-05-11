# -*- coding: utf-8 -*-

# flash dash
import flask
from flask import Flask, request, render_template
from flask import send_from_directory
from flask_caching import Cache
from dash import Dash
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_table
import dash_table_experiments as dt
from dash.dependencies import Input, Output, State
# dash bootstrap components
import dash_bootstrap_components as dbc

# viz
import plotly
import chart_studio.plotly as py
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# data
import urllib
from urllib.parse import urlparse, parse_qsl, urlencode
import pandas as pd
import sqlite3
import xlsxwriter

# other
import numpy as np
import random
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import datetime
import time
import requests
import subprocess


# script
import update_top_diversity_interwiki
sys.path.insert(0, '/srv/wcdo/src_data')
import wikilanguages_utils

setting_up_time = time.time()



def main():

    source_lang = 'af'
    exclude_images = 'none'
    exclude_art = 'none'
    number_images = 4


    df = pd.read_csv('after_query.csv')

    try:
        page_title_original = df.page_title_original.tolist()
    except:
        page_title_original = df.page_title.tolist()

    qitems_num_interwiki = df.set_index('qitem')['num_interwiki'].to_dict()

    for x in range (1,number_images+1):
        df['Image '+str(x)] = None

    # original lang
    page_titles_images = page_titles_to_current_images(page_title_original, source_lang)

    # other langs
    page_titles_langs = page_titles_to_languages(page_title_original, source_lang)

    # all ranked
    page_titles_all_images_ranked = page_titles_to_rank_images(number_images, page_titles_images, page_titles_langs)


    print (page_titles_all_images_ranked)

    input('')

    df = page_titles_to_df(df, page_titles_images, page_titles_all_images_ranked, page_titles_langs)


    df.to_csv('after_ranks2.csv')






def page_titles_to_current_images(page_titles, languagecode):
    mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()

    # query = 'SELECT il_to FROM imagelinks where il_from = %s;'
    page_titles_images = {}
    # try:
    page_asstring = ','.join( ['%s'] * len(page_titles) )
    query = 'SELECT page_title, il_to FROM imagelinks INNER JOIN page on il_from = page_id WHERE il_from_namespace = 0 AND page_title IN (%s);' % page_asstring

    try:
        mysql_cur_read.execute(query, (page_titles))
        result = mysql_cur_read.fetchall()

        list_images = set()
        old_page_title = ''
        i = 0
        for row in result:
            imagename = row[1].decode('utf-8')
            if '.ogg' in imagename: continue
            page_title = row[0].decode('utf-8')

            if page_title != old_page_title:
                page_titles_images[old_page_title]=list_images
                list_images = set()
                i = 0

            old_page_title = page_title
           
            i += 1
            # if i<=20:
            list_images.add(imagename)

        page_titles_images[old_page_title]=list_images

    except:
        print ('timeout page_titles_to_current_images.')   

    return page_titles_images



def page_titles_to_languages(page_titles, languagecode):
    mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()

    page_asstring = ','.join( ['%s'] * len(page_titles) )
    query = 'SELECT page_title, ll_title as page_title_other_lang, ll_lang as other_lang FROM langlinks INNER JOIN page on ll_from = page_id WHERE page_title IN (%s);' % page_asstring

    df = pd.read_sql_query(query, mysql_con_read, params = page_titles)
    page_titles_langs = df.stack().str.decode('utf-8').unstack()


    # input('')
    # df = pd.DataFrame(columns=['page_title','page_title_other_lang','other_lang'])

    # try:
    #     mysql_cur_read.execute(query, (page_titles))
    #     result = mysql_cur_read.fetchall()
        
    #     page_titles_langs = {}
    #     other_langs_page_titles = {}

    #     old_page_title = ''
    #     for row in result:
    #         page_title_lang_a = row[0].decode('utf-8')
    #         page_title_other_lang = row[1].decode('utf-8')
    #         other_lang = row[2].decode('utf-8')

    #         if page_title_lang_a != old_page_title and old_page_title!='':

    #             page_title_lang_a, other_lang, page_title_other_lang

    #             page_titles_langs[old_page_title] = other_langs_page_titles
    #             other_langs_page_titles = {}

    #         other_langs_page_titles[other_lang] = page_title_other_lang
    #         old_page_title = page_title_lang_a

    #     page_titles_langs[old_page_title] = other_langs_page_titles

    # except:
    #     print ('timeout.')
    


    return page_titles_langs


    # això s'ha de fer amb un dataframe. at loc.



def page_titles_to_rank_images(num_images, page_titles_images, page_titles_langs):

    page_titles_all_images_ranked = {}
    print ('here')

    langs = page_titles_langs.other_lang.unique()
    for lang in langs:
        articles_list = page_titles_langs.loc[page_titles_langs['other_lang']==lang].page_title_other_lang.tolist()
        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(lang); mysql_cur_read = mysql_con_read.cursor()

        print (lang, articles_list)
        articles_list = articles_list[:2]

        page_asstring = ','.join( ['%s'] * len(articles_list) )
        query = 'SELECT page_title, il_to FROM imagelinks INNER JOIN page on il_from = page_id WHERE il_from_namespace = 0 AND page_title IN (%s);' % page_asstring

        mysql_cur_read.execute(query, (articles_list))
        result = mysql_cur_read.fetchall()
        for row in result:
            page_title = row[0]
            image_title = row[1]


    print ('eh')
    input('')



    print (articles_list)

    df = pd.read_sql_query(query, mysql_con_read, params = articles_list)
    page_titles_images = df.stack().str.decode('utf-8').unstack()

    print (page_titles_images)
    print ('eh')
    input('')




    #     input('')

    #     mysql_cur_read.execute(query, (articles_list))
    #     result = mysql_cur_read.fetchall()
    #     for row in result:

    #     ptitle_original = page_titles_langs.loc[page_titles_langs['page_title_other_lang']==ptitle]


    #     print (articles_list)
    #     input('')

    # page_titles_langs.loc[page_titles_langs['other_lang' == lang ] & page_titles_langs['page_title_other_lang' == ptitle]]


    # input('')














    for page_title in page_titles_images.keys():
        print (page_title)

        if page_title == '': continue
        images_rank = {}
        for languagecode, page_title_x in page_titles_langs[page_title].items():

            mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()
            query = 'SELECT page_title, il_to FROM imagelinks INNER JOIN page on il_from = page_id WHERE il_from_namespace = 0 AND page_title = %s;'

            mysql_cur_read.execute(query, [page_title_x])
            result = mysql_cur_read.fetchall()

            for row in result:
                imagename = row[1].decode('utf-8')
                if '.ogg' in imagename: continue

                try:
                    images_rank[imagename]=images_rank[imagename]+1
                except:
                    images_rank[imagename]=1

            # except:
            #     print ('timeout.')

        page_titles_all_images_ranked[page_title]=sorted(images_rank, key=images_rank.get, reverse=True)

    return page_titles_all_images_ranked







def page_titles_to_df(df, page_titles_images, page_titles_all_images_ranked, page_titles_langs):

    for page_title in df.page_title:

        num_interwiki = len(page_titles_langs[page_titles])

        try:
            images_set = page_titles_images[page_title]
        except:
            images_set = set()        

        j = 1
        for image, images_rank in page_titles_all_images_ranked[page_title]:

            if '.ogg' in image: continue
            
            is_local = None
            if image in images_set:
                is_local = 1            

            image_size = 900/number_images

            URL = "https://commons.wikimedia.org/wiki/Special:FilePath/"+image+"?width=160"
            URL = "https://commons.wikimedia.org/wiki/Special:Redirect/file/"+image
            # URL = requests.get('https://commons.wikimedia.org/wiki/Special:FilePath/'+image+'?width=320')

            link_1 = html.A(html.Img(src=URL,style={'max-width': str(image_size)+ 'px', 'max-height':str(image_size)+ 'px'}), href='https://commons.wikimedia.org/wiki/File:'+image, target="_blank", style={'text-decoration':'none'})

            if is_local == 1:
                line = html.P(str(rank)+'/'+str(num_interwiki)+' Langs. ('+languagecode+')')
                color = 'green'
                # print (image)
                # print (images_set)
                # print (row)
            else:
                line = html.P(str(rank)+'/'+str(num_interwiki)+' Langs.')
                color = 'red'


            # CONDITIONS OF EXCLUSION
            if exclude_images == 'none' or exclude_images == 'all':
                df.at[page_title,'Image '+str(j)] = html.Div([
                    link_1, 
                    line,
                    ],style={'color': color})
                j+=1

            elif exclude_images == 'gaps' and image not in images_set: # case of gaps
                # line = html.P(str(rank)+'/'+str(num_interwiki)+' Langs. not including '+languagecode)
                df.at[page_title,'Image '+str(j)] = html.Div([
                    link_1, 
                    line,
                    ],style={'color': color})
                j+=1

            elif exclude_images == 'covered' and image in images_set: # case of gaps
                # line = html.P(str(rank)+'/'+str(num_interwiki)+' Langs. including '+languagecode)
                df.at[page_title,'Image '+str(j)] = html.Div([
                    link_1, 
                    line,
                    ],style={'color': color})

                j+=1

# exclude = {'Existing images':'gaps', 'Non existing images':'covered'}

            if j > number_images:
                break

    # df = df.reset_index()
    return df





### MAIN:
if __name__ == '__main__':

    startTime = time.time()
    year_month = datetime.date.today().strftime('%Y-%m')

    databases_path = '/srv/wcdo/databases/'
    ccc_db = 'ccc.db'
    stats_db = 'stats.db'
    top_ccc_db = 'top_ccc_articles.db'


    # Import the language-territories mappings
    territories = wikilanguages_utils.load_wikipedia_languages_territories_mapping()

    # Import the Wikipedia languages characteristics
    languages = wikilanguages_utils.load_wiki_projects_information();
    wikilanguagecodes = languages.index.tolist()

    main()
