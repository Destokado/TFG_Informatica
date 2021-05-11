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
import urllib
import webbrowser
import reverse_geocoder as rg
import numpy as np
from random import shuffle
# data
import pandas as pd
# classifier
from sklearn import svm, linear_model
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import gc



# MAIN
def main():

    wikilanguagecodes = ['fr','es','zh','de','ja','pl','pt','ru','uk','ro','sr']


#    wikilanguagecodes = ['ca']

    for languagecode in wikilanguagecodes:
        (page_titles_qitems, page_titles_page_ids)=wikilanguages_utils.load_dicts_page_ids_qitems(0,languagecode)
        print (languagecode)
        lgbt_links(languagecode,page_titles_page_ids,page_titles_qitems)
        print ('*')


################################################################


def lgbt_links(languagecode,page_titles_page_ids,page_titles_qitems):

    functionstartTime = time.time()
    conn = sqlite3.connect(databases_path + 'wikipedia_diversity_production.db'); cursor = conn.cursor()


    (enwiki_page_titles_qitems, enwiki_page_titles_page_ids)=wikilanguages_utils.load_dicts_page_ids_qitems(0,'en')
    enwiki_qitems_page_titles = {v: k for k, v in enwiki_page_titles_qitems.items()}



    try: cursor.execute('SELECT 1 FROM '+languagecode+'wiki;')
    except: return

    lgbt_page_title = {}
    lgbt_page_id = {}


    query = 'SELECT page_id, page_title FROM '+languagecode+'wiki WHERE sexual_orientation IS NOT NULL and sexual_orientation != "Q1035954" and ccc_binary = "1";'
    for row in cursor.execute(query):
        lgbt_page_id[row[0]]=row[1]
        lgbt_page_title[row[1]]=row[0]


"""

    # NEED TO REVISE THESE QUERIES
    query = 'SELECT page_id, page_title FROM '+languagecode+'wiki WHERE sexual_orientation_property IS NOT NULL and sexual_orientation_property != "Q1035954" and ccc_binary = "1";'
    for row in cursor.execute(query):
        lgbt_page_id[row[0]]=row[1]
        lgbt_page_title[row[1]]=row[0]

    query = 'SELECT page_id, page_title FROM '+languagecode+'wiki WHERE sexual_orientation_partner IS NOT NULL and sexual_orientation_partner != "Q1035954" and ccc_binary = "1";'
    for row in cursor.execute(query):
        lgbt_page_id[row[0]]=row[1]
        lgbt_page_title[row[1]]=row[0]
"""

    # print (len(lgbt_page_id))
    # print (lgbt_page_id)



    page_id_feature = {}
    query = 'SELECT page_id, num_interwiki FROM '+languagecode+'wiki;'
    for row in cursor.execute(query):
        page_id_feature[int(row[0])]=row[1]



#    dumps_path = 'gnwiki-20190720-pagelinks.sql.gz' # read_dump = '/public/dumps/public/wikidatawiki/latest-all.json.gz'

    dumps_path = '/public/dumps/public/'+languagecode+'wiki/latest/'+languagecode+'wiki-latest-pagelinks.sql.gz'
    wikilanguages_utils.check_dump(dumps_path, script_name)
    try:
        dump_in = gzip.open(dumps_path, 'r')
    except:
        print ('error. the file pagelinks is not working.')

    w = 0
    iteratingstartTime = time.time()
    print ('Iterating the dump.')


#    edfile2 = open(databases_path+languagecode+'_lgbt_pagelinks.tsv', "w")
    edfile2 = open(databases_path+'ccc_lgbt_pagelinks_'+languagecode+'wiki.tsv', "w")

    while True:
        line = dump_in.readline()
        try: line = line.decode("utf-8")
        except UnicodeDecodeError: line = str(line)

        if line == '':
            i+=1
            if i==3: break
        else: i=0

        if wikilanguages_utils.is_insert(line):
            # table_name = wikilanguages_utils.get_table_name(line)
            # columns = wikilanguages_utils.get_columns(line)
            values = wikilanguages_utils.get_values(line)
            if wikilanguages_utils.values_sanity_check(values): rows = wikilanguages_utils.parse_values(values)

            for row in rows:
                w+=1
#                print(row)
                pl_from = int(row[0])
                pl_from_namespace = row[1]
                pl_title = str(row[2])
                pl_namespace = row[3]

                try:
                    pl_title_page_id = int(page_titles_page_ids[pl_title])
                except:
                    pl_title_page_id = None
 
                if pl_from_namespace == '0' or pl_namespace == '0':

 


                    try:
                        feature=page_id_feature[pl_from]
                        lgbt_biography_1 = lgbt_page_id[pl_from]
                        lgbt_biography_2 = lgbt_page_id[pl_title_page_id]
                        if lgbt_biography_1 == lgbt_biography_2: continue

                        edfile2.write(str(lgbt_biography_1.replace('_',' '))+'\t'+str(lgbt_biography_2.replace('_',' '))+'\t'+str(feature)+'\t'+languagecode+'\n')

                        # lgbt_biography_1 = enwiki_qitems_page_titles[page_titles_qitems[lgbt_biography_1]]
                        # lgbt_biography_2 = enwiki_qitems_page_titles[page_titles_qitems[lgbt_biography_2]]

    #                    print (str(lgbt_biography_1.replace('_',' '))+'\t'+str(lgbt_biography_2.replace('_',' '))+'\t'+str(feature)+'\t'+languagecode+'\n')

                        # print (str(lgbt_biography_1)+'\t'+lgbt_biography_2+'\t'+str(feature)+'\n')


                    except:
                        pass




                if w % 1000000 == 0: # 10 million
                    print (w)
                    print ('current time: ' + str(time.time() - iteratingstartTime)+ ' '+languagecode)
                    print ('number of lines per second: '+str(round(((w/(time.time() - iteratingstartTime))/1000),2))+ ' thousand.')

                    # print (num_of_inlinks_from_ethnic_groups);
                    # print (num_of_outlinks_to_ethnic_group);


#    input('')
    print ('Done with the dump.')

    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    print (duration)



#######################################################################################


def main_with_exception_email():
    try:
        main()
    except:
    	wikilanguages_utils.send_email_toolaccount('WDO - PAGELINKS ERROR: '+ wikilanguages_utils.get_current_cycle_year_month(), 'ERROR.')


def main_loop_retry():
    page = ''
    while page == '':
        try:
            main()
            page = 'done.'
        except:
            print('There was an error in the main. \n')
            path = '/srv/wcdo/src_data/content_selection.err'
            file = open(path,'r')
            lines = file.read()
            wikilanguages_utils.send_email_toolaccount('WDO - PAGELINKS ERROR: '+ wikilanguages_utils.get_current_cycle_year_month(), 'ERROR.' + lines); print("Now let's try it again...")
            time.sleep(900)
            continue


######################################################################################

class Logger_out(object): # this prints both the output to a file and to the terminal screen.
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("content_selection"+".out", "w")
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
    def flush(self):
        pass
class Logger_err(object): # this prints both the output to a file and to the terminal screen.
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("content_selection"+".err", "w")
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
    def flush(self):
        pass


### MAIN:
if __name__ == '__main__':
    sys.stdout = Logger_out()
    sys.stderr = Logger_err()

    script_name = 'LGBT_pagelinks.py'
    cycle_year_month = wikilanguages_utils.get_current_cycle_year_month()
#    check_time_for_script_run(script_name, cycle_year_month)
    startTime = time.time()

    territories = wikilanguages_utils.load_wikipedia_languages_territories_mapping()
    languages = wikilanguages_utils.load_wiki_projects_information();


    wikilanguagecodes = sorted(languages.index.tolist())
    print ('checking languages Replicas databases and deleting those without one...')
    # Verify/Remove all languages without a replica database
    for a in wikilanguagecodes:
        if wikilanguages_utils.establish_mysql_connection_read(a)==None:
            wikilanguagecodes.remove(a)

    # Only those with a geographical context
    languageswithoutterritory=list(set(languages.index.tolist()) - set(list(territories.index.tolist())))
    for languagecode in languageswithoutterritory:
        try: wikilanguagecodes.remove(languagecode)
        except: pass


    print (wikilanguagecodes)
    print (len(wikilanguagecodes))



#    if wikilanguages_utils.verify_script_run(cycle_year_month, script_name, 'check', '') == 1: exit()

    main()
#    main_with_exception_email()
#    main_loop_retry()

    duration = str(datetime.timedelta(seconds=time.time() - startTime))


