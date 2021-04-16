import datetime
import json
import sqlite3
import time
import traceback
from datetime import datetime as dt

import pywikibot
import requests
import toolforge
import wikipedia
from pywikibot.data.sparql import SparqlQuery

import wikilanguages_utils

# Libraries
# pip install wptools https://github.com/siznax/wptools easy to get info page= wptools.page('Ghandi') --> Page.get_wikidata(), etc.

# WikiRepo --> useful for MAPS and locations --> retrieve locations with specific depth and timespan https://github.com/andrewtavis/wikirepo

# endregion
with open('test.json', encoding="utf8") as f:
    langcode_pageid_dict = json.load(f)

def main():




    result = get_gender_data(langcode_pageid_dict)
    print(result)

    with open ('results.json','w') as fp:
        json.dump(result,fp,indent=4)



def create_gender_homepage_visibility_db():
    conn = sqlite3.connect(wikilanguages_utils.databases_path + 'gender_homepage_visibility_db')
    cursor = conn.cursor()
    #TODO: Create table with Qitems as genders

    table_name = 'wiki_gender_homepage_metrics'
    query = f"CREATE TABLE IF NOT EXISTS {table_name} (lang varchar ,timestamp timestamp, male integer , female integer, ,PRIMARY KEY (lang,timestamp ))"
    cursor.execute(query)

    table_name = 'wiki_homepage_items'
    query = f"CREATE TABLE IF NOT EXISTS {table_name} (lang varchar, item varchar,gender varchar ,PRIMARY KEY (lang,timestamp))"
    cursor.execute(query)

    conn.commit()






def get_gender_data(langcode_pageid_dict):
    startTime = time.time()
    print(f'Fetch started at {dt.fromtimestamp(startTime)}')

    counter = len(langcode_pageid_dict.keys())
    final_list = []
    url = 'https://query.wikidata.org/sparql'
    headers = {'Content-type': 'application/sparql-query'}
    query = 'SELECT ?gender (count(distinct ?person) as ?number) WHERE { VALUES ?person{ %s } ?person wdt:P31 wd:Q5. ?person wdt:P21 ?gender. SERVICE wikibase:label { bd:serviceParam wikibase:language "en". ?gender rdfs:label ?genderLabel.} } GROUP BY  ?gender'

    for langcode in langcode_pageid_dict.keys():

        timestamp = time.time()
        queryValues = get_wikibase_items(langcode, langcode_pageid_dict[langcode])
        newquery = query.replace('%s', queryValues)

        r = requests.post(url,params={'format':'json'},data=newquery,headers=headers)
        #wikiquery = SparqlQuery()
        #queryResult_list =wikiquery.select(newquery)
        #queryResult_dict = parseListQueryToDict(queryResult_list)
        try:
            response = r.json()
        except json.decoder.JSONDecodeError:
            continue

        parsed_sparql_response = parse_sparql_response(response)

        print(f'For lang {langcode}: {parsed_sparql_response}')

        #final_list.append({'lang':langcode, 'item':item,'gender':gender,'timestamp':timestamp})
        #final_dict[langcode] = [queryResult_dict, timestamp]
        elapsedTime = datetime.timedelta(seconds= time.time() - startTime)

        counter -= 1
        print(f' Current Elapsed time: {elapsedTime} language(s) remaining: {counter} ')

    finish_time = time.time()
    print(f'Script started at {dt.fromtimestamp(startTime)} and ended at {dt.fromtimestamp(finish_time)}. Duration of :{datetime.timedelta(seconds=finish_time - startTime)}')

    return final_list

def get_wikibase_items(langcode:str, main_page_id:int):

    url = f"https://{langcode}.wikipedia.org/w/api.php?action=query&format=json&prop=pageprops&pageids={main_page_id}&generator=links&utf8=1&gplnamespace=0&gpllimit=max"
    r = requests.get(url)
    result = parse_wikibase_response(r.json())
    return result



def parse_wikibase_response(response:json): # Return a string with all the values like wd:id1 wd:id2...

    items = ""
    for page in response['query']['pages']:
        try:

            Q = page['pageprops']['wikibase_item']
            items+= 'wd:'+Q+" "
        except KeyError:
            continue
    return items

def parse_sparql_response(response:json,langcode:str,timestamp):
    parsedResult = []


    if len(response["results"]["bindings"]) !=0:

        for row in response["results"]["bindings"]:
            try:
                gender = row["gender"]["value"]
                item = row["item"]["value"]
                parsedResult.append({{'lang':langcode, 'item':item,'timestamp':timestamp,'gender':gender}})

            except:
                continue
    return parsedResult

def parseListQueryToDict(queryResult_list):
    parsedResult = {'male':0,'female':0,'non-binary':0,'intersex':0,'transgender male':0,'transgender female':0,'agender':0}

    try:
        for row in queryResult_list:
            gender = row['genderLabel']
            number = row['number']
            parsedResult[gender] = number
    finally:
        return parsedResult

def getOutlinkNames(page_id:int,langcode:str):
    # TODO Format tuples to match return
    #TODO Get things right from the mysql query
    #TODO Work out how to do the MYSQL query
    #namesQuery = "SELECT pagelinks.pl_title FROM pagelinks INNER JOIN page ON pagelinks.pl_title = page.page_title WHERE pagelinks.pl_from = %s AND pagelinks.pl_from_namespace = 0 AND pagelinks.pl_namespace = 0"
    #%s is a replacement for the page_id to look for
    #namesQuery.replace('%s',page_id)

   # for r in mysql.mysql_query(namesQuery,params=page_id, dbname= langcode+'wiki'):
   #     print(r)
   # for page in pagegenerators.MySQLPageGenerator(namesQuery):
   #     print(page)
    links = list()
    try:
        wikipedia.set_lang(langcode)
        page = wikipedia.page(pageid=page_id)
        links = page.links

    except Exception as e:
        print(f' Langcode: {langcode} and page_id: {page_id} ')
   # except KeyError as e:
   #     print(f' KeyError exception: There is no links for this {langcode} and page {page_id} with name {page.title}')
   #     #The KeyError exception means there are no links
        #traceback.print_exc()

    #print(links)
    #print(tuples.gi_yieldfrom)
    return links


def createQueryValues(site: pywikibot.Site,
                      article_names: list):
    valuesString = ""

    for a in article_names:
        try:
            qid = getWikiDataId(site, a)
            valuesString += 'wd:' + qid + " "
        except pywikibot.exceptions.NoPage :
            continue
    return valuesString


def getWikiDataId(site: pywikibot.Site, article: str):
    return pywikibot.Page(site, article).data_item().getID()


def getPageIDByName(langcode:str,mainPageName: str):
    #query = 'select page_id from page where page_title = %s AND page_namespace = 0'
    #result = mysql.mysql_query(query,params=mainPageName,dbname=langcode)
    #result.close()
    try:
        wikipedia.set_lang(langcode)
        page = wikipedia.page(title=mainPageName)
        id = page.pageid
        return id
    except Exception as e:
        print(e)
        print(f'Something wrong with {langcode} and {mainPageName}')
        pass
   # print(langcode,page.title,id)



def getMainPageTitles():
    site = pywikibot.Site('wikidata', 'wikidata')
    repo = site.data_repository()
    item = pywikibot.ItemPage(repo, "Q5296")
    sitelinks = item.iterlinks(family='wikipedia')

    lang_dict = {}
    for link in sitelinks:
        val = str(link)
        val = val.replace('[', '')
        val = val.replace(']', '')
        val = val.split(':')

        element = {val[0]: val[1]}

        lang_dict.update(element)

    print(lang_dict)


def retrieve_from_wikidata(query: str, lang: str, page: str):
    timestamp = time.time()
    site = pywikibot.Site(lang)

    workingPage = pywikibot.Page(site, page).data_item().getID()
    print(workingPage)
    query = query.replace('qualifier', workingPage)
    print(query)
    wikiquery = SparqlQuery()
    result = wikiquery.select(query)
    print(result)


def safePercent(number, total):
    if (number == 0 or total == 0): return 0
    if (number > total): raise ValueError('number cannot be greater than total')
    return round(number / total * 100, 2)


def count_by_lang(lang: str, page: str,
                  sister_project: str):
    timestamp = time.time()
    site = pywikibot.Site(lang, sister_project)

    workingPage = pywikibot.Page(site, page)
    print(f'The working page is{workingPage}')
    linkedPages = workingPage.embeddedin(namespaces=0)
    # linkedPages = workingPage.linkedPages(
    #    namespaces=0)  # Get the outlinks of the namespace 0 (Article)
    repo = site.data_repository()

    maleCount = 0;
    femaleCount = 0;
    othersCount = 0;
    print(linkedPages)
    for linkedpage in linkedPages:

        try:

            qualifier = linkedpage.data_item().getID()
        except:

            continue
        item = pywikibot.ItemPage(repo, qualifier)
        dict_claims = item.get()['claims']

        try:
            p = dict_claims['P31'][0].getTarget()  # Target page of the property P31
            value = p.title()  # Value of the property 'P31'
            if value == 'Q5':  # Is a human

                gender = dict_claims['P21'][0].getTarget().title()
                print(f'The qualifier {qualifier} represents the person {linkedpage.title()} and')
                if 'Q6581097' == gender:
                    maleCount += 1  # Is a male
                    print('************************************************is a male')
                elif ('Q6581072' == gender):
                    femaleCount += 1  # Is a female
                    print('****************************************************is a female')
                else:
                    othersCount += 1  # Is other gender
                    print('*******************************************is other')
        except KeyError as err:
            # print('Keyerror, continuing the loop', err)
            continue

    totalCount = maleCount + femaleCount + othersCount
    dict_count = {'language': lang, 'page': workingPage.title(), 'qualifier': workingPage.data_item().getID(),
                  'sister_project': sister_project,
                  'counter': {'males': maleCount, 'females': femaleCount, 'others': othersCount},
                  'percentage': {'males': safePercent(maleCount, totalCount),
                                 'females': safePercent(femaleCount, totalCount),
                                 'others': safePercent(othersCount, totalCount)}, 'timestamp': timestamp}

    return dict_count


if __name__ == '__main__':
    main()
