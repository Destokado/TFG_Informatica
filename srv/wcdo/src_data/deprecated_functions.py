def wd_check_and_introduce_wikipedia_missing_qitems(languagecode):

    function_name = 'wd_check_and_introduce_wikipedia_missing_qitems'
    if wikilanguages_utils.verify_function_run(cycle_year_month, script_name, function_name, 'check','')==1: return
    functionstartTime = time.time()

    langcodes = []

    if languagecode != '' and languagecode!= None: langcodes.append(languagecode)
    else: langcodes = wikilanguagecodes


    for languagecode in langcodes:
        print ('\n* '+languagecode)

        page_titles=list()
        page_ids=list()
        conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()
        query = 'SELECT page_title, page_id FROM '+languagecode+'wiki;'
        for row in cursor.execute(query):
            page_title=str(row[0])
            page_id = int(row[1])
            page_titles.append(str(row[0]))
            page_ids.append(row[1])

        print ('this is the number of page_ids: '+str(len(page_ids)))

        parameters = []
#            mysql_con_read = mdb.connect(host=languagecode+'wiki.analytics.db.svc.eqiad.wmflabs',db=languagecode+'wiki_p', read_default_file='./my.cnf', cursorclass=mdb_cursors.SSCursor,charset='utf8mb4', connect_timeout=60); mysql_cur_read = mysql_con_read.cursor()
        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()

        try:
            query = 'SELECT page_title, page_id FROM page WHERE page_namespace=0 AND page_is_redirect=0;'
        #            query = 'SELECT /*+ MAX_EXECUTION_TIME(1000) */ page_title, page_id FROM page WHERE page_namespace=0 AND page_is_redirect=0;'
            mysql_cur_read.execute(query)
            rows = mysql_cur_read.fetchall()
            print ('query done')
            Articles_namespace_zero = len(rows)
            all_articles = {}
            for row in rows: 
                page_title = row[0].decode('utf-8')
                page_id = int(row[1])
                all_articles[page_id]=page_title

            for page_id in page_ids:
                del all_articles[page_id]

            for page_id, page_title in all_articles.items():               
        #                print (page_title, page_id)
                parameters.append((page_title,page_id,''))

            print ('* '+languagecode+' language edition has '+str(articles_namespace_zero)+' Articles non redirect with namespace 0.')
            print ('* '+languagecode+' language edition has '+str(len(parameters))+' Articles that have no qitem in Wikidata and therefore are not in the CCC database.\n')

            conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()
            query = 'INSERT OR IGNORE INTO '+languagecode+'wiki (page_title,page_id,qitem) VALUES (?,?,?);';
            cursor.executemany(query,parameters)
            conn.commit()
            print ('page ids for this language are in: '+languagecode+'\n')
        except:
            print ('this language replica reached timeout: '+languagecode+'\n')
        #            input('')
    wikilanguages_utils.verify_function_run(cycle_year_month, script_name, function_name, 'mark', duration)
    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))



def label_other_ccc_country_properties(languagecode,page_titles_page_ids,page_titles_qitems):

    function_name = 'label_other_ccc_country_properties '+languagecode
    if create_function_account_db(function_name, 'check','')==1: return
    functionstartTime = time.time()


    conn = sqlite3.connect(databases_path + wikidata_db); cursor = conn.cursor()
    conn2 = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor2 = conn2.cursor()

    (iso_qitem, label_qitem) = wikilanguages_utils.load_all_countries_qitems()

    try: countries_language = set(territories.loc[languagecode]['ISO3166'].tolist())
    except: 
        try: countries_language = set(); countries_language.add(territories.loc[languagecode]['ISO3166'])
        except: pass
    countries_language = list(set(countries_language)&set(iso_qitem.keys())) # these iso3166 codes
    qitems_countries_language = []
    for country in countries_language: qitems_countries_language.append(iso_qitem[country])
    qitems_countries_language = qitems_countries_language + list(set(wikilanguages_utils.get_old_current_countries_pairs(languagecode,'').keys()))


    page_asstring = ','.join( ['?'] * (len(iso_qitem)) ) # total
    query = 'SELECT country_properties.qitem, page_title, count(country_properties.qitem) FROM country_properties INNER JOIN sitelinks ON sitelinks.qitem = country_properties.qitem WHERE sitelinks.langcode ="'+languagecode+'wiki" AND country_properties.qitem2 IN (%s)' % page_asstring

    page_asstring = ','.join( ['?'] * (len(qitems_countries_language)) ) # local
    query += ' AND country_properties.qitem2 NOT IN (%s) GROUP BY country_properties.qitem' % page_asstring

    parameters = list(iso_qitem.values())+qitems_countries_language

#    print (query)
#    print (parameters)
    table_update = []
    for row in cursor.execute(query, parameters):
#        print (row)
        qitem=row[0]
        page_title=row[1].replace(' ','_')
        try: page_id = page_titles_page_ids[page_title]
        except: continue
        count=row[2]
        table_update.append((0,count,page_title,qitem,page_id))

    query = 'UPDATE '+languagecode+'wiki SET ccc_binary = ?, other_ccc_country_wd = ? WHERE page_title = ? AND qitem = ? AND page_id = ?;'
    cursor2.executemany(query,table_update)
    conn2.commit()
    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    create_function_account_db(function_name, 'mark', duration)



def label_other_ccc_location_properties(languagecode,page_titles_page_ids,page_titles_qitems):

    function_name = 'label_other_ccc_location_properties '+languagecode
    if create_function_account_db(function_name, 'check','')==1: return

    functionstartTime = time.time()

    conn = sqlite3.connect(databases_path + wikidata_db); cursor = conn.cursor()
    conn2 = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor2 = conn2.cursor()

    qitem_page_titles = {v: k for k, v in page_titles_qitems.items()}

    (iso_qitem, label_qitem) = wikilanguages_utils.load_all_countries_qitems()

    try: 
        countries_language = territories.loc[languagecode]['ISO3166'].tolist()
    except: 
        try: countries_language = set(); countries_language.add(territories.loc[languagecode]['ISO3166'])
        except: pass

    qitems_countries_language = []
    for country in countries_language:
        if country in iso_qitem:
            qitems_countries_language.append(iso_qitem[country])

    qitems_countries_language = list(set(qitems_countries_language))

    query = 'SELECT qitem FROM '+languagecode+'wiki WHERE location_wd IS NOT NULL;'
    ccc_location_qitems=[]
    for row in cursor2.execute(query): ccc_location_qitems.append(row[0])

    table_update = []
    length=len(ccc_location_qitems)
#    length=500000
    if length<200000:
#        print ('short')

        page_asstring = ','.join( ['?'] * (len(ccc_location_qitems)) ) # local
        page_asstring2 = ','.join( ['?'] * (len(qitems_countries_language)) ) # local

        query = 'SELECT location_properties.qitem, page_title, count(location_properties.qitem) FROM location_properties INNER JOIN sitelinks ON sitelinks.qitem = location_properties.qitem WHERE sitelinks.langcode ="'+languagecode+'wiki" AND location_properties.qitem NOT IN (%s)' % page_asstring
        query = query + ' AND location_properties.qitem2 NOT IN (%s)' % page_asstring2
        query = query + ' GROUP BY location_properties.qitem;'

        for row in cursor.execute(query, ccc_location_qitems+qitems_countries_language):
            qitem=row[0]
            page_title=row[1].replace(' ','_')
            try: page_id = page_titles_page_ids[page_title]
            except: continue
            count=row[2]
            table_update.append((0,count,page_title,qitem,page_id))

    else:
#        print ('long')
        page_asstring2 = ','.join( ['?'] * (len(qitems_countries_language)) ) # local
        query = 'SELECT DISTINCT location_properties.qitem, count(location_properties.qitem) FROM location_properties INNER JOIN sitelinks ON sitelinks.qitem = location_properties.qitem WHERE sitelinks.langcode = "'+languagecode+'wiki" AND location_properties.qitem2 NOT IN (%s) GROUP BY location_properties.qitem;' % page_asstring2

        location_qitems_count = {}
        location_qitems = []
        for row in cursor.execute(query,qitems_countries_language): 
            location_qitems.append(row[0])
            location_qitems_count[row[0]]=row[1]

#        print (len(location_qitems))
        location_qitems = list(set(location_qitems) ^ set(location_qitems) & set(ccc_location_qitems))
#        print (len(location_qitems))

        # ^ is subtract
        # & is intersection
        # it is read from right to left

        num_art=0
        for qitem in location_qitems:
            num_art+=1
            try:
                page_title = qitem_page_titles[qitem]
                page_id = page_titles_page_ids[page_title]
                table_update.append((0,location_qitems_count[qitem],page_title,qitem,page_id))
#                print ((0,1,page_title,qitem,page_id))
            except:
                pass
#            if num_art % 1000 == 0: print (num_art)

#    print (len(table_update))
#    input('')
    query = 'UPDATE '+languagecode+'wiki SET ccc_binary = ?, other_ccc_location_wd = ? WHERE page_title = ? AND qitem = ? AND page_id = ?;'
    cursor2.executemany(query,table_update)
    conn2.commit()

    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    create_function_account_db(function_name, 'mark', duration)





def label_other_ccc_category_crawling(languagecode,page_titles_page_ids,page_titles_qitems):

    function_name = 'label_other_ccc_category_crawling '+languagecode
    if create_function_account_db(function_name, 'check','')==1: retur

    functionstartTime = time.time()

    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()
    qitem_page_titles = {v: k for k, v in page_titles_qitems.items()}

    qitems = page_titles_qitems.values()

    qitems_keywords_binary = {}
    qitems_category_crawling_level = {}

    for queried_languagecode in wikilanguagecodes:
        if queried_languagecode == languagecode: continue
        query = 'SELECT MAX(category_crawling_level) FROM '+queried_languagecode+'wiki;'
        level_max = 0
        cursor.execute(query)
        value = cursor.fetchone()
        if value != None: level_max = value[0]
        if level_max == 0 or level_max == None: continue
#        print (queried_languagecode)

        query = 'SELECT '+queried_languagecode+'wiki.qitem, '+queried_languagecode+'wiki.category_crawling_level, '+queried_languagecode+'wiki.keyword_title, '+languagecode+'wiki.page_title FROM '+queried_languagecode+'wiki INNER JOIN '+languagecode+'wiki ON '+queried_languagecode+'wiki.qitem = '+languagecode+'wiki.qitem WHERE '
        query += ''+languagecode+'wiki.ccc_binary IS NULL AND ('+languagecode+'wiki.category_crawling_level IS NOT NULL OR '+languagecode+'wiki.language_weak_wd IS NOT NULL OR '+languagecode+'wiki.affiliation_wd IS NOT NULL OR '+languagecode+'wiki.has_part_wd IS NOT NULL);'

        count = 0
        for row in cursor.execute(query):
            qitem=row[0]
#            if queried_languagecode == 'ar': print (row[3],row[1])

            if row[2] != None: qitems_keywords_binary[qitem]=1
            if row[1] != None: 
                category_crawling_level=row[1]
                if category_crawling_level != 0: category_crawling_level=category_crawling_level-1
                if category_crawling_level > 6: category_crawling_level = 6

                relative_level=1-float(category_crawling_level/6)
                # we choose always the lowest category crawling level in case the Article is in category crawling of different languages.
                if qitem in qitems_category_crawling_level:
                    if qitems_category_crawling_level[qitem]>relative_level: qitems_category_crawling_level[qitem]=relative_level
                else: 
                    qitems_category_crawling_level[qitem]=relative_level
                    count+=1
#        print (count)

    table_update = []
    for qitem in qitems:
        keyword = 0; relative_level = 0;

        page_id=page_titles_page_ids[qitem_page_titles[qitem]]

        if qitem in qitems_keywords_binary: keyword = 1
        else: keyword = 0

        if qitem in qitems_category_crawling_level:
            relative_level = qitems_category_crawling_level[qitem]
        else: relative_level = 0

        if keyword != 0 or relative_level != 0:
            table_update.append((relative_level,keyword,qitem,page_id))

#    print ('\nThe number of Articles that are going to be updated for this language edition CCC: '+languagecode+' that relate to other language edition keywords/category crawling are: '+str(len(table_update)))
    cursor.executemany('UPDATE '+languagecode+'wiki SET other_ccc_category_crawling_relative_level = ?, other_ccc_keyword_title = ? WHERE qitem = ? AND page_id = ?', table_update)
    conn.commit()

    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    create_function_account_db(function_name, 'mark', duration)



# Get the Articles table with the number of inlinks.
def label_potential_ccc_articles_with_inlinks(languagecode,page_titles_page_ids,page_titles_qitems,group):


    def full_query(languagecode,page_titles_page_ids,page_titles_qitems,group):

        # get the ccc and potential ccc Articles
        print ('Attempt with a MySQL. Full query.')
        page_titles_inlinks_group = []
        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()

        page_asstring = ','.join( ['%s'] * len( Article_selection ) )
        query = 'SELECT count(pl_from), pl_title FROM pagelinks WHERE pl_from_namespace=0 AND pl_namespace=0 AND pl_from IN (%s) GROUP BY pl_title' % page_asstring
        mysql_cur_read.execute(query,list(Article_selection.keys()))
        rows = mysql_cur_read.fetchall()
        #        print ('query run.')
        for row in rows:
            pl_title = str(row[1].decode('utf-8'))
            try: 
        #                print ((row[0],all_ccc_articles[pl_title],all_ccc_articles_qitems[pl_title]))
                page_titles_inlinks_group.append((row[0],page_titles_page_ids[pl_title],page_titles_qitems[pl_title], pl_title))
            except: pass

        if group == 'ccc':
            query = 'UPDATE '+languagecode+'wiki SET num_inlinks_from_CCC=? WHERE page_id = ? AND qitem = ? AND page_title=?;'
        else:
            query = 'UPDATE '+languagecode+'wiki SET num_inlinks_from_geolocated_abroad=? WHERE page_id = ? AND qitem = ? AND page_title=?;'

        cursor.executemany(query,page_titles_inlinks_group)
        conn.commit()
        #        print ('- Articles with links coming from the group: '+str(len(page_titles_inlinks_group)))

        # INLINKS
        query = 'SELECT count(*) FROM '+languagecode+'wiki WHERE num_inlinks IS NOT NULL;'
        cursor.execute(query)
        if cursor.fetchone()[0] == 0:
            page_titles_inlinks = []
            mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()
            query = 'SELECT count(pl_from), pl_title FROM pagelinks WHERE pl_from_namespace=0 AND pl_namespace=0 GROUP BY pl_title'
            mysql_cur_read.execute(query)
        #        page_asstring = ','.join( ['%s'] * len( all_ccc_articles ) )
        #        query = 'SELECT count(pl_from), pl_title FROM pagelinks WHERE pl_from_namespace=0 AND pl_namespace=0 AND pl_title IN (%s) GROUP BY pl_title' # % page_asstring
        #        mysql_cur_read.execute(query,set(all_ccc_articles.keys()))
            rows = mysql_cur_read.fetchall()
        #        print ('query run.')

            for row in rows:
                try:
                    pl_title=str(row[1].decode('utf-8'))
                    count=row[0]
                    page_titles_inlinks.append((count,float(count),page_titles_page_ids[pl_title],page_titles_qitems[pl_title],pl_title))
        #                print ((row[0],float(row[0]),all_ccc_articles[pl_title],all_ccc_articles_qitems[pl_title]))
                except:
                    continue

            if group == 'ccc':
                query = 'UPDATE '+languagecode+'wiki SET num_inlinks=?,percent_inlinks_from_CCC=(num_inlinks_from_CCC/?) WHERE page_id = ? AND qitem = ? AND page_title=?;'
            else:
                query = 'UPDATE '+languagecode+'wiki SET num_inlinks=?,percent_inlinks_from_geolocated_abroad=(num_inlinks_from_geolocated_abroad/?) WHERE page_id = ? AND qitem = ? AND page_title=?;'

            cursor.executemany(query,page_titles_inlinks)
            conn.commit()
        #            print ('- Articles with any inlink at all: '+str(len(page_titles_inlinks)))

        else:
            if group == 'ccc':
                query = 'UPDATE '+languagecode+'wiki SET percent_inlinks_from_CCC=(1.0*num_inlinks_from_CCC/num_inlinks);'
            else:
                query = 'UPDATE '+languagecode+'wiki SET percent_inlinks_from_geolocated_abroad=(1.0*num_inlinks_from_geolocated_abroad/num_inlinks);'
            cursor.execute(query)
            conn.commit()



    def full_query_batches(languagecode,page_titles_page_ids,page_titles_qitems,group):

        # get the ccc and potential ccc Articles
        print ('Attempt with a MySQL. Full query batches.')
        page_titles_inlinks_group = []
        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()

        art = sorted(list(page_titles_qitems.keys())); y = set()
        for x in art:
            y.add(x[:2])
        beginnings = sorted(y)
        print(len(y))

        for val in beginnings:
            val = val+'%'
#            if "'" in val:
#                val = '"'+val+'"'
#            else:
#                val = "'"+val+"'"

            page_asstring = ','.join( ['%s'] * len( Article_selection ) )
            query = "SELECT count(pl_from), pl_title FROM pagelinks WHERE pl_from_namespace=0 AND pl_namespace=0 AND pl_from IN (%s)" % page_asstring
            query = query + " AND pl_title LIKE %s GROUP BY pl_title;"

            parameters = list(Article_selection.keys())
            parameters.append(val)

#            print (val)

#            print(query)

            mysql_cur_read.execute(query,parameters)
            rows = mysql_cur_read.fetchall()
#            print (len(rows))
            #        print ('query run.')
            for row in rows:
                try: 
                    pl_title = str(row[1].decode('utf-8'))
                    page_titles_inlinks_group.append((row[0],page_titles_page_ids[pl_title],page_titles_qitems[pl_title], pl_title))
#                    print ((row[0],page_titles_page_ids[pl_title],page_titles_qitems[pl_title], pl_title))
                except: pass

        if group == 'ccc':
            query = 'UPDATE '+languagecode+'wiki SET num_inlinks_from_CCC=? WHERE page_id = ? AND qitem = ? AND page_title=?;'
        else:
            query = 'UPDATE '+languagecode+'wiki SET num_inlinks_from_geolocated_abroad=? WHERE page_id = ? AND qitem = ? AND page_title=?;'

        cursor.executemany(query,page_titles_inlinks_group)
        conn.commit()
        print ('- Articles with links coming from the group: '+str(len(page_titles_inlinks_group)))

        # INLINKS
        query = 'SELECT count(*) FROM '+languagecode+'wiki WHERE num_inlinks IS NOT NULL;'
        cursor.execute(query)
        if cursor.fetchone()[0] == 0:
            page_titles_inlinks = []
            mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()


            for val in beginnings:
                val = val+'%'
                if "'" in val:
                    val = '"'+val+'"'
                else:
                    val = "'"+val+"'"
#                print (val)
 
                query = "SELECT count(pl_from), pl_title FROM pagelinks WHERE pl_from_namespace=0 AND pl_namespace=0 AND pl_title LIKE "+val+" GROUP BY pl_title"
                mysql_cur_read.execute(query)
                rows = mysql_cur_read.fetchall()
#                print(len(rows))

                for row in rows:
                    try:
                        pl_title=str(row[1].decode('utf-8'))
                        count=row[0]
                        page_titles_inlinks.append((count,float(count),page_titles_page_ids[pl_title],page_titles_qitems[pl_title],pl_title))
#                        print((count,float(count),page_titles_page_ids[pl_title],page_titles_qitems[pl_title],pl_title))
#                        pass

                    except:
                        pass

            if group == 'ccc':
                query = 'UPDATE '+languagecode+'wiki SET num_inlinks=?,percent_inlinks_from_CCC=(num_inlinks_from_CCC/?) WHERE page_id = ? AND qitem = ? AND page_title=?;'
            else:
                query = 'UPDATE '+languagecode+'wiki SET num_inlinks=?,percent_inlinks_from_geolocated_abroad=(num_inlinks_from_geolocated_abroad/?) WHERE page_id = ? AND qitem = ? AND page_title=?;'

            cursor.executemany(query,page_titles_inlinks)
            conn.commit()
            print ('- Articles with any inlink at all: '+str(len(page_titles_inlinks)))

        else:
            if group == 'ccc':
                query = 'UPDATE '+languagecode+'wiki SET percent_inlinks_from_CCC=(1.0*num_inlinks_from_CCC/num_inlinks);'
            else:
                query = 'UPDATE '+languagecode+'wiki SET percent_inlinks_from_geolocated_abroad=(1.0*num_inlinks_from_geolocated_abroad/num_inlinks);'
            cursor.execute(query)
            conn.commit()


    def code_logics(languagecode,page_titles_page_ids,page_titles_qitems,group):

        print ('Attempt with code logics. One by one.')

        Article_selection_page_ids = set(Article_selection.keys())

        page_titles_inlinks_group = []
        page_ids=[]
        num_art = 0
        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()

        #        print ('Progression.')
        for x,y in page_titles_page_ids.items():
            query = 'SELECT pl_from FROM pagelinks WHERE pl_namespace=0 AND pl_from_namespace=0 AND pl_title = %s;'
            mysql_cur_read.execute(query,(x,))
            rows = mysql_cur_read.fetchall()
            pl_title = x
            for row in rows:
                page_ids.append(row[0])
            try:
                num_art = num_art + 1
                if num_art % 10000 == 0:
                    print (100*num_art/len(page_titles_page_ids))
                    print ('current time: ' + str(time.time() - functionstartTime))

                count=len(list(set(page_ids).intersection(Article_selection_page_ids)))
                page_titles_inlinks_group.append((count,len(page_ids),float(count)/float(len(page_ids)),page_titles_page_ids[pl_title],page_titles_qitems[pl_title],pl_title))
                page_ids.clear()
            except: 
                page_ids.clear()
                pass

        #        print ('- Articles with inlinks: '+str(len(page_titles_inlinks_group)))

        if group == 'ccc':
            query = 'UPDATE '+languagecode+'wiki SET (num_inlinks_from_CCC,num_inlinks,percent_inlinks_from_CCC)=(?,?,?) WHERE page_id = ? AND qitem = ? AND page_title=?;'
        else:
            query = 'UPDATE '+languagecode+'wiki SET (num_inlinks_from_geolocated_abroad,num_inlinks,percent_inlinks_from_geolocated_abroad)=(?,?,?) WHERE page_id = ? AND qitem = ? AND page_title=?;'            

        cursor.executemany(query,page_titles_inlinks_group)
        conn.commit()


    def code_logics_batches(languagecode,page_titles_page_ids,page_titles_qitems,group):

        print ('Attempt with code logics. Batches.')
        #input('')
        cur_time = time.time()
       # get the ccc and potential ccc Articles

        Article_selection_page_ids = set(Article_selection.keys())
        page_titles_inlinks_group = []

        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()

        num_art = 0
        page_ids = set()

        art = sorted(list(page_titles_qitems.keys())); y = set()
        for x in art:
            y.add(x[:2])

        beginnings = sorted(y)
        print(len(y))
        for val in beginnings:
            val = val+'%'
            if "'" in val:
                val = '"'+val+'"'
            else:
                val = "'"+val+"'"

            query = "SELECT pl_from, pl_title FROM pagelinks WHERE pl_namespace=0 AND pl_from_namespace=0 AND pl_title LIKE "+val

            print (query)
            old_pl_title = ''
            mysql_cur_read.execute(query)
            rows = mysql_cur_read.fetchall()
            for row in rows:
                pl_title = row[1].decode('utf-8')

                if old_pl_title != pl_title and old_pl_title!='':
                    try:
                        num_art = num_art + 1
                        if num_art % 10000 == 0:
                            print (100*num_art/len(page_titles_page_ids))
                            print ('total time: ' + str(time.time() - functionstartTime))
                            print ('current time: ' + str(time.time() - cur_time))


                        count=len(page_ids.intersection(Article_selection_page_ids))
                        page_titles_inlinks_group.append((count,len(page_ids),float(count)/float(len(page_ids)),page_titles_page_ids[old_pl_title],page_titles_qitems[old_pl_title],old_pl_title))
#                        print((count,len(page_ids),float(count)/float(len(page_ids)),page_titles_page_ids[old_pl_title],page_titles_qitems[old_pl_title],old_pl_title))
                        page_ids.clear()
                    except:
                        page_ids.clear()
                        pass

                page_ids.add(row[0])
                old_pl_title = pl_title
        #        print ('- Articles with inlinks: '+str(len(page_titles_inlinks_group)))

            try:
                count=len(page_ids.intersection(Article_selection_page_ids))
                page_titles_inlinks_group.append((count,len(page_ids),float(count)/float(len(page_ids)),page_titles_page_ids[old_pl_title],page_titles_qitems[old_pl_title],old_pl_title))
                page_ids.clear()
            except:
                pass


        if group == 'ccc':
            query = 'UPDATE '+languagecode+'wiki SET (num_inlinks_from_CCC,num_inlinks,percent_inlinks_from_CCC)=(?,?,?) WHERE page_id = ? AND qitem = ? AND page_title=?;'
        else:
            query = 'UPDATE '+languagecode+'wiki SET (num_inlinks_from_geolocated_abroad,num_inlinks,percent_inlinks_from_geolocated_abroad)=(?,?,?) WHERE page_id = ? AND qitem = ? AND page_title=?;'            

        cursor.executemany(query,page_titles_inlinks_group)
        conn.commit()



##### GENERAL FUNCTION

    function_name = 'label_potential_ccc_articles_with_inlinks '+group+' '+languagecode
    if create_function_account_db(function_name, 'check','')==1: return

    functionstartTime = time.time()
    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()
    Article_selection = {}

    if group == 'ccc':
        query = 'SELECT page_id, page_title FROM '+languagecode+'wiki WHERE ccc_binary=1;'
        for row in cursor.execute(query):
            Article_selection[row[0]]=row[1]
#        print ('- Articles in CCC: '+str(len(article_selection)))
    else:
        query = 'SELECT page_id, page_title FROM '+languagecode+'wiki WHERE ccc_binary=0;'
        for row in cursor.execute(query):
            Article_selection[row[0]]=row[1]
#        print ('- Articles with other language CCC relationships: '+str(len(article_selection)))

    
#    full_query(languagecode,page_titles_page_ids,page_titles_qitems,group)
#    full_query_batches(languagecode,page_titles_page_ids,page_titles_qitems,group)
#    code_logics_batches(languagecode,page_titles_page_ids,page_titles_qitems,group)
#    code_logics(languagecode,page_titles_page_ids,page_titles_qitems,group)

    """
    iswiki: 

    inlinks query sencera: 
    0:01:37.282888

    inlinks query sencera batches:
    0:03:26.662578

    inlinks code logics one-by-one:
    0:05:49.295539

    inlinks code logics batches:
    0:02:27.099360

    """


   
    try:
        code_logics(languagecode,page_titles_page_ids,page_titles_qitems,group)
    except:
        try:
            full_query(languagecode,page_titles_page_ids,page_titles_qitems,group)
        except:
            try:
                code_logics_batches(languagecode,page_titles_page_ids,page_titles_qitems,group)
            except:
                full_query_batches(languagecode,page_titles_page_ids,page_titles_qitems,group)


    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    print (duration)
    create_function_account_db(function_name, 'mark', duration)



# Get the Articles table with the number of outlinks.
def label_potencial_ccc_articles_with_outlinks(languagecode,page_titles_page_ids,page_titles_qitems,group):


    def full_query(languagecode,page_titles_page_ids,page_titles_qitems,group):
        print ('Attempt with a MySQL. Full query.')

        # OUTLINKS TO GROUP
        page_titles_outlinks_group = []
        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()

        page_asstring = ','.join( ['%s'] * len( Article_selection ) )
        query = 'SELECT count(pl_title), pl_from FROM pagelinks WHERE pl_from_namespace=0 AND pl_namespace=0 AND pl_title IN (%s) GROUP BY pl_from;' % page_asstring

        mysql_cur_read.execute(query,list(Article_selection.values()))
        rows = mysql_cur_read.fetchall()
    #        print ('query run.')
        for row in rows:
            try:
                page_title=page_ids_page_titles[row[1]]
                page_titles_outlinks_group.append((row[0],row[1],page_titles_qitems[page_title],page_title))
            except: pass

        if group == 'ccc':
            query = 'UPDATE '+languagecode+'wiki SET num_outlinks_to_CCC=? WHERE page_id = ? AND qitem = ? AND page_title=?;'
        else:
            query = 'UPDATE '+languagecode+'wiki SET num_outlinks_to_geolocated_abroad=? WHERE page_id = ? AND qitem = ? AND page_title=?;'

        cursor.executemany(query,page_titles_outlinks_group)
        conn.commit()

        print ('- Articles pointing at the group: '+str(len(page_titles_outlinks_group)))

        # OUTLINKS
        query = 'SELECT count(*) FROM '+languagecode+'wiki WHERE num_outlinks IS NOT NULL;'
        cursor.execute(query)
        if cursor.fetchone()[0] == 0:
            page_titles_outlinks = []
            mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()
            query = 'SELECT count(pl_title),pl_from FROM pagelinks WHERE pl_from_namespace=0 AND pl_namespace=0 GROUP BY pl_from'
            mysql_cur_read.execute(query)
            rows = mysql_cur_read.fetchall()
            for row in rows:
                try:
                    count=row[0]
                    page_title = page_ids_page_titles[row[1]]
                    page_titles_outlinks.append((count,float(count),row[1],page_titles_qitems[page_title],page_title))
                except: continue

            if group == 'ccc':
                query = 'UPDATE '+languagecode+'wiki SET num_outlinks=?,percent_outlinks_to_CCC=(num_outlinks_to_CCC/?) WHERE page_id = ? AND qitem = ? AND page_title=?;'
            else:
                query = 'UPDATE '+languagecode+'wiki SET num_outlinks=?,percent_outlinks_to_geolocated_abroad=(num_outlinks_to_geolocated_abroad/?) WHERE page_id = ? AND qitem = ? AND page_title=?;'

            cursor.executemany(query,page_titles_outlinks)
            conn.commit()
            print ('- Articles with any outlink at all: '+str(len(page_titles_outlinks)))

        # OUTLINKS TO GROUP
        else:
            if group == 'ccc':
                query = 'UPDATE '+languagecode+'wiki SET percent_outlinks_to_CCC=(1.0*num_outlinks_to_CCC/num_outlinks);'
            else:
                query = 'UPDATE '+languagecode+'wiki SET percent_outlinks_to_geolocated_abroad=(1.0*num_outlinks_to_geolocated_abroad/num_outlinks);'
            cursor.execute(query)
            conn.commit()



    def full_query_batches(languagecode,page_titles_page_ids,page_titles_qitems,group):
        print ('Attempt with a MySQL. Full query batches.')

        # OUTLINKS TO GROUP
        page_titles_outlinks_group = []
        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()

        cursor.execute("SELECT max(page_id) FROM "+languagecode+'wiki;')
        maxval = cursor.fetchone()[0]
        page_asstring = ','.join( ['%s'] * len( Article_selection ) )

        increment = 50000
        while (maxval > 0):
            val2 = maxval
            maxval = maxval - increment
            if maxval < 0: maxval = 0
            val1 = maxval

            interval = 'pl_from BETWEEN '+str(val1)+' AND '+str(val2)
            query = 'SELECT count(pl_title), pl_from FROM pagelinks WHERE pl_from_namespace=0 AND pl_namespace=0 AND '+interval+' AND pl_title IN (%s) GROUP BY pl_from;' % page_asstring

            print(interval)
#            print (query)
            mysql_cur_read.execute(query,list(Article_selection.values()))
            rows = mysql_cur_read.fetchall()

            for row in rows:
                try:
                    page_title=page_ids_page_titles[row[1]]
                    page_titles_outlinks_group.append((row[0],row[1],page_titles_qitems[page_title],page_title))
                except: pass

        if group == 'ccc':
            query = 'UPDATE '+languagecode+'wiki SET num_outlinks_to_CCC=? WHERE page_id = ? AND qitem = ? AND page_title=?;'
        else:
            query = 'UPDATE '+languagecode+'wiki SET num_outlinks_to_geolocated_abroad=? WHERE page_id = ? AND qitem = ? AND page_title=?;'

        cursor.executemany(query,page_titles_outlinks_group)
        conn.commit()

        print ('- Articles pointing at the group: '+str(len(page_titles_outlinks_group)))


        # OUTLINKS
        query = 'SELECT count(*) FROM '+languagecode+'wiki WHERE num_outlinks IS NOT NULL;'
        cursor.execute(query)
        if cursor.fetchone()[0] == 0:
            page_titles_outlinks = []
            mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()

            cursor.execute("SELECT max(page_id) FROM "+languagecode+'wiki;')
            maxval = cursor.fetchone()[0]
            increment = 50000
            while (maxval > 0):
                val2 = maxval
                maxval = maxval - increment
                if maxval < 0: maxval = 0
                val1 = maxval

                interval = 'AND pl_from BETWEEN '+str(val1)+' AND '+str(val2)
                query = 'SELECT count(pl_title),pl_from FROM pagelinks WHERE pl_from_namespace=0 AND pl_namespace=0 '+interval+' GROUP BY pl_from'
                print (query)

                mysql_cur_read.execute(query)
                rows = mysql_cur_read.fetchall()
                for row in rows:
                    try:
                        count=row[0]
                        page_title = page_ids_page_titles[row[1]]
                        page_titles_outlinks.append((count,float(count),row[1],page_titles_qitems[page_title],page_title))
                    except: continue

            if group == 'ccc':
                query = 'UPDATE '+languagecode+'wiki SET num_outlinks=?,percent_outlinks_to_CCC=(num_outlinks_to_CCC/?) WHERE page_id = ? AND qitem = ? AND page_title=?;'
            else:
                query = 'UPDATE '+languagecode+'wiki SET num_outlinks=?,percent_outlinks_to_geolocated_abroad=(num_outlinks_to_geolocated_abroad/?) WHERE page_id = ? AND qitem = ? AND page_title=?;'

            cursor.executemany(query,page_titles_outlinks)
            conn.commit()
            print ('- Articles with any outlink at all: '+str(len(page_titles_outlinks)))


        # OUTLINKS TO GROUP
        else:
            if group == 'ccc':
                query = 'UPDATE '+languagecode+'wiki SET percent_outlinks_to_CCC=(1.0*num_outlinks_to_CCC/num_outlinks);'
            else:
                query = 'UPDATE '+languagecode+'wiki SET percent_outlinks_to_geolocated_abroad=(1.0*num_outlinks_to_geolocated_abroad/num_outlinks);'
            cursor.execute(query)
            conn.commit()


    def code_logics(languagecode,page_titles_page_ids,page_titles_qitems,group):

        print ('Attempt with code logics. One by one.')

        #input('')
        cur_time = time.time()
       # get the ccc and potential ccc Articles

        Articles_page_titles = set(Article_selection.values())

        page_titles_outlinks_group = []
        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()

        page_titles=set()
        num_art = 0
#        print ('Progression.')
        for x,y in page_ids_page_titles.items():
    #        print (x)
            query = 'SELECT pl_title FROM pagelinks WHERE pl_namespace=0 AND pl_from_namespace=0 AND pl_from = %s;'
            mysql_cur_read.execute(query,(x,))
            rows = mysql_cur_read.fetchall()
            for row in rows: 
                pl_from = x
                page_titles.add(str(row[0].decode('utf-8')))
            try:
                num_art = num_art + 1
                if num_art % 50000 == 0:
                    print (100*num_art/len(page_ids_page_titles))
                    print (len(page_titles_outlinks_group))
                    print (len(page_ids_page_titles))
                    print ('total time: ' + str(time.time() - functionstartTime))
                    print ('current time: ' + str(time.time() - cur_time))
                    cur_time = time.time()            

                count=len(page_titles.intersection(Articles_page_titles))
                page_title=page_ids_page_titles[pl_from]
                page_titles_outlinks_group.append((count,len(page_titles),float(count)/float(len(page_titles)),pl_from,page_titles_qitems[page_title],page_title))
                page_titles = set()

            except:
                continue
        print ('articles with outlinks: '+str(len(page_titles_outlinks_group)))
        
        # OUTLINKS AND OUTLINKS TO GROUP
        if group == 'ccc':
            query = 'UPDATE '+languagecode+'wiki SET (num_outlinks_to_CCC,num_outlinks,percent_outlinks_to_CCC)=(?,?,?) WHERE page_id = ? AND qitem = ? AND page_title=?;'
        else:
            query = 'UPDATE '+languagecode+'wiki SET (num_outlinks_to_geolocated_abroad,num_outlinks,percent_outlinks_to_geolocated_abroad)=(?,?,?) WHERE page_id = ? AND qitem = ? AND page_title=?;'

        cursor.executemany(query,page_titles_outlinks_group)
        conn.commit()


    def code_logics_batches(languagecode,page_titles_page_ids,page_titles_qitems,group):

        print ('Attempt with code logics. Batches.')
        #input('')
        cur_time = time.time()
       # get the ccc and potential ccc Articles

        Articles_page_titles = set(Article_selection.values())
        page_titles_outlinks_group = list()

        print ('Trying to run the query with batches: '+languagecode)
        cursor.execute("SELECT max(page_id) FROM "+languagecode+'wiki;')
        maxval = cursor.fetchone()[0]
        print (maxval)

        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()

        increment = 50000
        while (maxval > 0):
            val2 = maxval
            maxval = maxval - increment
            if maxval < 0: maxval = 0
            val1 = maxval

            interval = 'AND pl_from BETWEEN '+str(val1)+' AND '+str(val2)+' ORDER BY pl_from'
            query = 'SELECT pl_title, pl_from FROM pagelinks WHERE pl_namespace=0 AND pl_from_namespace=0 '+interval
            print (query)
            mysql_cur_read.execute(query)
            rows = mysql_cur_read.fetchall()
            num_art = 0
            old_pl_from = ''
            page_titles = set()

            for row in rows: 
                pl_from = row[1]

                if old_pl_from != pl_from and old_pl_from!='':

                    num_art = num_art + 1
                    if num_art % 50000 == 0:
                        print (100*num_art/len(page_ids_page_titles))
                        print (len(page_titles_outlinks_group))
                        print (len(page_ids_page_titles))
                        print ('total time: ' + str(time.time() - functionstartTime))
                        print ('current time: ' + str(time.time() - cur_time))
                        cur_time = time.time()            

                    try:
#                        count=len(page_titles)-(len(set(page_titles)-set(Articles_page_titles)))
                        count=len(page_titles.intersection(Articles_page_titles))
                        page_title=page_ids_page_titles[old_pl_from]
                        page_titles_outlinks_group.append((count,len(page_titles),float(count)/float(len(page_titles)),old_pl_from,page_titles_qitems[page_title],page_title))
                        page_titles.clear()
                    except:
                        page_titles.clear()
                        pass


                page_titles.add(str(row[0].decode('utf-8')))
                old_pl_from = pl_from

            try:
                num_art = num_art + 1
                if num_art % 1000 == 0:
                    print (100*num_art/len(page_ids_page_titles))
                    print (len(page_titles_outlinks_group))
                    print (len(page_ids_page_titles))
                    print ('total time: ' + str(time.time() - functionstartTime))
                    print ('current time: ' + str(time.time() - cur_time))
                    cur_time = time.time()            

                count=len(page_titles.intersection(Articles_page_titles))
#                count=len(page_titles)-(len(set(page_titles)-set(Articles_page_titles)))
                page_title=page_ids_page_titles[old_pl_from]
                page_titles_outlinks_group.append((count,len(page_titles),float(count)/float(len(page_titles)),old_pl_from,page_titles_qitems[page_title],page_title))
                page_titles.clear()
            except:
                page_titles.clear()
                pass


        # OUTLINKS AND OUTLINKS TO GROUP
        if group == 'ccc':
            query = 'UPDATE '+languagecode+'wiki SET (num_outlinks_to_CCC,num_outlinks,percent_outlinks_to_CCC)=(?,?,?) WHERE page_id = ? AND qitem = ? AND page_title=?;'
        else:
            query = 'UPDATE '+languagecode+'wiki SET (num_outlinks_to_geolocated_abroad,num_outlinks,percent_outlinks_to_geolocated_abroad)=(?,?,?) WHERE page_id = ? AND qitem = ? AND page_title=?;'

        cursor.executemany(query,page_titles_outlinks_group)
        conn.commit()
        print ('articles with outlinks: '+str(len(page_titles_outlinks_group)))



    functionstartTime = time.time()
    function_name = 'label_potencial_ccc_articles_with_outlinks '+group+' '+languagecode
    if create_function_account_db(function_name, 'check','')==1: return

    page_ids_page_titles = {v: k for k, v in page_titles_page_ids.items()}


    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()
    Article_selection = {}
    if group == 'ccc':
        query = 'SELECT page_id, page_title FROM '+languagecode+'wiki WHERE ccc_binary=1;'
        for row in cursor.execute(query):
            Article_selection[row[0]]=row[1]
#        print ('- Articles in CCC: '+str(len(article_selection)))
    else:
        query = 'SELECT page_id, page_title FROM '+languagecode+'wiki WHERE ccc_binary=0;'
        for row in cursor.execute(query):
            Article_selection[row[0]]=row[1]
#        print ('- Articles with other language CCC relationships: '+str(len(article_selection)))


#    full_query(languagecode,page_titles_page_ids,page_titles_qitems,group)
#    full_query_batches(languagecode,page_titles_page_ids,page_titles_qitems,group)
#    code_logics_batches(languagecode,page_titles_page_ids,page_titles_qitems,group)
#    code_logics(languagecode,page_titles_page_ids,page_titles_qitems,group)

    """
    iswiki
    outlinks query sencera: 
    0:01:12.503035

    outlinks query sencera batches:
    0:01:50.865450

    outlinks code logics one-by-one:
    articles with outlinks: 46612
    0:03:48.656990

    outlinks code logics batches:
    0:01:58.0684440:01:45.740129
    """

    try:
        code_logics(languagecode,page_titles_page_ids,page_titles_qitems,group)   
    except:
        try:
            full_query_batches(languagecode,page_titles_page_ids,page_titles_qitems,group)    
        except:
            try:
                code_logics_batches(languagecode,page_titles_page_ids,page_titles_qitems,group)
            except:
                full_query(languagecode,page_titles_page_ids,page_titles_qitems,group)  
                

    
    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    print(duration)
    create_function_account_db(function_name, 'mark', duration)



# Extends the Articles table with the first timestamp.
def extend_articles_timestamp(languagecode, page_titles_qitems, page_titles_page_ids):

    function_name = 'extend_articles_timestamp '+languagecode
    if create_function_account_db(function_name, 'check','')==1: return

    functionstartTime = time.time()
    last_period_time = functionstartTime

    page_ids_page_titles = {v: k for k, v in page_titles_page_ids.items()}

    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()
    page_ids_timestamps = []

    try:
        print ('Trying to run the entire query: '+languagecode)
        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()
        mysql_cur_read.execute("SELECT MIN(rev_timestamp),rev_page FROM revision GROUP by rev_page")
        rows = mysql_cur_read.fetchall()
        for row in rows: 
            try:
                page_id = row[1]
                page_title = page_ids_page_titles[page_id]
                qitem = page_titles_qitems[page_title]
                page_ids_timestamps.append((str(row[0].decode('utf-8')),page_id,qitem))
            except: pass
    except:
        print ('Trying to run the query with batches: '+languagecode)
        cursor.execute("SELECT max(page_id) FROM "+languagecode+'wiki;')
        maxval = cursor.fetchone()[0]
        print (maxval)

        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()
        increment = 500000
        while (maxval > 0):
            val2 = maxval
            maxval = maxval - increment
            if maxval < 0: maxval = 0
            val1 = maxval
            interval = 'WHERE rev_page BETWEEN '+str(val1)+' AND '+str(val2)
            query = "SELECT MIN(rev_timestamp),rev_page FROM revision "+interval+" GROUP by rev_page"
            print (query)
            mysql_cur_read.execute(query)
            rows = mysql_cur_read.fetchall()
            for row in rows: 
                try:
                    page_id = row[1]
                    page_title = page_ids_page_titles[page_id]
                    qitem = page_titles_qitems[page_title]
                    page_ids_timestamps.append((str(row[0].decode('utf-8')),page_id,qitem))
                except: pass
            print (len(page_ids_timestamps))
            print (str(datetime.timedelta(seconds=time.time() - last_period_time))+' seconds.')
            print (str(len(page_ids_timestamps)/int(datetime.timedelta(seconds=time.time() - last_period_time).total_seconds()))+' rows per second.')
            last_period_time = time.time()

    query = 'UPDATE '+languagecode+'wiki SET date_created=? WHERE page_id = ? AND qitem = ?;'
    cursor.executemany(query,page_ids_timestamps)
    conn.commit()

    print ('CCC timestamp updated.')
    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    create_function_account_db(function_name, 'mark', duration)


# Extends the Articles table with the number of editors per Article.
def extend_articles_editors(languagecode, page_titles_qitems, page_titles_page_ids):

    function_name = 'extend_articles_editors '+languagecode
    if create_function_account_db(function_name, 'check','')==1: return

    functionstartTime = time.time()
    last_period_time = functionstartTime

    page_titles_editors = []
    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()

    page_ids_page_titles = {v: k for k, v in page_titles_page_ids.items()}

    # I tried to introduce a timeout to the entire query and it did not work. It was not effective.
    try:
        print ('(1) Trying to run the entire query: '+languagecode)

        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()

#        query = 'SELECT COUNT(DISTINCT revactor_actor), revactor_page FROM revision_actor_temp GROUP BY revactor_page;'
        query = 'SELECT COUNT(DISTINCT rev_actor),rev_page FROM revision GROUP BY rev_page'

        mysql_cur_read.execute(query)
        rows = mysql_cur_read.fetchall()
        for row in rows: 
            try:
                page_id = row[1]
                page_title = page_ids_page_titles[page_id]
                qitem = page_titles_qitems[page_title]
                page_titles_editors.append((row[0],page_id,qitem))
            except: pass

        query = 'UPDATE '+languagecode+'wiki SET num_editors=? WHERE page_id = ? AND qitem = ?;'
        cursor.executemany(query,page_titles_editors)
        conn.commit()
        print ('done')

    except:       
        print ('(2) Trying to run the query with batches: '+languagecode)
        cursor.execute("SELECT max(page_id) FROM "+languagecode+'wiki;')
        maxval = cursor.fetchone()[0]
        print (maxval)

        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()
        increment = 100000

        increment = 50000

        range_values = 0
        round_seconds = 0

        max_round_seconds = 3000

        while (range_values < maxval and round_seconds < max_round_seconds):
            page_titles_editors = []
            val1 = range_values
            range_values = range_values + increment
            if range_values > maxval: range_values = maxval
            val2 = range_values
            interval = 'WHERE rev_page BETWEEN '+str(val1)+' AND '+str(val2)

            query = 'SELECT COUNT(DISTINCT rev_actor),rev_page FROM revision '+interval+' GROUP BY rev_page;'
#            query = 'SELECT COUNT(DISTINCT rev_actor),rev_page FROM revision INNER JOIN page ON rev_page = page_id WHERE page_namespace=0 AND page_is_redirect=0 '+interval+' GROUP BY rev_page'
            print (query)
            mysql_cur_read.execute(query)
            rows = mysql_cur_read.fetchall()
            for row in rows: 
                try:
                    page_id = row[1]
                    page_title = page_ids_page_titles[page_id]
                    qitem = page_titles_qitems[page_title]
                    page_titles_editors.append((row[0],page_id,qitem))
                except: pass
            round_seconds = datetime.timedelta(seconds=time.time() - last_period_time)
            print (len(page_titles_editors))
            print (str(round_seconds)+' seconds.')
            print (str(len(page_titles_editors)/int(datetime.timedelta(seconds=time.time() - last_period_time).total_seconds()))+' rows per second.')
            last_period_time = time.time()

            query = 'UPDATE '+languagecode+'wiki SET num_editors=? WHERE page_id = ? AND qitem = ?;'
            cursor.executemany(query,page_titles_editors)
            conn.commit()


        if round_seconds > max_round_seconds:
            print ('(3) Trying counting all the revision editors in batches.')

            page_titles_editors = []
            mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()


            mysql_cur_read.execute("SELECT max(rev_page) FROM revision;")
            maxval = mysql_cur_read.fetchone()[0]
            print (maxval)

        #    increment = 500000
        #    increment = 250000
        #    increment = 50000
            increment = 25000
            iterations = int(maxval/increment)
            print ('There are '+str(iterations)+' intervals.')

            i = 0
            while (range_values < maxval):

                val1 = range_values
                range_values = range_values + increment
                if range_values > maxval: range_values = maxval
                val2 = range_values


                interval = 'WHERE rev_page BETWEEN '+str(val1)+' AND '+str(val2)+' ORDER BY rev_page'
                query = 'SELECT rev_page, rev_actor FROM revision '+interval

                print (query)
                parameters = []
    #            try:

                mysql_cur_read.execute(query)
                rows = mysql_cur_read.fetchall()
        #        file = open(revisions_path+filename,'a') 

                old_page_id = ''
                cur_page_id = ''
                cur_page_id_in = 0
                actors = set()

                k = 0
                for row in rows:

                    cur_page_id = row[0]
                    rev_actor = int(row[1])

                    if cur_page_id != old_page_id and cur_page_id_in == 1:
                        i+=1
                        num_editors = len(actors)
                        actors = set()
                        page_titles_editors.append((num_editors,old_page_id,qitem))

    #                    print ('this goes in:')
    #                    print(i,page_title,(num_editors,old_page_id,qitem))
                                   
                        if i % 10000 == 0:
    #                        input('')
                            print (str(i)+' pages.')
    #                        print (len(page_titles_editors))
                            query = 'UPDATE '+languagecode+'wiki SET num_editors=? WHERE page_id = ? AND qitem = ?;'
                            cursor.executemany(query,page_titles_editors)
                            conn.commit()
                            page_titles_editors = []

                    if cur_page_id != old_page_id or k == 0:
                        try:
                            page_title = page_ids_page_titles[cur_page_id]
                            qitem = page_titles_qitems[page_title]
                            cur_page_id_in = 1
                        except:
                            cur_page_id_in = 0
                        print(page_title,cur_page_id_in)

                    if cur_page_id_in == 1:
                        actors.add(rev_actor)

                    old_page_id = cur_page_id
                    k+=1

    #            except:
    #                print ('the query timed out.')
            print('Counting all revision editors worked.')


    print ('Editors updated.')
    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    create_function_account_db(function_name, 'mark', duration)

# Extends the Articles table with the number of discussions per Article.
def extend_articles_discussions(languagecode, page_titles_qitems, page_titles_page_ids):
    function_name = 'extend_articles_discussions '+languagecode
    if create_function_account_db(function_name, 'check','')==1: return

    functionstartTime = time.time()
    last_period_time = functionstartTime

    updated = []
    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()

    try:
        print ('Trying to run the entire query: '+languagecode)
        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()
        mysql_cur_read.execute("SELECT page_title, COUNT(*) FROM revision r, page p WHERE r.rev_page=p.page_id AND p.page_namespace=1 GROUP by page_title;")
        rows = mysql_cur_read.fetchall()
        for row in rows:
            page_title=str(row[0].decode('utf-8'))
            try: updated.append((row[1],page_titles_page_ids[str(row[0].decode('utf-8'))],page_titles_qitems[page_title]))
            except: pass

        query = 'UPDATE '+languagecode+'wiki SET num_discussions=? WHERE page_id = ? AND qitem = ?;'
        cursor.executemany(query,updated)
        conn.commit()

    except:
        print ('Trying to run the query with batches: '+languagecode)
        cursor.execute("SELECT max(page_id) FROM "+languagecode+'wiki;')
        maxval = cursor.fetchone()[0]
        print (maxval)

        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()
        increment = 10000000
        while (maxval > 0):
            updated = []
            val2 = maxval
            maxval = maxval - increment
            if maxval < 0: maxval = 0
            val1 = maxval
            interval = 'AND page_id BETWEEN '+str(val1)+' AND '+str(val2)
            query = "SELECT COUNT(*), page_title FROM revision r, page p WHERE r.rev_page=p.page_id AND p.page_namespace=1 "+interval+" GROUP by page_title;"
            print (query)
            mysql_cur_read.execute(query)
            rows = mysql_cur_read.fetchall()
            for row in rows: 
                try: updated.append((row[0],page_titles_page_ids[str(row[1].decode('utf-8'))],page_titles_qitems[str(row[1].decode('utf-8'))]))
                except: pass
            print (len(updated))
            print (str(datetime.timedelta(seconds=time.time() - last_period_time))+' seconds.')
            print (str(len(updated)/int(datetime.timedelta(seconds=time.time() - last_period_time).total_seconds()))+' rows per second.')
            last_period_time = time.time()

            query = 'UPDATE '+languagecode+'wiki SET num_discussions=? WHERE page_id = ? AND qitem = ?;'
            cursor.executemany(query,updated)
            conn.commit()

    print ('Discussions updated.')
    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    create_function_account_db(function_name, 'mark', duration)


# Extends the Articles table with the number of edits per Article.
def extend_articles_edits(languagecode, page_titles_qitems,page_titles_page_ids):

    functionstartTime = time.time()
    last_period_time = functionstartTime
    function_name = 'extend_articles_edits '+languagecode
    if create_function_account_db(function_name, 'check','')==1: return

    page_ids_edits = []
    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()
    page_ids_page_titles = {v: k for k, v in page_titles_page_ids.items()}

    try:
        print ('Trying to run the entire query: '+languagecode)
        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()
        query = "SELECT rev_page, COUNT(*) FROM revision GROUP by rev_page;"
        mysql_cur_read.execute(query)
        rows = mysql_cur_read.fetchall()
        for row in rows:
            count=row[1]
            try:
                page_title = page_ids_page_titles[row[0]]
                qitem = page_titles_qitems[page_title]
                page_ids_edits.append((count,page_id,qitem))
            except: pass

        query = 'UPDATE '+languagecode+'wiki SET num_edits=? WHERE page_id = ? AND qitem = ?;'
        cursor.executemany(query,page_ids_edits)
        conn.commit()

    except:
        print ('Trying to run the query with batches: '+languagecode)
        cursor.execute("SELECT max(page_id) FROM "+languagecode+'wiki;')
        maxval = int(cursor.fetchone()[0])

        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()
        increment = 50000
        print ('There are '+str(int(maxval/increment))+' iterations.')

        range_values = 0
        while (range_values < maxval):
            page_ids_edits = []
            val1 = range_values
            range_values = range_values + increment
            if range_values > maxval: range_values = maxval
            val2 = range_values

            interval = 'rev_page BETWEEN '+str(val1)+' AND '+str(val2)
            query = "SELECT COUNT(*), rev_page FROM revision WHERE "+interval+" GROUP by rev_page;"
            print (query)
            mysql_cur_read.execute(query)
            rows = mysql_cur_read.fetchall()
            for row in rows: 
                try:
                    page_id = row[1]
                    page_title = page_ids_page_titles[page_id]
                    qitem = page_titles_qitems[page_title]
                    page_ids_edits.append((row[0],page_id,qitem))
                except: pass
            print (len(page_ids_edits))
            batchtime = int(datetime.timedelta(seconds=time.time() - last_period_time).total_seconds())
            print (str(batchtime)+' seconds.')
            print (str(len(page_ids_edits)/batchtime)+' rows per second.')
            last_period_time = time.time()

            query = 'UPDATE '+languagecode+'wiki SET num_edits=? WHERE page_id = ? AND qitem = ?;'
            cursor.executemany(query,page_ids_edits)
            conn.commit()

    print ('Edits updated.')
    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    create_function_account_db(function_name, 'mark', duration)


# Extends the Articles table with the number of edits per Article.
def extend_articles_edits_last_month(languagecode, page_titles_qitems,page_titles_page_ids):

    functionstartTime = time.time()
    last_period_time = functionstartTime
    function_name = 'extend_articles_edits_last_month '+languagecode
    if create_function_account_db(function_name, 'check','')==1: return

    page_ids_edits = []
    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()
    page_ids_page_titles = {v: k for k, v in page_titles_page_ids.items()}

    last_month_date = datetime.date.today() - relativedelta.relativedelta(months=1)
    first_day = last_month_date.replace(day = 1).strftime('%Y%m%d%H%M%S')
    last_day = last_month_date.replace(day = calendar.monthrange(last_month_date.year, last_month_date.month)[1]).strftime('%Y%m%d%H%M%S')
    month_condition = 'rev_timestamp >= "'+ first_day +'" AND rev_timestamp < "'+last_day+'"'


    try:
        print ('Trying to run the entire query: '+languagecode)
        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()

        query = "SELECT rev_page, COUNT(*) FROM revision WHERE "+month_condition+" GROUP by rev_page;"
        mysql_cur_read.execute(query)
        rows = mysql_cur_read.fetchall()
        for row in rows:
            page_id=row[0]
            count=row[1]
            try: 
                page_title=page_ids_page_titles[page_id]
                page_ids_edits.append((count,page_id,page_titles_qitems[page_title]))
            except: 
                pass

        query = 'UPDATE '+languagecode+'wiki SET num_edits_last_month=? WHERE page_id = ? AND qitem = ?;'
        cursor.executemany(query,page_ids_edits)
        conn.commit()

    except:
        print ('Trying to run the query with batches: '+languagecode)
        cursor.execute("SELECT max(page_id) FROM "+languagecode+'wiki;')
        maxval = int(cursor.fetchone()[0])
        print (maxval)

        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()
        increment = 50000
        print ('There are '+str(int(maxval/increment))+' iterations.')

        range_values = 0
        while (range_values < maxval):
            page_ids_edits = []
            val1 = range_values
            range_values = range_values + increment
            if range_values > maxval: range_values = maxval
            val2 = range_values

            interval = 'rev_page BETWEEN '+str(val1)+' AND '+str(val2)
            query = "SELECT COUNT(*), rev_page FROM revision WHERE "+interval+" AND "+month_condition+" GROUP by rev_page;"
            print (query)
            mysql_cur_read.execute(query)
            rows = mysql_cur_read.fetchall()
            for row in rows:
                try:
                    page_id = row[1]
                    qitem = page_titles_qitems[page_ids_page_titles[page_id]]
                    page_ids_edits.append((row[0],page_id,qitem))
                except: pass
            print (len(page_ids_edits))
            print (str(datetime.timedelta(seconds=time.time() - last_period_time))+' seconds.')
            print (str(len(page_ids_edits)/int(datetime.timedelta(seconds=time.time() - last_period_time).total_seconds()))+' rows per second.')
            last_period_time = time.time()

            query = 'UPDATE '+languagecode+'wiki SET num_edits_last_month=? WHERE page_id = ? AND qitem = ?;'
            cursor.executemany(query,page_ids_edits)
            conn.commit()

    print ('Edits last month updated.')
    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    create_function_account_db(function_name, 'mark', duration)




def extend_articles_references(languagecode, page_titles_qitems, page_titles_page_ids):

    functionstartTime = time.time()
    last_period_time = functionstartTime
    function_name = 'extend_articles_references '+languagecode
    if create_function_account_db(function_name, 'check','')==1: return

    page_ids_references = []
    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()
    page_ids_page_titles = {v: k for k, v in page_titles_page_ids.items()}
#    print (len(page_titles_page_ids))

    try:
        i = 0
        print ('Trying to run the entire query: '+languagecode)
        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()
        mysql_cur_read.execute("SELECT el_from, COUNT(*) FROM externallinks GROUP by el_from;")
        rows = mysql_cur_read.fetchall()
        for row in rows:
            try: 
                page_id=row[0]
                count=row[1]
                qitem = page_titles_qitems[page_ids_page_titles[page_id]]
                page_ids_references.append((count,page_id,qitem))
                i += 1
            except: 
                pass

        query = 'UPDATE '+languagecode+'wiki SET num_references=? WHERE page_id = ? AND qitem = ?;'
        cursor.executemany(query,page_ids_references)
        conn.commit()
    except:
        print ('Trying to run the query with batches: '+languagecode)
        cursor.execute("SELECT max(page_id) FROM "+languagecode+'wiki;')
        maxval = int(cursor.fetchone()[0])
#        print (maxval)

        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()
        increment = 1000000
        range_values = 0
        i = 0
        while (range_values < maxval):
            val1 = range_values
            range_values = range_values + increment
            if range_values > maxval: range_values = maxval
            val2 = range_values

            interval = 'WHERE el_from BETWEEN '+str(val1)+' AND '+str(val2)
            query = "SELECT el_from, COUNT(*) FROM externallinks "+interval+" GROUP by el_from;"

            print (query)
            mysql_cur_read.execute(query)
            rows = mysql_cur_read.fetchall()
            for row in rows:
                try:
                    page_id=row[0]
                    count=row[1]
                    qitem = page_titles_qitems[page_ids_page_titles[page_id]]
                    page_ids_references.append((count,page_id,qitem))
                    i+=1
                except: pass

            print (len(page_ids_references))
            print (str(datetime.timedelta(seconds=time.time() - last_period_time))+' seconds.')
            print (str(len(page_ids_references)/int(datetime.timedelta(seconds=time.time() - last_period_time).total_seconds()))+' rows per second.')
            last_period_time = time.time()

        query = 'UPDATE '+languagecode+'wiki SET num_references=? WHERE page_id = ? AND qitem = ?;'
        cursor.executemany(query,page_ids_references)
        conn.commit()

    print (str(i)+' References updated.')
    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    create_function_account_db(function_name, 'mark', duration)



def extend_articles_bytes(languagecode, page_titles_qitems):

    functionstartTime = time.time()
    last_period_time = functionstartTime
    function_name = 'extend_articles_bytes '+languagecode
    if create_function_account_db(function_name, 'check','')==1: return

    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()
    mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()
    mysql_cur_read.execute("SELECT page_title, page_id, page_len FROM page;")
    rows = mysql_cur_read.fetchall()
    for row in rows:
        page_title=str(row[0].decode('utf-8'))
        page_id=row[1]
        count=row[2]
        try:
            query = 'UPDATE '+languagecode+'wiki SET num_bytes=? WHERE page_id = ? AND qitem = ?;'
            cursor.execute(query,(count,page_id,page_titles_qitems[page_title]))
        except:
            pass
    conn.commit()

    print ('Bytes updated.')
    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    create_function_account_db(function_name, 'mark', duration)



# Extends the Articles table with the number of images.
def extend_articles_images(languagecode,page_titles_qitems,page_titles_page_ids):

    functionstartTime = time.time()
    function_name = 'extend_articles_images '+languagecode
    if create_function_account_db(function_name, 'check','')==1: return

    conn2 = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor2 = conn2.cursor()

    page_ids_page_titles = {v: k for k, v in page_titles_page_ids.items()}

    updated = []
    mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()

    mysql_cur_read.execute("SELECT il_from, count(il_to) FROM imagelinks GROUP BY il_from")
    rows = mysql_cur_read.fetchall()

    for row in rows:
        try:
            page_id=row[0]
            qitem = page_titles_qitems[page_ids_page_titles[page_id]]
            image_count=row[1]
            updated.append((image_count,page_id,qitem))
        except:
            pass
    query = 'UPDATE '+languagecode+'wiki SET num_images = ? WHERE page_id = ? AND qitem = ?;'
    print ('There are '+str(len(updated))+' articles with images.')

    cursor2.executemany(query,updated)
    conn2.commit()
    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    create_function_account_db(function_name, 'mark', duration)


# Extends the Articles table with the number of pageviews.
def extend_articles_pageviews(languagecode, page_titles_qitems, page_titles_page_ids):

    functionstartTime = time.time()
    function_name = 'extend_articles_pageviews '+languagecode
    if create_function_account_db(function_name, 'check','')==1: return

    conn = sqlite3.connect(databases_path + 'pageviews.db'); cursor = conn.cursor()
    conn2 = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor2 = conn2.cursor()

    query = "SELECT page_title, num_pageviews FROM pageviews WHERE languagecode = '"+languagecode+"';"
    updated = []
    for row in cursor.execute(query):
        try:
            page_title=row[0]
            pageviews=row[1]
            page_id = page_titles_page_ids[page_title]
            qitem = page_titles_qitems[page_title]
#            print (page_title,pageviews,page_id,qitem)
            updated.append((pageviews,page_id,qitem))
        except: 
            pass

    query = 'UPDATE '+languagecode+'wiki SET num_pageviews=? WHERE page_id = ? AND qitem = ?;'
    cursor2.executemany(query,updated)
    conn2.commit()
    print (str(len(updated))+' Articles with pageviews updated.')
    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    create_function_account_db(function_name, 'mark', duration)






def extend_articles_revision_features(languagecode, page_titles_qitems, page_titles_page_ids):

    functionstartTime = time.time()
    function_name = 'extend_articles_revision_features '+languagecode
    if wikilanguages_utils.verify_function_run(cycle_year_month, script_name, function_name, 'check','')==1: return

    num_editors = {}
    num_edits = {}
    num_edits_last_month = {}
    first_edit_timestamp = {}
    num_discussions = {}


    page_ids_qitems = {}
    for page_title,page_id in page_titles_page_ids.items():
        page_ids_qitems[page_id]=page_titles_qitems[page_title]

    for page_id in page_titles_page_ids.values():
        num_discussions[page_id]=0
        num_editors[page_id]=set()
        num_edits[page_id]=0
        num_edits_last_month[page_id]=0
        first_edit_timestamp[page_id]=''

    last_month_date = datetime.date.today() - relativedelta.relativedelta(months=1)
    first_day = int(last_month_date.replace(day = 1).strftime('%Y%m%d%H%M%S'))
    last_day = int(last_month_date.replace(day = calendar.monthrange(last_month_date.year, last_month_date.month)[1]).strftime('%Y%m%d%H%M%S'))

    d_paths = []
    i = 0
    loop = True
    while (loop):
        i+=1
        dumps_path = '/public/dumps/public/'+languagecode+'wiki/latest/'+languagecode+'wiki-latest-stub-meta-history'+str(i)+'.xml.gz'
        loop = os.path.isfile(dumps_path)
        dumps_path = '/srv/wcdo/dumps/enwiki-latest-stub-meta-history'+str(i)+'.xml'#.gz'
        if loop == True: 
            d_paths.append(dumps_path)
        if i==1 and loop == False:#True:
            d_paths.append('/public/dumps/public/'+languagecode+'wiki/latest/'+languagecode+'wiki-latest-stub-meta-history.xml.gz')

    print(len(d_paths))

    page_title_page_id = {}
    for dump_path in d_paths:

        print(dump_path)

        page_title = None
        cur_page_title = None
        ns = None
        page_id = None

        cur_time = time.time()
        i=0

        n_discussions = 0
        n_edits = 0
        n_editors = set()


#        with gzip.open(dump_path, 'rb') as xml_file:
        pages = etree.iterparse(dump_path, events=("start", "end"))
        for event, elem in pages:

            if event == 'start':

                if elem.tag == '{http://www.mediawiki.org/xml/export-0.10/}mediawiki':
                    root = elem

            elif event == 'end':
                # SECTION PAGETITLE, PAGEID, NS

                taggy = elem.tag.replace('{http://www.mediawiki.org/xml/export-0.10/}','')
                text =  elem.text
#                print (taggy)
#                print (text)

                if taggy == 'title': 
                    page_title = text.replace(' ','_')

                # if elem.attrib != None:
                #     try:
                #         page_title = elem.attrib['title'].replace(' ','_')
                #     except:
                #         pass

                if page_title != cur_page_title and cur_page_title != None:
                    num_edits[page_id] = n_edits
                    n_edits = 0
                    num_editors[page_id]=len(n_editors)
                    n_editors=set()
                    num_discussions[page_id]=n_discussions
                    page_id = None

                    i+=1
                    if i%100==0: 
                        last_time=cur_time
                        cur_time=time.time()
                        print('\t'+str(i)+' '+str(datetime.timedelta(seconds=cur_time - last_time)))
                        print(str(round(100/(cur_time - last_time),3))+' '+'pages per second.')

                cur_page_title = page_title

                if taggy == 'id' and page_id == None:
                    page_id = int(text)

                    if ns == 0:
                        try:
                          qitem = page_ids_qitems[page_id] # only to create a page_id None in case it is not there
                          page_title_page_id[cur_page_title]=page_id
                        except:
                            page_id = None

                    if ns == 1:
                        title = cur_page_title.split(':')[1]
                        try:
                            page_id = page_title_page_id[title]
                            qitem = page_ids_qitems[page_id] # only to create a page_id None in case it is not there
                        except:
                            page_id = None

                if taggy == 'ns':
                    ns = int(text)

                if (taggy == 'username' or taggy == 'ip') and page_id != None:
                    username = text

                    if ns == 0:
                        n_editors.add(username)
                        n_edits+=1

                    if ns == 1 and page_id!= None:
                        n_discussions+=1
#                        print(page_id,ns,cur_page_title)

                if taggy == 'timestamp' and ns == 0 and page_id != None: 

                    timestamp = datetime.datetime.strptime(text,'%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d%H%M%S')
                    if first_edit_timestamp[page_id]=='': first_edit_timestamp[page_id] = timestamp
                    timestamp = int(timestamp)
                    if timestamp > first_day and timestamp < last_day:
                        num_edits_last_month[page_id]+=1

                elem.clear()

    print('parsed')

    page_ids_page_titles = {v: k for k, v in page_title_page_id.items()}
    parameters = []
    for page_id in num_editors:
        # print((len(num_editors[page_id]), 
        #     num_edits[page_id], 
        #     num_edits_last_month[page_id], 
        #     first_edit_timestamp[page_id], 
        #     num_discussions[page_id], 
        #     page_id, 
        #     page_ids_qitems[page_id], 
        #     page_ids_page_titles[page_id]))

        try:
            parameters.append((num_editors[page_id], num_edits[page_id], num_edits_last_month[page_id], first_edit_timestamp[page_id], num_discussions[page_id], page_id, page_ids_qitems[page_id], page_ids_page_titles[page_id]))
        except:
            pass
#    print (len(parameters),len(page_titles_qitems))

    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()

    query = 'UPDATE '+languagecode+'wiki SET (num_editors, num_edits, num_edits_last_month, date_created,num_discussions)=(?,?,?,?,?) WHERE page_id = ? AND qitem = ? AND page_title=?;'
    cursor.executemany(query,parameters)
    conn.commit()

    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    wikilanguages_utils.verify_function_run(cycle_year_month, script_name, function_name, 'mark', duration)



def download_latest_wikidata_dump():
    function_name = 'download_latest_wikidata_dump'
    if create_function_account_db(function_name, 'check','')==1: return

    functionstartTime = time.time()
    print ('* Downloading the latest Wikidata dump.')
    url = "https://dumps.wikimedia.org/wikidatawiki/entities/latest-all.json.gz" # download the dump: https://dumps.wikimedia.org/wikidatawiki/entities/20180212/
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(dumps_path + local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=10240): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    create_function_account_db(function_name, 'mark', duration)


def download_latest_pageviews_dump():
    functionstartTime = time.time()
    print ('* Downloading the latest pageviews dump.')

    increment = 1
    exists = False
    while exists==False:
        lastMonth = datetime.date.today() - datetime.timedelta(days=increment)
        month_day = lastMonth.strftime("%Y-%m")
        filename = 'pagecounts-'+month_day+'-views-ge-5-totals.bz2'
        url = 'https://dumps.wikimedia.org/other/pagecounts-ez/merged/'+filename
        exists = (requests.head(url).status_code == 200)
        increment = increment + 30

    print (url)
    local_filename =dumps_path + url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=10240): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()

    os.rename(dumps_path+filename,dumps_path+'latest_pageviews.bz2')
    print ('* download_latest_pageviews_dump Function completed after: ' + str(datetime.timedelta(seconds=time.time() - functionstartTime)))



def pageviews_dump_iterator():
    print ('Iterating the pageviews dump.')
    conn = create_pageviews_db(); cursor = conn.cursor()

    read_dump = dumps_path + 'latest_pageviews.bz2'
    pageviews_dict = {}
    dump_in = bz2.open(read_dump, 'r')
    line = dump_in.readline()
    line = line.rstrip().decode('utf-8')[:-1]
    values=line.split(' ')
    last_language = values[0].split('.')[0]

    iter = 0
    while line != '':
        iter += 1
        if iter % 10000000 == 0: print (str(iter/10000000)+' million lines.')
        line = dump_in.readline()
        line = line.rstrip().decode('utf-8')[:-1]
        values=line.split(' ')

        if len(values)<3: continue
        language = values[0].split('.')[0]
        page_title = values[1]
        pageviews_count = values[2]

        if language!=last_language:
            print (last_language)
            print (len(pageviews_dict))
            pageviews = []
            for key in pageviews_dict:
                try:
#                    if last_language=='ca':
#                        print ((key[0], key[1], pageviews_dict[(key[0],key[1])]))
                    pageviews.append((key[0], key[1], pageviews_dict[(key[0],key[1])]))
                except:
                    pass

            query = "INSERT INTO pageviews (languagecode, page_title, num_pageviews) VALUES (?,?,?);"
            cursor.executemany(query,pageviews)
            conn.commit()
            pageviews_dict={}
#            input('')

        if pageviews_count == '': continue
#            print (line)
        if (language,page_title) in pageviews_dict: 
            pageviews_dict[(language,page_title)]=pageviews_dict[(language,page_title)]+int(pageviews_count)
        else:
            pageviews_dict[(language,page_title)]=int(pageviews_count)

#        if page_title == 'Berga' and language == 'ca':
#            print (line)
#            print ((language,page_title))
#            print (pageviews_dict[(language,page_title)])
#            input('')

        last_language=language

    print ('Pageviews have been introduced into the database.')



def delete_latest_pageviews_dump():
    function_name = 'delete_latest_pageviews_dump'
    if create_function_account_db(function_name, 'check','')==1: return
    functionstartTime = time.time()
    os.remove(dumps_path + "latest_pageviews.bz2")
    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    create_function_account_db(function_name, 'mark', duration)


def delete_pageviews_db():
    function_name = 'delete_pageviews_db'
    if create_function_account_db(function_name, 'check','')==1: return
    functionstartTime = time.time()
    os.remove(databases_path + "pageviews.db")
    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    create_function_account_db(function_name, 'mark', duration)


# WE ARE NOT CRETING THIS DB ANYMORE AND JUST QUERY THE REPLICA.
def create_images_db():

    functionstartTime = time.time()
    last_period_time = functionstartTime

    try: os.remove(databases_path + "images.db");
    except: pass;
    conn = sqlite3.connect(databases_path + 'images.db')
    cursor = conn.cursor()

    for languagecode in wikilanguagecodes:
        parameters = []

        try:
            mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()
        except:
            print ('Not created. The '+languages.loc[languagecode]['Wikipedia']+' with code '+languagecode+' is not active (closed or in incubator). Therefore, we cannot obtain the images.')
            continue

        # Create the table and store the data.
        query = ('CREATE TABLE images_'+languagecode+'wiki ('+'page_id integer, image_name text, PRIMARY KEY (page_id,image_name));')
        cursor.execute(query)
        conn.commit()

        mysql_cur_read.execute("SELECT il_from, il_to FROM imagelinks WHERE il_from_namespace = 0")
        rows = mysql_cur_read.fetchall()
        for row in rows: 
            try: parameters.append((row[0],str(row[1].decode('utf-8'))))
            except: continue

        query = 'INSERT OR IGNORE INTO images_'+languagecode+'wiki (page_id,image_name) VALUES (?,?);';
        cursor.executemany(query,parameters)
        conn.commit()
        print ('Images for this language are in: '+languagecode+'\n')

    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))


def wd_all_qitems(cursor):
    cursor.execute("CREATE TABLE qitems (qitem text PRIMARY KEY);")
    mysql_con_read = mdb.connect(host='wikidatawiki.analytics.db.svc.eqiad.wmflabs',db='wikidatawiki_p', read_default_file='./my.cnf', cursorclass=mdb_cursors.SSCursor); mysql_cur_read = mysql_con_read.cursor()
    query = 'SELECT page_title FROM page WHERE page_namespace=0;'
    mysql_cur_read.execute(query)
    while True:
        row = mysql_cur_read.fetchone()
        if row == None: break
        qitem = row[0].decode('utf-8')
        query = "INSERT INTO qitems (qitem) VALUES ('"+qitem+"');"
        cursor.execute(query)
    print ('All Qitems obtained and in wikidata.db.')



# It updates the database with the labels for those items whose language does not have title in sitelink.
def wd_labels_update_db():

    function_name = 'wd_labels_update_db'
    if create_function_account_db(function_name, 'check','')==1: return
    functionstartTime = time.time()

    # Locate the dump
    read_dump = 'latest-all.json.gz' # read_dump = '/public/dumps/public/wikidatawiki/entities/latest-all.json.gz'
    dump_in = gzip.open(dumps_path + read_dump, 'r')
    line = dump_in.readline()
    iter = 0

    conn = sqlite3.connect(databases_path + 'wikidata.db'); cursor = conn.cursor()
    print ('Iterating the dump to update the labels.')
    labels = 0
    while line != '':
        iter += 1
        line = dump_in.readline()
        line = line.rstrip().decode('utf-8')[:-1]

        try:
            entity = json.loads(line)
            qitem = entity['id']
            if not qitem.startswith('Q'): continue
        except:
            print ('JSON error.')
        wd_labels = entity['labels']

        query = 'SELECT langcode FROM sitelinks WHERE qitem ="'+qitem+'"'
        langs = set()
        for row in cursor.execute(query): langs.add(str(row[0]))
        if len(langs)==0: continue

#        print (qitem)
#        print ('these are the languages sitelinks:')
#        print (langs)
#        print ('these are the languages labels:')
#        print (wd_labels)   
        for code, title in wd_labels.items(): # bucle de llengües
            code = code + 'wiki'
            if code in wikilanguagecodeswiki and code not in langs:
                values=[qitem,code,title['value']]
                try: 
                    cursor.execute("INSERT INTO labels (qitem, langcode, label) VALUES (?,?,?)",values)
                    labels+=1
 #                   print ('This is new:')
 #                   print (values)
                except: 
                    pass
#                    print ('This Q and language are already in: ')
 #                  print (values)

        if iter % 500000 == 0:
            conn.commit()

#            print (iter)
            print (100*iter/50000000)
            print ('current number of stored labels: '+str(labels))
            print ('current time: ' + str(time.time() - startTime))
#            break
    conn.commit()
    conn.close()
    print ('DONE with the JSON for the labels iteration.')

    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    create_function_account_db(function_name, 'mark', duration)


# Not useful: done with verify_original_lang_fields(languagecode).
# This function takes the page_titles from the missing articles introduced from other languages and looks for them in the original language to see if they exist.
def update_missing_ccc_interwiki():

    wikilanguagecodes = ['ca']
    function_name = 'update_missing_ccc_interwiki'
    if create_function_account_db(function_name, 'check','')==1: return

    functionstartTime = time.time()
    conn2 = sqlite3.connect(databases_path + missing_ccc_db); cursor2 = conn2.cursor()

    for languagecode in wikilanguagecodes:       

        list_page_ids = set()
        page_ids_qitems = {}
        titles = []
        langs = []

        page_title_qitems = {}
        query = 'SELECT DISTINCT page_title, qitem, languagecode FROM missing_ccc_'+languagecode+'wiki ORDER BY languagecode'

        for row in cursor2.execute(query):
            cur_il_title = row[0]
            if cur_il_title != None: cur_il_title = cur_il_title.replace(' ','_')

            qitem = row[1]
            page_title_qitems[cur_il_title] = qitem

            cur_languagecode = row[2]
            if cur_languagecode != None: 
                cur_languagecode = cur_languagecode.replace('_','-')
            if cur_languagecode == 'be-tarask': cur_languagecode = 'be-x-old'
            if cur_languagecode == 'nan': cur_languagecode = 'zh-min-nan'
            if cur_languagecode != None: 
                cur_languagecode = cur_languagecode + 'wiki'

            titles.append(cur_il_title)
            langs.append(cur_languagecode)

        page_asstring1 = ','.join( ['?'] * len( titles ) )
        page_asstring2 = ','.join( ['?'] * len( langs ) )

        print(len(cur_il_title))

        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()
        query = 'SELECT ll_from, page_title FROM langlinks INNER JOIN page ON ll_from = page_id WHERE il_title IN (%s)' % page_asstring1
        query+= ' AND ll_lang IN (%s);' % page_asstring2

        mysql_cur_read.execute(query)
        rows = mysql_cur_read.fetchall()

        parameters = []
        for row in rows:
            page_id=row[0]
            page_title = row[1].replace('_',' ')
            
            try: qitem = page_title_qitems[page_title]
            except: pass

            parameters.append((page_id,page_title,qitem))
            print((page_id,page_title,qitem))

        input('')
        query = 'UPDATE missing_ccc_'+languagecode+'wiki SET (page_id_original_lang,page_title_original_lang) = (?,?) WHERE qitem = ?;'
        cursor2.executemany(query,parameters)
        conn2.commit()


def traspassing_missing_ccc_db():
    create_wikipedia_missing_ccc_db()


    conn = sqlite3.connect(databases_path + missing_ccc_db); cursor = conn.cursor()
    conn2 = sqlite3.connect(databases_path + 'missing_ccc_copy.db'); cursor2 = conn2.cursor()

    for languagecode in wikilanguagecodes:

        parameters = []
        query = 'SELECT qitem, languagecode, non_language_pairs,page_id, page_title, geocoordinates, iso3166, iso31662, ccc_binary, ccc_geolocated,country_wd, location_wd, created_by_wd, part_of_wd, keyword_title, language_strong_wd, gender, folk, earth, monuments_and_buildings, music_creations_and_organizations, sport_and_teams, food, paintings, glam,books,clothing_and_fashion,industry, num_inlinks, num_outlinks, num_bytes, num_references, num_edits, num_editors, num_discussions, num_pageviews, num_wdproperty, num_interwiki, num_images, featured_article, page_title_original_lang, page_id_original_lang, num_bytes_original_lang, num_references_original_lang, num_editors_original_lang FROM missing_ccc_'+languagecode+'wiki;'

        for row in cursor2.execute(query):
            raw = []
            for r in row:
                if r == None:
                    r = ''
                raw.append(r)

            parameters.append(raw)

        print (languagecode,len(parameters))
        query = 'INSERT OR IGNORE INTO missing_ccc_'+languagecode+'wiki (qitem, languagecode, non_language_pairs,page_id, page_title, geocoordinates, iso3166, iso31662, ccc_binary, ccc_geolocated,country_wd, location_wd, created_by_wd, part_of_wd, keyword_title, language_strong_wd, gender, folk, earth, monuments_and_buildings, music_creations_and_organizations, sport_and_teams, food, paintings, glam,books,clothing_and_fashion,industry, num_inlinks, num_outlinks, num_bytes, num_references, num_edits, num_editors, num_discussions, num_pageviews, num_wdproperty, num_interwiki, num_images, featured_article, page_title_original_lang, page_id_original_lang, num_bytes_original_lang, num_references_original_lang, num_editors_original_lang) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);'

        cursor.executemany(query,parameters)
        conn.commit()


        cursor.execute('SELECT count(*) FROM missing_ccc_'+languagecode+'wiki;')
        print (languagecode,cursor.fetchone()[0])    



# Obtain the Articles with a keyword in title. This is considered potential CCC.
def label_ccc_articles_keywords(languagecode,page_titles_qitems):

    functionstartTime = time.time()
    # function_name = 'label_ccc_articles_keywords '+languagecode
    # if create_function_account_db(function_name, 'check','')==1: return

    # CREATING KEYWORDS DICTIONARY
    keywordsdictionary = {}
    if languagecode not in languageswithoutterritory:
        try: qitems=territories.loc[languagecode]['QitemTerritory'].tolist()
        except: qitems=[];qitems.append(territories.loc[languagecode]['QitemTerritory'])
        for qitem in qitems:
            keywords = []
            # territory in Native language
            territorynameNative = territories.loc[territories['QitemTerritory'] == qitem].loc[languagecode]['territorynameNative']
            # demonym in Native language
            try: 
                demonymsNative = territories.loc[territories['QitemTerritory'] == qitem].loc[languagecode]['demonymNative'].split(';')
                # print (demonymsNative)
                for demonym in demonymsNative:
                    if demonym!='':keywords.append(demonym.strip())
            except: pass
            keywords.append(territorynameNative)
            keywordsdictionary[qitem]=keywords
   
    # language name
    languagenames = languages.loc[languagecode]['nativeLabel'].split(';')
    qitemresult = languages.loc[languagecode]['Qitem']
    keywordsdictionary[qitemresult]=languagenames
#    print (keywordsdictionary)

    
    # We tried to use the Sqlite3 database but we cannot do collate to make non-accent queries.
#    print (keywordsdictionary)
    mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode); mysql_cur_read = mysql_con_read.cursor()

    selectedarticles = {}
    for item in keywordsdictionary:
#        print (item)
        for keyword in keywordsdictionary[item]:
            if keyword == '': continue
            keyword = keyword.replace(' ','%')
            query = 'SELECT page_id, page_title FROM page WHERE page_namespace=0 AND page_is_redirect=0 AND CONVERT(page_title USING utf8mb4) COLLATE utf8mb4_general_ci LIKE '+'"%'+keyword+'%"'+' ORDER BY page_id';
           # with this query, we obtain all the combinations for the keyword (no accents). română is romana, Romanați,...

#            query = 'SELECT page_id, page_title FROM page WHERE page_namespace=0 AND page_is_redirect=0 AND  page_title LIKE '+'"%'+keyword+'%"'+' ORDER BY page_id';
            # this is the clean version.
 
            mysql_cur_read.execute(query)
#            print ("Number of Articles found through this word: " + keyword.replace('%',' '));
            result = mysql_cur_read.fetchall()
            if len(result) == 0: 
                pass
                #print (str(len(result))+' ALERT!');
            else:
                pass
#                print (len(result))

            for row in result:
                page_id = str(row[0])
                page_title = str(row[1].decode('utf-8'))

                if page_id not in selectedarticles:
#                    print (keyword+ '\t'+ page_title + '\t' + page_id + ' dins' + '\n')
                    selectedarticles[page_id] = [page_title, item]
                else:
                    if item not in selectedarticles[page_id]: 
                        selectedarticles[page_id].append(item)
                    #if len(selectedarticles[page_id])>2:print (selectedarticles[page_id])

    insertedarticles = []
    for page_id, value in selectedarticles.items():
        page_title = str(value.pop(0))
        keyword_title = str(';'.join(value))
        try: 
            qitem=page_titles_qitems[page_title]
        except: 
            qitem=None
        insertedarticles.append((1,keyword_title,page_title,page_id,qitem))

    # conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()
    # query = 'UPDATE '+languagecode+'wiki SET (ccc_binary,keyword_title,page_title) = (?,?,?) WHERE page_id = ? AND qitem = ?;'
    # cursor.executemany(query,insertedarticles)
    # conn.commit()

    print ('articles with keywords on titles in Wikipedia language '+(languagecode)+' have been inserted.');
    print ('The number of inserted Articles are '+str(len(insertedarticles)))
    # duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    # create_function_account_db(function_name, 'mark', duration)





# Obtain the Articles with a keyword in title. This is considered potential CCC.
def label_missing_ccc_articles_keywords(languagecode,languagecodes_higher):

    function_name = 'label_missing_ccc_articles_keywords '+languagecode
    if create_function_account_db(function_name, 'check','')==1: return

    functionstartTime = time.time()
#    print ('\n* Getting keywords related Articles for language: '+languages.loc[languagecode]['languagename']+' '+languagecode+'.')

    for languagecode_higher in languagecodes_higher:

        (page_titles_qitems, page_titles_page_ids)=wikilanguages_utils.load_dicts_page_ids_qitems(0,languagecode_higher)
        if len(page_titles_qitems)==0: continue


        # CREATING KEYWORDS DICTIONARY 
        try:
            keywordsdictionary = pairs.loc[pairs['wikimedia_higher'] == languagecode_higher].loc[languagecode][['qitem','territoryname_higher']]
            keywordsdictionary = keywordsdictionary.set_index('qitem')
            keywordsdictionary = keywordsdictionary.to_dict()['territoryname_higher']
            for qitem,keyword in keywordsdictionary.items():
                keywordsdictionary[qitem]=[keyword]
        except:
            keywordsdictionary = {}

    #    print (page_title[0].encode('utf-8'))

        # language name
        qitemresult = languages.loc[languagecode]['Qitem']
        words =[]
        conn = sqlite3.connect(databases_path+'wikidata.db'); cursor = conn.cursor();
        query = 'SELECT page_title FROM sitelinks WHERE qitem=? AND langcode=?'

        if ';' in qitemresult:
            for qitem in qitemresult.split(';'):
                cursor.execute(query,(qitem,languagecode_higher+'wiki'))
                page_title = cursor.fetchone()
                if page_title != None: page_title = page_title[0]
                else: page_title = ''
                words.append(page_title)
        else:
            cursor.execute(query,(qitemresult,languagecode_higher+'wiki'))
            page_title = cursor.fetchone()
            if page_title != None: page_title = page_title[0]
            else: page_title = ''
#            page_title = page_title.replace(' language','')
            words.append(page_title)

        keywordsdictionary[qitemresult]=words
        print (keywordsdictionary)

        mysql_con_read = wikilanguages_utils.establish_mysql_connection_read(languagecode_higher); mysql_cur_read = mysql_con_read.cursor()
        selectedarticles = {}
        for item in keywordsdictionary:
    #        print (item)
            for keyword in keywordsdictionary[item]:
                if keyword == '': continue
                keyword = keyword.replace(' ','%')
                query = 'SELECT page_id, page_title FROM page WHERE CONVERT(page_title USING utf8mb4) COLLATE utf8mb4_general_ci LIKE '+'"%'+keyword+'%";'
               # with this query, we obtain all the combinations for the keyword (no accents). română is romana, Romanați,...

    #            query = 'SELECT page_id, page_title FROM page WHERE page_namespace=0 AND page_is_redirect=0 AND  page_title LIKE '+'"%'+keyword+'%"'+' ORDER BY page_id';
                # this is the clean version.
     
                mysql_cur_read.execute(query)
    #            print ("Number of Articles found through this word: " + keyword.replace('%',' '));
                result = mysql_cur_read.fetchall()
                if len(result) == 0: 
    #                print (str(len(result))+' ALERT!');
                    pass
                else: 
                    pass
                    #print (len(result))

                for row in result:
                    page_id = str(row[0])
                    page_title = str(row[1].decode('utf-8'))

                    try: qitem = page_titles_qitems[page_title]
                    except: continue

                    try:
    #                    print (keyword+ '\t'+ page_title + '\t' + page_id + ' dins' + '\n')
                        selectedarticles[page_id] = [page_title, item]
                    except:
                        try:
                            selectedarticles[page_id].index(item)
                        except:
                            selectedarticles[page_id].append(item)
                            #if len(selectedarticles[page_id])>2:print (selectedarticles[page_id])

        print ('The total number of Articles by this language dictionary is: ')
        print (len(selectedarticles))


        insertedarticles = []
        for page_id, value in selectedarticles.items():
            page_title = str(value.pop(0))
            keyword_title = str(';'.join(value))
            try: 
                qitem=page_titles_qitems[page_title]
            except: 
                qitem=None
            insertedarticles.append((languagecode_higher,1,keyword_title,page_title,page_id,qitem))

        conn = sqlite3.connect(databases_path + missing_ccc_db); cursor = conn.cursor()

        query = 'INSERT OR IGNORE INTO missing_ccc_'+languagecode+'wiki (languagecode,ccc_binary,keyword_title,page_title,page_id,qitem) VALUES (?,?,?,?,?,?);'
        cursor.executemany(query,insertedarticles)
        conn.commit()

    print ('articles with keywords on titles in Wikipedia language '+(languagecode)+' have been inserted.');

    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    create_function_account_db(function_name, 'mark', duration)


def generate_ccc_ccc_intersections():
    time_range = 'last accumulated'
    function_name = 'generate_ccc_ccc_intersections '+time_range
    if create_function_account_db(function_name, 'check','')==1: return

    functionstartTime = time.time()
    period = cycle_year_month

    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()
    conn2 = sqlite3.connect(databases_path + stats_db); cursor2 = conn2.cursor()

    # between languages ccc
    for languagecode_1 in wikilanguagecodes:
        print (languagecode_1 +'\t'+ str(datetime.timedelta(seconds=time.time() - functionstartTime)))
        query = 'SELECT COUNT(ccc_binary) FROM '+languagecode_1+'wiki WHERE ccc_binary=1'
        cursor.execute(query)
        language_ccc_count = cursor.fetchone()[0]
        if language_ccc_count == 0: continue

        for languagecode_2 in wikilanguagecodes:
            if languagecode_1 == languagecode_2: continue

            query = 'SELECT COUNT (*) FROM '+languagecode_2+'wiki INNER JOIN ccc_'+languagecode_1+'wiki ON ccc_'+languagecode_1+'wiki.qitem = ccc_'+languagecode_2+'wiki.qitem WHERE ccc_'+languagecode_2+'wiki.ccc_binary = 1 AND ccc_'+languagecode_1+'wiki.ccc_binary = 1;'
            cursor.execute(query)
            row = cursor.fetchone()
            ccc_coincident_articles_count = row[0]

            insert_intersections_values(time_range,cursor2,'articles',languagecode_1,'ccc',languagecode_2,'ccc',ccc_coincident_articles_count,language_ccc_count,period)

    conn2.commit()
    print ('languagecode_1, ccc, languagecode_2, ccc,'+ period)

    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    create_function_account_db(function_name, 'mark', duration)



# OUTDATED
def copy_db_to_another():

    print ('coyping wikipedia_diversity to another .db')

    functionstartTime = time.time()

    conn = sqlite3.connect(databases_path + 'wikipedia_diversity_backup.db'); cursor = conn.cursor()
    conn2 = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor2 = conn2.cursor()

    for languagecode in wikilanguagecodes:
        print (languagecode)

        # RETRIEVING
        query = ('SELECT '+
            # general
        'qitem, '+
        'page_id, '+
        'page_title, '+
        'date_created, '+
        'geocoordinates, '+
        'iso3166, '+
        'iso31662, '+

        # calculations:
#        'ccc_binary, '+
#        'main_territory, '+
#        'num_retrieval_strategies, '+ # this is a number

        # set as CCC
        'ccc_geolocated,'+ # 1, -1 o null.
#        'country_wd, '+ # 'P1:Q1;P2:Q2;P3:Q3'
        'location_wd, '+ # 'P1:QX1:Q; P2:QX2:Q' Q is the main territory
        'language_strong_wd, '+ # 'P1:Q1;P2:Q2;P3:Q3'
#        'created_by_wd, '+ # 'P1:Q1;P2:Q2;P3:Q3'
#        'part_of_wd, '+ # 'P1:Q1;P2:Q2;P3:Q3'
        'keyword_title, '+ # 'QX1;QX2'

        # retrieved as potential CCC:
        'category_crawling_territories, '+ # 'QX1;QX2'
        'category_crawling_level, '+ # 'level'
#        'language_weak_wd, '+ # 'P1:Q1;P2:Q2;P3:Q3'
#        'affiliation_wd, '+ # 'P1:Q1;P2:Q2;P3:Q3'
#        'has_part_wd, '+ # 'P1:Q1;P2:Q2;P3:Q3'
        'num_inlinks_from_CCC, '+
        'num_outlinks_to_CCC, '+
        'percent_inlinks_from_CCC, '+
        'percent_outlinks_to_CCC, '+

        # retrieved as potential other CCC (part of other CCC)
        # from wikidata properties
#        'other_ccc_country_wd, '+
#        'other_ccc_location_wd, '+
#        'other_ccc_language_strong_wd, '+
#        'other_ccc_created_by_wd, '+
#        'other_ccc_part_of_wd, '+
#        'other_ccc_language_weak_wd, '+
#        'other_ccc_affiliation_wd, '+
#        'other_ccc_has_part_wd, '+
        # from other wikipedia ccc database.
#        'other_ccc_keyword_title, '+
#        'other_ccc_category_crawling_relative_level, '+
        # from links to/from non-ccc geolocated Articles.
#        'num_inlinks_from_geolocated_abroad, '+
#        'num_outlinks_to_geolocated_abroad, '+
#        'percent_inlinks_from_geolocated_abroad, '+
#        'percent_outlinks_to_geolocated_abroad, '+

        # characteristics of rellevance
        'num_inlinks, '+
        'num_outlinks, '+
        'num_bytes, '+
        'num_references, '+
        'num_edits, '+
        'num_editors, '+
        'num_discussions, '+
        'num_pageviews, '+
        'num_wdproperty, '+
        'num_interwiki, '+
        'featured_article '+

        'FROM '+languagecode+'wiki;')

#        print (query)
        parameters = []

        for row in cursor.execute(query):
            parameters.append(tuple(row))

        # INSERTING
        page_asstring = ','.join( ['?'] * (query.count(',')+1)) 
        query = ('INSERT INTO '+languagecode+'wiki ('+
            # general
        'qitem, '+
        'page_id, '+
        'page_title, '+
        'date_created, '+
        'geocoordinates, '+
        'iso3166, '+
        'iso31662, '+

        # calculations:
#        'ccc_binary, '+
#        'main_territory, '+
#        'num_retrieval_strategies, '+ # this is a number

        # set as CCC
        'ccc_geolocated,'+ # 1, -1 o null.
#        'country_wd, '+ # 'P1:Q1;P2:Q2;P3:Q3'
        'location_wd, '+ # 'P1:QX1:Q; P2:QX2:Q' Q is the main territory
        'language_strong_wd, '+ # 'P1:Q1;P2:Q2;P3:Q3'
#        'created_by_wd, '+ # 'P1:Q1;P2:Q2;P3:Q3'
#        'part_of_wd, '+ # 'P1:Q1;P2:Q2;P3:Q3'
        'keyword_title, '+ # 'QX1;QX2'

        # retrieved as potential CCC:
        'category_crawling_territories, '+ # 'QX1;QX2'
        'category_crawling_level, '+ # 'level'
#        'language_weak_wd, '+ # 'P1:Q1;P2:Q2;P3:Q3'
#        'affiliation_wd, '+ # 'P1:Q1;P2:Q2;P3:Q3'
#        'has_part_wd, '+ # 'P1:Q1;P2:Q2;P3:Q3'
        'num_inlinks_from_CCC, '+
        'num_outlinks_to_CCC, '+
        'percent_inlinks_from_CCC, '+
        'percent_outlinks_to_CCC, '+

        # retrieved as potential other CCC (part of other CCC)
        # from wikidata properties
#        'other_ccc_country_wd, '+
#        'other_ccc_location_wd, '+
#        'other_ccc_language_strong_wd, '+
#        'other_ccc_created_by_wd, '+
#        'other_ccc_part_of_wd, '+
#        'other_ccc_language_weak_wd, '+
#        'other_ccc_affiliation_wd, '+
#        'other_ccc_has_part_wd, '+
        # from other wikipedia ccc database.
#        'other_ccc_keyword_title, '+
#        'other_ccc_category_crawling_relative_level, '+
        # from links to/from non-ccc geolocated Articles.
#        'num_inlinks_from_geolocated_abroad, '+
#        'num_outlinks_to_geolocated_abroad, '+
#        'percent_inlinks_from_geolocated_abroad, '+
#        'percent_outlinks_to_geolocated_abroad, '+

        # characteristics of rellevance
        'num_inlinks, '+
        'num_outlinks, '+
        'num_bytes, '+
        'num_references, '+
        'num_edits, '+
        'num_editors, '+
        'num_discussions, '+
        'num_pageviews, '+
        'num_wdproperty, '+
        'num_interwiki, '+
        'featured_article '+
        ') '+

        'VALUES ('+
        page_asstring+
        ');')

        cursor2.executemany(query,parameters)
        conn2.commit()


def copy_db2_to_another():

    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()

    conn2 = sqlite3.connect(databases_path + 'wikipedia_diversity_.db'); cursor2 = conn2.cursor()

    for languagecode in wikilanguagecodes[wikilanguagecodes.index('vo')+1:]:

        if languagecode in ('ban','nqo','mnw'): continue

        params = []
        query = 'SELECT qitem, page_id, page_title, date_created, geocoordinates, iso3166, iso31662, region, ccc_binary, ccc_binary_last_cycle, main_territory, num_retrieval_strategies, ccc_geolocated,country_wd, location_wd, language_strong_wd, created_by_wd, part_of_wd, keyword_title, category_crawling_territories, category_crawling_level, language_weak_wd, affiliation_wd, has_part_wd, num_inlinks_from_CCC, num_outlinks_to_CCC, percent_inlinks_from_CCC, percent_outlinks_to_CCC, other_ccc_country_wd, other_ccc_location_wd, other_ccc_language_strong_wd, other_ccc_created_by_wd, other_ccc_part_of_wd, other_ccc_language_weak_wd, other_ccc_affiliation_wd, other_ccc_has_part_wd, other_ccc_keyword_title, other_ccc_category_crawling_relative_level, num_inlinks_from_geolocated_abroad, num_outlinks_to_geolocated_abroad, percent_inlinks_from_geolocated_abroad, percent_outlinks_to_geolocated_abroad, num_inlinks, num_outlinks, num_bytes, num_references, num_edits, num_editors, num_discussions, num_pageviews, num_wdproperty, num_interwiki, num_images, num_edits_last_month,featured_article, wikirank, first_timestamp_lang,folk, earth, monuments_and_buildings, music_creations_and_organizations, sport_and_teams, food, paintings, glam,books,clothing_and_fashion,industry, gender, sexual_orientation, religion, race_and_ethnia, time FROM '+languagecode+'wiki;'


        for row in cursor2.execute(query):
            # for r in row:
            #     a = 

            params.append(row)


        query = 'INSERT OR IGNORE INTO '+languagecode+'wiki (qitem, page_id, page_title, date_created, geocoordinates, iso3166, iso31662, region, ccc_binary, ccc_binary_last_cycle, main_territory, num_retrieval_strategies, ccc_geolocated,country_wd, location_wd, language_strong_wd, created_by_wd, part_of_wd, keyword_title, category_crawling_territories, category_crawling_level, language_weak_wd, affiliation_wd, has_part_wd, num_inlinks_from_CCC, num_outlinks_to_CCC, percent_inlinks_from_CCC, percent_outlinks_to_CCC, other_ccc_country_wd, other_ccc_location_wd, other_ccc_language_strong_wd, other_ccc_created_by_wd, other_ccc_part_of_wd, other_ccc_language_weak_wd, other_ccc_affiliation_wd, other_ccc_has_part_wd, other_ccc_keyword_title, other_ccc_category_crawling_relative_level, num_inlinks_from_geolocated_abroad, num_outlinks_to_geolocated_abroad, percent_inlinks_from_geolocated_abroad, percent_outlinks_to_geolocated_abroad, num_inlinks, num_outlinks, num_bytes, num_references, num_edits, num_editors, num_discussions, num_pageviews, num_wdproperty, num_interwiki, num_images, num_edits_last_month,featured_article, wikirank, first_timestamp_lang,folk, earth, monuments_and_buildings, music_creations_and_organizations, sport_and_teams, food, paintings, glam,books,clothing_and_fashion,industry, gender, sexual_orientation, religion, race_and_ethnia, time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);'

        cursor.executemany(query,params)
        conn.commit()
        print (languagecode)


def get_new_cycle_year_month():

    # try:
    #     pathf = databases_path+'wikidata.db'
    #     current_cycle_date = time.strftime('%Y%m%d%H%M%S', time.gmtime(os.path.getmtime(pathf)))
    #     current_cycle_date = datetime.datetime.strptime(current_cycle_date,'%Y%m%d%H%M%S')-dateutil.relativedelta.relativedelta(months=1)
    #     current_cycle = current_cycle_date.strftime('%Y-%m')
    #     print ('wikidata.db exists.')

    pathf = '/public/dumps/public/wikidatawiki/entities/latest-all.json.gz'
    current_cycle_date = time.strftime('%Y%m%d%H%M%S', time.gmtime(os.path.getmtime(pathf)))
    current_cycle_date = datetime.datetime.strptime(current_cycle_date,'%Y%m%d%H%M%S')-dateutil.relativedelta.relativedelta(months=1)
    current_cycle = current_cycle_date.strftime('%Y-%m')

    print (current_cycle)
    return current_cycle


def get_current_cycle_year_month():
    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()
    query = 'SELECT MAX(date_created) FROM enwiki;'
    cursor.execute(query)
    timestamp = cursor.fetchone()[0]
    current_cycle = datetime.datetime.strptime(str(timestamp),'%Y%m%d%H%M%S').date()

    current_cycle_date = current_cycle-dateutil.relativedelta.relativedelta(months=1)
    current_cycle = current_cycle_date.strftime('%Y-%m')

    print (current_cycle)
    return current_cycle



def delete_last_iteration_top_diversity_articles_lists():
    conn = sqlite3.connect(databases_path + top_diversity_db); cursor = conn.cursor()

    print ('Deleting all the rest from the last iteration.')
    for languagecode in wikilanguagecodes:
        print (languagecode)

        query = 'SELECT count(DISTINCT measurement_date) FROM '+languagecode+'wiki_top_articles_features'
        cursor.execute(query)
        if cursor.fetchone()[0] > 1:
            query = 'DELETE FROM '+languagecode+'wiki_top_articles_features WHERE measurement_date IN (SELECT MIN(measurement_date) FROM '+languagecode+'wiki_top_articles_features)'
            cursor.execute(query); conn.commit()
        else: print ('only one measurement_date in wiki_top_articles_features')

        query = 'SELECT count(DISTINCT measurement_date) FROM '+languagecode+'wiki_top_articles_lists'
        cursor.execute(query)
        if cursor.fetchone()[0] > 1:
            query = 'DELETE FROM '+languagecode+'wiki_top_articles_lists WHERE measurement_date IN (SELECT MIN(measurement_date) FROM '+languagecode+'wiki_top_articles_lists)'
            cursor.execute(query); conn.commit()
        else: print ('only one measurement_date in wiki_top_articles_lists')


    query = 'SELECT count(DISTINCT measurement_date) FROM wdo_intersections'
    cursor.execute(query)
    if cursor.fetchone()[0] > 1:
        query = 'DELETE FROM wdo_intersections WHERE measurement_date IN (SELECT MIN(measurement_date) FROM wdo_intersections)'
        cursor.execute(query); conn.commit()
    else: print ('only one measurement_date in wdo_intersections')




def generate_top_ccc_articles_lists_intersections():
    time_range = 'last accumulated'
    function_name = 'generate_top_ccc_articles_lists_intersections '+time_range
    if wikilanguages_utils.verify_function_run(cycle_year_month, script_name, function_name, 'check','')==1: return

    functionstartTime = time.time()
    period = cycle_year_month

    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()
    conn2 = sqlite3.connect(databases_path + stats_db); cursor2 = conn2.cursor()
    conn4 = sqlite3.connect(databases_path + top_diversity_db); cursor4 = conn4.cursor()

    all_articles = {}
    for languagecode_1 in wikilanguagecodes:
        qitems = set()
        query = 'SELECT qitem FROM '+languagecode_1+'wiki'
        for row in cursor.execute(query): qitems.add(row[0])
        all_articles[languagecode_1]=qitems
    print ('all loaded.')


    # PERHAPS: THIS SHOULD BE LIMITED TO 100 ARTICLES PER LIST.
    # CCC TOP ARTICLES LISTS
    lists = ['editors', 'featured', 'geolocated', 'keywords', 'women', 'men', 'created_first_three_years', 'created_last_year', 'pageviews', 'discussions','edits','edited_last_month','images','wdproperty_many','interwiki_many','interwiki_editors','interwiki_wdproperty','wikirank','earth','monuments_and_buildings','sport_and_teams','glam','folk','music_creations_and_organizations','food','paintings','books','clothing_and_fashion','industry','religion','ethnic_groups','religious_groups','lgtb']

    for languagecode in wikilanguagecodes:
        print (languagecode +'\t'+ str(datetime.timedelta(seconds=time.time() - functionstartTime)))
        wpnumberofarticles=wikipedialanguage_currentnumberarticles[languagecode]
        all_top_ccc_articles_count = 0
        all_top_ccc_articles_coincident_count = 0

        all_ccc_lists_items=set()
        for list_name in lists:
            lists_qitems = set()

            for languagecode_2 in wikilanguagecodes:
#                query = 'SELECT qitem FROM '+languagecode_2+'wiki_top_articles_lists WHERE list_name ="'+list_name+'" AND measurement_date IS (SELECT MAX(measurement_date) FROM '+languagecode_2+'wiki_top_articles_lists);'

                query = 'SELECT qitem FROM '+languagecode_2+'wiki_top_articles_lists WHERE list_name ="'+list_name+'"'#+'" AND measurement_date IS (SELECT MAX(measurement_date) FROM ccc_'+languagecode_2+'wiki_top_articles_lists);'
                for row in cursor4.execute(query):
                    all_ccc_lists_items.add(row[0])
                    lists_qitems.add(row[0])

            all_top_ccc_articles_count+=len(lists_qitems)
            ccc_list_coincident_count=len(lists_qitems.intersection(all_articles[languagecode]))

            insert_intersections_values(time_range,cursor2,'articles','top_ccc_articles_lists',list_name,languagecode,'wp',ccc_list_coincident_count,len(lists_qitems), period)

            insert_intersections_values(time_range,cursor2,'articles',languagecode,'wp','top_ccc_articles_lists',list_name,ccc_list_coincident_count,wpnumberofarticles, period)


        #  CCC Top articles lists - sum spread and sum coverage
        for languagecode_2 in wikilanguagecodes:
            qitems_unique = set()
            country = ''
#                query = 'SELECT qitem, country FROM '+languagecode_2+'wiki_top_articles_lists WHERE measurement_date IS (SELECT MAX(measurement_date) FROM '+languagecode_2+'wiki_top_articles_lists) AND position <= 100 ORDER BY country'

            query = 'SELECT qitem, country FROM '+languagecode_2+'wiki_top_articles_lists WHERE position <= 100 ORDER BY country'# AND measurement_date IS (SELECT MAX(measurement_date) FROM ccc_'+languagecode_2+'wiki_top_articles_lists)'
            for row in cursor4.execute(query):
                cur_country = row[1]

                if cur_country != country and country != '':
                    list_origin = ''
                    if country != 'all': list_origin = country+'_('+languagecode_2+')'
                    else: list_origin = languagecode_2

                    coincident_qitems_all_qitems = len(qitems_unique.intersection(all_articles[languagecode]))
                    insert_intersections_values(time_range,cursor2,'articles',list_origin,'all_top_ccc_articles',languagecode,'wp',coincident_qitems_all_qitems,len(qitems_unique), period)
                    qitems_unique = set()

                qitems_unique.add(row[0])
                country = cur_country

            # last iteration
            if country != 'all': list_origin = country+'_('+languagecode_2+')'
            else: list_origin = languagecode_2

            coincident_qitems_all_qitems = len(qitems_unique.intersection(all_articles[languagecode]))
            insert_intersections_values(time_range,cursor2,'articles',list_origin,'all_top_ccc_articles',languagecode,'wp',coincident_qitems_all_qitems,len(qitems_unique), period)

        # all CCC Top articles lists
        all_top_ccc_articles_coincident_count = len(all_ccc_lists_items.intersection(all_articles[languagecode]))
        insert_intersections_values(time_range,cursor2,'articles','ccc','all_top_ccc_articles',languagecode,'wp',all_top_ccc_articles_coincident_count,all_top_ccc_articles_count, period)

        insert_intersections_values(time_range,cursor2,'articles',languagecode,'wp','ccc','all_top_ccc_articles',all_top_ccc_articles_coincident_count,wpnumberofarticles, period)

    conn2.commit()
    print ('top_ccc_articles_lists, list_name, languagecode, wp,'+ period)
    print ('wp, languagecode, top_ccc_articles_lists, list_name,'+ period)

    print ('list_origin, all_top_ccc_articles, languagecode, wp,'+ period)

    print ('ccc, all_top_ccc_articles, languagecode, wp,'+ period)
    print ('languagecode, wp, ccc, all_top_ccc_articles,'+ period)



    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    wikilanguages_utils.verify_function_run(cycle_year_month, script_name, function_name, 'mark', duration)



def generate_top_diversity_articles_lists_intersections():

    def insert_intersections_values(cursor3, set1, set1descriptor, set2, set2descriptor, abs_value, base, period):

        if abs_value == None: abs_value = 0

        if base == None or base == 0: rel_value = 0
        else: rel_value = 100*abs_value/base

        if 'avg' in set1 or 'avg' in set2: rel_value = base # exception for calculations in generate_langs_ccc_intersections()

        if rel_value != 0.0 or abs_value != 0:
            query_insert = 'INSERT OR IGNORE INTO wdo_intersections'+' (abs_value, rel_value, set1, set1descriptor, set2, set2descriptor, measurement_date) VALUES (?,?,?,?,?,?,?)'

            values = (abs_value, rel_value, set1, set1descriptor, set2, set2descriptor, period)
            cursor3.execute(query_insert,values);

            query_update = 'UPDATE wdo_intersections'+' SET abs_value = ?, rel_value = ? WHERE set1 = ? AND set1descriptor = ? AND set2 = ? AND set2descriptor = ? AND measurement_date = ?'
            cursor3.execute(query_update,values);
            # print(values)


    functionstartTime = time.time()
    period = measurement_date

    conn4 = sqlite3.connect(databases_path + top_diversity_db); cursor4 = conn4.cursor()
    conn3 = sqlite3.connect(databases_path + top_diversity_db); cursor3 = conn4.cursor()

    all_articles = {}
    for languagecode_1 in wikilanguagecodes:
        qitems = set()
        query = 'SELECT qitem FROM '+languagecode_1+'wiki_top_articles_page_titles WHERE generation_method = "sitelinks";'
        for row in cursor4.execute(query): qitems.add(row[0])
        all_articles[languagecode_1]=qitems
        print (languagecode_1,len(qitems))
    print ('all loaded.')


    # PERHAPS: THIS SHOULD BE LIMITED TO 100 ARTICLES PER LIST.
    # CCC TOP ARTICLES LISTS
    lists = ['editors', 'featured', 'geolocated', 'keywords', 'women', 'men', 'created_first_three_years', 'created_last_year', 'pageviews', 'discussions','edits','edited_last_month','images','wdproperty_many','interwiki_many','interwiki_editors','interwiki_wdproperty','wikirank','earth','monuments_and_buildings','sport_and_teams','glam','folk','music_creations_and_organizations','food','paintings','books','clothing_and_fashion','industry']

    for languagecode in wikilanguagecodes:
        print (languagecode +'\t'+ str(datetime.timedelta(seconds=time.time() - functionstartTime)))
        wpnumberofarticles=wikipedialanguage_currentnumberarticles[languagecode]
        all_top_diversity_articles_count = 0
        all_top_diversity_articles_coincident_count = 0

        all_ccc_lists_items=set()
        for list_name in lists:
            lists_qitems = set()

            for languagecode_2 in wikilanguagecodes:
                query = 'SELECT qitem FROM '+languagecode_2+'wiki_top_articles_lists WHERE list_name ="'+list_name+'"'# measurement_date IS (SELECT MAX(measurement_date) FROM '+languagecode_2+'wiki_top_articles_lists);'

                # query = 'SELECT qitem FROM ccc_'+languagecode_2+'wiki_top_articles_lists WHERE list_name ="'+list_name+'" AND measurement_date IS (SELECT MAX(measurement_date) FROM ccc_'+languagecode_2+'wiki_top_articles_lists);'

                for row in cursor4.execute(query):
                    all_ccc_lists_items.add(row[0])
                    lists_qitems.add(row[0])

            all_top_diversity_articles_count+=len(lists_qitems)
            ccc_list_coincident_count=len(lists_qitems.intersection(all_articles[languagecode]))

            insert_intersections_values(cursor3,'top_diversity_articles_lists',list_name,'wp',languagecode,ccc_list_coincident_count,len(lists_qitems), period)

            insert_intersections_values(cursor3,languagecode,'wp','top_diversity_articles_lists',list_name,ccc_list_coincident_count,wpnumberofarticles, period)

        lang_art = all_articles[languagecode]



        #  All articles from a specific lang/country - sum spread and sum coverage
        for languagecode_2 in wikilanguagecodes:
            qitems_unique = set()
            country = ''
#                query = 'SELECT qitem, country FROM '+languagecode_2+'wiki_top_articles_lists WHERE measurement_date IS (SELECT MAX(measurement_date) FROM '+languagecode_2+'wiki_top_articles_lists) AND position <= 100 ORDER BY country'
            query = 'SELECT qitem, country FROM '+languagecode_2+'wiki_top_articles_lists WHERE position <= 100 ORDER BY country'# measurement_date IS (SELECT MAX(measurement_date) FROM 

            # print (query)
            # SELECT qitem, country FROM cawiki_top_articles_lists WHERE position <= 100 ORDER BY country
            for row in cursor4.execute(query):
                cur_country = str(row[1])

                if cur_country != country and country != '':
                    coincident_qitems_all_qitems = len(qitems_unique.intersection(lang_art))
                    list_origin = ''
                    if country != 'all': 
                        list_origin = country+'_('+languagecode_2+')'
                    else: 
                        list_origin = languagecode_2

                    insert_intersections_values(cursor3,list_origin,'all_top_diversity_articles',languagecode,'wp',coincident_qitems_all_qitems,len(qitems_unique), period)
                    qitems_unique = set()

                qitems_unique.add(row[0])
                country = cur_country

            # last iteration
            if country != 'all' and country != '': 
                list_origin = country+'_('+languagecode_2+')'
            else: 
                list_origin = languagecode_2

            coincident_qitems_all_qitems = len(qitems_unique.intersection(lang_art))
            insert_intersections_values(cursor3,list_origin,'all_top_diversity_articles',languagecode,'wp',coincident_qitems_all_qitems,len(qitems_unique), period)

        # All Top articles lists
        all_top_diversity_articles_coincident_count = len(all_ccc_lists_items.intersection(lang_art))
        insert_intersections_values(cursor3,'ccc','all_top_diversity_articles',languagecode,'wp',all_top_diversity_articles_coincident_count,all_top_diversity_articles_count, period)

        insert_intersections_values(cursor3,languagecode,'wp','ccc','all_top_diversity_articles',all_top_diversity_articles_coincident_count,wpnumberofarticles, period)

        conn4.commit()

    print ('top_diversity_articles_lists, list_name, wp, languagecode,'+ period)
    print ('wp, languagecode, top_diversity_articles_lists, list_name,'+ period)

    print ('list_origin, all_top_diversity_articles, languagecode, wp,'+ period)

    print ('ccc, all_top_diversity_articles, languagecode, wp,'+ period)
    print ('languagecode, wp, ccc, all_top_diversity_articles,'+ period)

    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    wikilanguages_utils.verify_function_run(cycle_year_month, script_name, function_name, 'mark', duration)


# current dataset period
# cursor.execute('SELECT MAX(year_month) FROM function_account;'); current_dataset_period_top_diversity=cursor.fetchone()[0]
conn2 = sqlite3.connect(databases_path + 'stats_production.db'); cursor2 = conn2.cursor() 
cursor2.execute('SELECT MAX(period) FROM wcdo_intersections_accumulated;'); current_dataset_period_stats=cursor2.fetchone()[0]
current_dataset_period_stats = '2019-05'
# conn3 = sqlite3.connect(databases_path + 'missing_ccc_production.db'); cursor3 = conn3.cursor() 
# cursor3.execute('SELECT MAX(year_month) FROM function_account;'); current_dataset_period_missing_ccc=cursor3.fetchone()[0]


##### ##### ##### ##### #####





def update_language_country_all_top_diversity_articles_intersections():

    def insert_intersections_values(cursor3, set1, set1descriptor, set2, set2descriptor, abs_value, base, period):

        if abs_value == None: abs_value = 0

        if base == None or base == 0: rel_value = 0
        else: rel_value = 100*abs_value/base

        if 'avg' in set1 or 'avg' in set2: rel_value = base # exception for calculations in generate_langs_ccc_intersections()

        if rel_value != 0.0 or abs_value != 0:
            query_insert = 'INSERT OR IGNORE INTO wcdo_intersections'+' (abs_value, rel_value, set1, set1descriptor, set2, set2descriptor, measurement_date) VALUES (?,?,?,?,?,?,?)'

            values = (abs_value, rel_value, set1, set1descriptor, set2, set2descriptor, period)
            cursor3.execute(query_insert,values);

            query_update = 'UPDATE wcdo_intersections'+' SET abs_value = ?, rel_value = ? WHERE set1 = ? AND set1descriptor = ? AND set2 = ? AND set2descriptor = ? AND measurement_date = ?'
            cursor3.execute(query_update,values);
            # print(values)


    functionstartTime = time.time()
    period = measurement_date

    conn4 = sqlite3.connect(databases_path + top_diversity_db); cursor4 = conn4.cursor()
    conn3 = sqlite3.connect(databases_path + top_diversity_db); cursor3 = conn4.cursor()

    all_articles = {}
    for languagecode_1 in wikilanguagecodes:
        qitems = set()
        query = 'SELECT qitem FROM '+languagecode_1+'wiki_top_articles_page_titles WHERE generation_method = "sitelinks";'
        for row in cursor4.execute(query): qitems.add(row[0])
        all_articles[languagecode_1]=qitems
        print (languagecode_1,len(qitems))
    print ('all loaded.')

    # CCC TOP ARTICLES LISTS
    lists = ['editors', 'featured', 'geolocated', 'keywords', 'women', 'men', 'created_first_three_years', 'created_last_year', 'pageviews', 'discussions','edits','edited_last_month','images','wdproperty_many','interwiki_many','interwiki_editors','interwiki_wdproperty','wikirank','earth','monuments_and_buildings','sport_and_teams','glam','folk','music_creations_and_organizations','food','paintings','books','clothing_and_fashion','industry']

    for languagecode in wikilanguagecodes:
        print (languagecode +'\t'+ str(datetime.timedelta(seconds=time.time() - functionstartTime)))

        lang_art = all_articles[languagecode]

        #  All articles from a specific lang/country - sum spread and sum coverage
        for languagecode_2 in wikilanguagecodes:
            qitems_unique = set()
            country = ''
#                query = 'SELECT qitem, country FROM '+languagecode_2+'wiki_top_articles_lists WHERE measurement_date IS (SELECT MAX(measurement_date) FROM '+languagecode_2+'wiki_top_articles_lists) AND position <= 100 ORDER BY country'
            query = 'SELECT qitem, country FROM '+languagecode_2+'wiki_top_articles_lists WHERE position <= 100 ORDER BY country'# measurement_date IS (SELECT MAX(measurement_date) FROM 

            # print (query)
            # SELECT qitem, country FROM cawiki_top_articles_lists WHERE position <= 100 ORDER BY country
            for row in cursor4.execute(query):
                cur_country = str(row[1])

                if cur_country != country and country != '':
                    coincident_qitems_all_qitems = len(qitems_unique.intersection(lang_art))
                    list_origin = ''
                    if country != 'all': 
                        list_origin = country+'_('+languagecode_2+')'
                    else: 
                        list_origin = languagecode_2

                    insert_intersections_values(cursor3,list_origin,'all_top_ccc_articles',languagecode,'wp',coincident_qitems_all_qitems,len(qitems_unique), period)
                    qitems_unique = set()

                qitems_unique.add(row[0])
                country = cur_country

            # last iteration
            if country != 'all' and country != '': 
                list_origin = country+'_('+languagecode_2+')'
            else: 
                list_origin = languagecode_2

            coincident_qitems_all_qitems = len(qitems_unique.intersection(lang_art))
            insert_intersections_values(cursor3,list_origin,'all_top_ccc_articles',languagecode,'wp',coincident_qitems_all_qitems,len(qitems_unique), period)

        conn4.commit()

    # print ('list_origin, all_top_diversity_articles, languagecode, wp,'+ period)
    # duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))
    # wikilanguages_utils.verify_function_run(cycle_year_month, script_name, function_name, 'mark', duration)


def count_number_qitems_per_list():
    # COUNT THE NUMBER OF QITEMS PER LIST
    conn = sqlite3.connect(databases_path + top_diversity_db); cursor = conn.cursor()
    lists=['geolocated', 'keywords', 'women', 'men']  

    list_count_100_wp = {}
    list_count_100 = {}
    for list_name in lists:
        for languagecode in wikilanguagecodes:
            query = 'SELECT count(*) FROM ccc_'+languagecode+'wiki_top_articles_lists WHERE list_name ="'+list_name+'" AND measurement_date;'


            cursor.execute(query)
            num_list = int(cursor.fetchone()[0])
            if num_list < 100:
                list_count_100_wp[languages.loc[languagecode]['languagename']]=wikipedialanguage_currentnumberarticles[languagecode]
                list_count_100[languages.loc[languagecode]['languagename']]=num_list

        print (list_name,len(list_count_100))

        print (sorted( ((v,k) for k,v in list_count_100_wp.items()), reverse=True))
        print (sorted( ((v,k) for k,v in list_count_100.items()), reverse=True))



# the transposition is not necessary.
# df_topics1 = pd.pivot_table(df_topics,values=['rel_value','abs_value'], index=['set1'],columns=['set2descriptor'])
# df_topics1.columns = ['{}_{}'.format(x[1], x[0]) for x in df_topics1.columns]
# df_topics1 = df_topics1.rename(columns = {})
# prova = {'books_abs_value', 'clothing_and_fashion_abs_value', 'earth_abs_value', 'folk_abs_value', 'food_abs_value', 'glam_abs_value', 'industry_abs_value', 'monuments_and_buildings_abs_value', 'music_creations_and_organizations_abs_value', 'paintings_abs_value', 'sport_and_teams_abs_value', 'books_rel_value', 'clothing_and_fashion_rel_value', 'earth_rel_value', 'folk_rel_value', 'food_rel_value', 'glam_rel_value', 'industry_rel_value', 'monuments_and_buildings_rel_value', 'music_creations_and_organizations_rel_value', 'paintings_rel_value', 'sport_and_teams_rel_value'}













# # 2 hours to get all the qitems
def wd_all_qitems(cursor):

    function_name = 'wd_all_qitems'
    print (function_name)

    functionstartTime = time.time()

    cursor.execute("CREATE TABLE qitems (qitem text PRIMARY KEY);")
    dumps_path = '/public/dumps/public/wikidatawiki/latest/wikidatawiki-latest-page.sql.gz'
    dump_in = gzip.open(dumps_path, 'r')

    query = "INSERT INTO qitems (qitem) VALUES (?);"

    qitems_list = list()
    qitems = {}
    iter = 0
    while True:
        line = dump_in.readline()
        try: line = line.decode("utf-8")
        except UnicodeDecodeError: line = str(line)

        if line == '':
            i+=1
            if i==3: break
        else: i=0

        iter+=1
#        print (iter)
        if wikilanguages_utils.is_insert(line):
            values = wikilanguages_utils.get_values(line)
            if wikilanguages_utils.values_sanity_check(values): rows = wikilanguages_utils.parse_values(values)

            for row in rows:
                page_namespace = int(row[1])
                if page_namespace != 0: continue
                qitem = row[2]
                qitems[qitem]=None
                qitems_list.append((qitem,))

        if iter % 100 == 0:
            duration = time.time() - functionstartTime
            items = len(qitems)

            print ('line: '+str(iter))
            print (items)
            print ('current time: ' + str(duration))
            print ('number of lines per second: '+str(iter/(time.time() - functionstartTime)))
            print ('number of items per second: '+str(items/(time.time() - functionstartTime)))
#            store_lines_per_second((time.time() - functionstartTime), iter, function_name, dumps_path, cycle_year_month)

#            print (qitems_list)
            cursor.executemany(query,qitems_list)
            qitems_list = list()

    cursor.executemany(query, qitems_list)
    print(len(qitems))
    print ('wd_all_qitems DONE')

    store_lines_per_second((time.time() - functionstartTime), iter, function_name, dumps_path, cycle_year_month)

    return qitems


# # 4 thousand items per second, while with dump it is 10,000. so this would take 5 hours.
# def wd_all_qitems(cursor):

#     function_name = 'wd_all_qitems'
#     print (function_name)

#     functionstartTime = time.time()

#     cursor.execute("CREATE TABLE qitems (qitem text PRIMARY KEY);")
#     mysql_con_read = mdb.connect(host='wikidatawiki.analytics.db.svc.eqiad.wmflabs',db='wikidatawiki_p', read_default_file='./my.cnf', cursorclass=mdb_cursors.SSCursor); mysql_cur_read = mysql_con_read.cursor()
#     query = 'SELECT page_title FROM page WHERE page_namespace=0;'
#     mysql_cur_read.execute(query)

#     i = 0; print (i)
#     while True:
#         row = mysql_cur_read.fetchone()
#         i+=1
#         if row == None: break
#         qitem = row[0].decode('utf-8')
#         query = "INSERT INTO qitems (qitem) VALUES ('"+qitem+"');"
#         cursor.execute(query)

#         if i % 1000 == 0:
#             duration = time.time() - functionstartTime
#             print (i, qitem)
#             print ('current time: ' + str(duration))
#             print ('number of line per second: '+str(i/(time.time() - functionstartTime)))
#             print ('number of items per second: '+str(i/(time.time() - functionstartTime)))

#     print ('All Qitems obtained and in wikidata.db.')
#     return i




def wd_check_qitem(cursor,qitem):
    query='SELECT 1 FROM qitems WHERE qitem = "'+qitem+'"'
    cursor.execute(query)
    row = cursor.fetchone()
    if row: row = str(row[0]);
    return row




def restore_ccc_binary_create_old_ccc_binary(languagecode,file):
#    print("start the CONTENT selection restore to the original ccc binary for language: "+languagecode)

    functionstartTime = time.time()

    if file == 1:
        filename = databases_path + 'old_ccc/' + languagecode+'_old_ccc.csv'
        output_file = codecs.open(filename, 'a', 'UTF-8')

    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()
    query = 'SELECT qitem, page_id, ccc_geolocated, country_wd, location_wd, language_strong_wd, created_by_wd, part_of_wd, keyword_title, ccc_binary FROM '+languagecode+'wiki;'

    parameters = []
    for row in cursor.execute(query):
        qitem = row[0]
        page_id = row[1]
        ccc_binary = None
        main_territory = None

        ccc_geolocated = row[2]
        if ccc_geolocated == 1: ccc_binary = 1;
        if ccc_geolocated == -1: ccc_binary = 0;

        for x in range(3,len(row)-2):
            if row[x] != None: ccc_binary = 1

#        print ((ccc_binary,main_territory,qitem,page_id))
        parameters.append((ccc_binary,main_territory,qitem,page_id))

        cur_ccc_binary = row[9]
        if file == 1: output_file.write(qitem + '\t' + str(cur_ccc_binary) + '\n')

    query = 'UPDATE '+languagecode+'wiki SET ccc_binary = ?, main_territory = ? WHERE qitem = ? AND page_id = ?;'
    cursor.executemany(query,parameters)
    conn.commit()

    duration = str(datetime.timedelta(seconds=time.time() - functionstartTime))


def check_current_ccc_binary_old_ccc_binary(languagecode):
#    print("compare current ccc with a previous one.")

    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()

    old_ccc_file_name = databases_path + 'old_ccc/' + languagecode+'_old_ccc.csv'
    old_ccc_file = open(old_ccc_file_name, 'r')    
    old_ccc = {}
    old_number_ccc = 0
    for line in old_ccc_file: # dataset
        page_data = line.strip('\n').split('\t')
#        page_data = line.strip('\n').split(',')
        ccc_binary = str(page_data[1])
        qitem = page_data[0]
        qitem=str(qitem)
        old_ccc[qitem] = ccc_binary
        if ccc_binary == 1: old_number_ccc+=1

    query = 'SELECT count(*) FROM '+languagecode+'wiki WHERE ccc_binary=1;'
    cursor.execute(query)
    current_number_ccc=cursor.fetchone()[0]

    print ('In old CCC there were: '+str(old_number_ccc)+' Articles, a percentage of '+str(float(100*old_number_ccc/wikipedialanguage_numberarticles[languagecode])))
    print ('In current CCC there are: '+str(current_number_ccc)+' Articles, a pecentage of '+str(float(100*current_number_ccc/wikipedialanguage_numberarticles[languagecode])))

    print ('\nProceeding now with the Article comparison: ')

    conn = sqlite3.connect(databases_path + wikipedia_diversity_db); cursor = conn.cursor()
#    query = 'SELECT qitem, page_id, page_title, ccc_binary FROM '+languagecode+'wiki;'
    query = 'SELECT qitem, page_id, page_title, ccc_binary, category_crawling_territories, language_weak_wd, affiliation_wd, has_part_wd, num_inlinks_from_CCC, num_outlinks_to_CCC, percent_inlinks_from_CCC, percent_outlinks_to_CCC, other_ccc_country_wd, other_ccc_location_wd, other_ccc_language_strong_wd, other_ccc_created_by_wd, other_ccc_part_of_wd, other_ccc_language_weak_wd, other_ccc_affiliation_wd, other_ccc_has_part_wd, other_ccc_keyword_title, other_ccc_category_crawling_relative_level, num_inlinks_from_geolocated_abroad, num_outlinks_to_geolocated_abroad, percent_inlinks_from_geolocated_abroad, percent_outlinks_to_geolocated_abroad FROM '+languagecode+'wiki;'

    i = 0
    j = 0

    for row in cursor.execute(query):
        qitem = row[0]
        page_id = str(row[1])
        page_title = row[2]

        ccc_binary = row[3]
        if ccc_binary == None or ccc_binary == 'None': ccc_binary = 0
        if ccc_binary == '1': ccc_binary = 1

        category_crawling_territories = str(row[4])
        language_weak_wd = str(row[5])
        affiliation_wd = str(row[6])
        has_part_wd = str(row[7])
        num_inlinks_from_CCC = str(row[8])
        num_outlinks_to_CCC = str(row[9])
        percent_inlinks_from_CCC = str(row[10])
        percent_outlinks_to_CCC = str(row[11])
        other_ccc_country_wd = str(row[12])
        other_ccc_location_wd = str(row[13])
        other_ccc_language_strong_wd = str(row[14])
        other_ccc_created_by_wd = str(row[15])
        other_ccc_part_of_wd = str(row[16])
        other_ccc_language_weak_wd = str(row[17])
        other_ccc_affiliation_wd = str(row[18])
        other_ccc_has_part_wd = str(row[19])
        other_ccc_keyword_title = str(row[20])
        other_ccc_category_crawling_relative_level = str(row[21])
        num_inlinks_from_geolocated_abroad = str(row[22])
        num_outlinks_to_geolocated_abroad = str(row[23])
        percent_inlinks_from_geolocated_abroad = str(row[24])
        percent_outlinks_to_geolocated_abroad = str(row[25])

        old_ccc_binary = old_ccc[qitem]
        if old_ccc_binary == None or old_ccc_binary == 'None': old_ccc_binary = 0
        if old_ccc_binary == '1' or old_ccc_binary == 1: old_ccc_binary = 1

        line = page_title+' , '+page_id+'\n\tcategory_crawling_territories\t'+category_crawling_territories+'\tlanguage_weak_wd\t'+language_weak_wd+'\taffiliation_wd\t'+affiliation_wd+'\thas_part_wd\t'+has_part_wd+'\tnum_inlinks_from_CCC\t'+num_inlinks_from_CCC+'\tnum_outlinks_to_CCC\t'+num_outlinks_to_CCC+'\tpercent_inlinks_from_CCC\t'+percent_inlinks_from_CCC+'\tpercent_outlinks_to_CCC\t'+percent_outlinks_to_CCC+'\tother_ccc_country_wd\t'+other_ccc_country_wd+'\tother_ccc_location_wd\t'+other_ccc_location_wd+'\tother_ccc_language_strong_wd\t'+other_ccc_language_strong_wd+'\tother_ccc_created_by_wd\t'+other_ccc_created_by_wd+'\tother_ccc_part_of_wd\t'+other_ccc_part_of_wd+'\tother_ccc_language_weak_wd\t'+other_ccc_language_weak_wd+'\tother_ccc_affiliation_wd\t'+other_ccc_affiliation_wd+'\tother_ccc_has_part_wd\t'+other_ccc_has_part_wd+'\tother_ccc_keyword_title\t'+other_ccc_keyword_title+'\tother_ccc_category_crawling_relative_level\t'+other_ccc_category_crawling_relative_level+'\tnum_inlinks_from_geolocated_abroad\t'+num_inlinks_from_geolocated_abroad+'\tnum_outlinks_to_geolocated_abroad\t'+num_outlinks_to_geolocated_abroad+'\tpercent_inlinks_from_geolocated_abroad\t'+percent_inlinks_from_geolocated_abroad+'\tpercent_outlinks_to_geolocated_abroad\t'+percent_outlinks_to_geolocated_abroad

#        if ccc_binary == 1: 

        if ccc_binary == 1 and old_ccc_binary == 0:
            print ('* '+line + '\n old_ccc_binary: '+str(old_ccc_binary)+', ccc_binary: '+str(ccc_binary))
            print ('now ccc (only positive), before non-ccc'+'\n')
            j += 1

        if ccc_binary == 0 and old_ccc_binary == 1:
            print ('* '+line + '\n old_ccc_binary: '+str(old_ccc_binary)+', ccc_binary: '+str(ccc_binary))
            print ('before ccc (with positive and negative), now non-ccc'+'\n')
            i += 1

    print ("*\n")
    print ("There are "+str(i)+" Articles that are non-CCC now but they were.")
    print ("There are "+str(j)+" Articles that are CCC now but they were non-CCC before.")
    print ("* End of the comparison")


