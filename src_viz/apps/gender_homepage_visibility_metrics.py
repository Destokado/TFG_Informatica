import datetime
import json
import sqlite3
import time

from datetime import datetime as dt
import requests
import sys
sys.path.insert(0, '/srv/wcdo/src_viz/apps_dev')

def main():

    while True:
        startScripttime = dt.utcnow()
        print('Script started at {}'.format(startScripttime))
        with open('/srv/wcdo/src_viz/apps_dev/langcode_mainPage_ID.json', encoding="utf8") as f:
            langcode_pageid_dict = json.load(f)
        result = get_gender_data(langcode_pageid_dict)

        conn = sqlite3.connect('/srv/wcdo/src_viz/apps_dev/gender_homepage_visibility.db')
        cursor = conn.cursor()
        query = "INSERT INTO persons (lang,timestamp ,gender,person) VALUES (?,?,?,?) ;"
        cursor.executemany(query, result)
        print('Inserted', cursor.rowcount, 'records to the table.')
        conn.commit()
        conn.close()

        print('---------SCRIPT DONE--------------')
        finishScripttime = dt.utcnow()
        print('Started at {}, finished at  {} for a duration of {}'.format(startScripttime,finishScripttime,datetime.timedelta(seconds=finishScripttime.timestamp()-startScripttime.timestamp())))
        time.sleep(86400)

def get_last_data_update():
    conn = sqlite3.connect('/srv/wcdo/src_viz/apps_dev/gender_homepage_visibility.db')
    cursor = conn.cursor()
    query = "SELECT MAX(timestamp) FROM persons"
    cursor.execute(query)
    row = cursor.fetchone()
    conn.close()
    return row[0]

def create_gender_homepage_visibility_db():
    conn = sqlite3.connect('/srv/wcdo/src_viz/apps_dev/gender_homepage_visibility.db')
    cursor = conn.cursor()
    query = "CREATE TABLE IF NOT EXISTS persons (lang varchar NOT NULL ,timestamp timestamp NOT NULL, " \
            "gender integer NOT NULL , person integer NOT NULL ,PRIMARY KEY (lang,timestamp,gender,person ))"
    cursor.execute(query)
    conn.commit()
    conn.close()


def get_gender_data(langcode_pageid_dict):

    get_data_time = dt.utcnow()
    fetch_timestamp = dt.utcnow().today().timestamp()
    print('Fetch started at UTC {}'.format( get_data_time))

    counter = len(langcode_pageid_dict.keys())
    final_list = []
    not_in_list = []
    url = 'https://query.wikidata.org/sparql'
    headers = {'Content-Type':'application/sparql-query','Accept':'application/sparql-results+json', 'User-Agent':'WikipediaDiversityObservatory WDO (https://meta.wikimedia.org/wiki/Wikipedia_Diversity_Observatory;tools.wcdo@tools.wmflabs.org) python-requests/2.18.4'}
    query = "SELECT ?gender ?person WHERE { VALUES ?person { %s } ?person wdt:P31 wd:Q5; wdt:P21 ?gender. }"


    for langcode in langcode_pageid_dict.keys():


        try: #Get the wikidata IDs
            queryValues = get_wikibase_items(langcode, langcode_pageid_dict[langcode])
        except KeyError:
            print('Something wrong with {} when getting the query values'.format(langcode))
            print('*********************CONTINUING EXECUTION************************')
            not_in_list.append({'lang': langcode, 'error': 'Query Values'})
            counter -= 1
            continue
        except ValueError:
            print('Get wikibase items of {} response is empty'.format(langcode))

            print('*********************CONTINUING EXECUTION************************')
            not_in_list.append({'lang': langcode, 'error': 'No links or links without wikidata page'})
            counter -= 1
            continue

        #Fill the query and send the request
        newquery = query.replace('%s', queryValues)
        r = requests.post(url, params={'format': 'json'}, data=newquery, headers= headers)

        #Wait until the request api is available again
        if r.status_code == 429:
            print(r.headers,r.reason)
            print(r.request.headers)
            continue

        #Look for potential errors
        try:
            r.raise_for_status()
        except Exception as err:
            print(err)
            print('The Request object is:\n URL:{} \n BODY: {}\n Headers: {}'.format(r.request.url, r.request.body,
                                                                                     r.request.headers))
            not_in_list.append({'lang': langcode, 'error': 'Something bad with the response: {}'.format(err)})

            counter -= 1
            continue

        try:
            response = r.json()
        except json.decoder.JSONDecodeError:
            not_in_list.append({'lang': langcode, 'error': 'Converting query to json\n'})
            print('Response from langcode {} is {}'.format(langcode,response.url))
            print('The Response object is:\n URL:{} \n Headers: {}\n CONTENT: {}'.format(r.url,r.headers,r.content))
            counter -= 1
            continue

        try:
            parsed_sparql_response = parse_sparql_response(response, langcode, fetch_timestamp)
        except ValueError:
            not_in_list.append({'lang': langcode, 'error': 'No Wikidata Items were persons with gender'})
            counter -= 1
            continue

        final_list.extend(
            parsed_sparql_response)  # We use extend to append every element on the list. Otherwise, its appended as a single element
        elapsedTime = datetime.timedelta(seconds= dt.utcnow().timestamp() - get_data_time.timestamp())

        counter -= 1
        print(' Current Elapsed time: {} language(s) remaining: {} '.format(elapsedTime,counter))

   # finish_time = dt.utcnow()
    #print('Script started at {} and ended at {}. Duration of :{}'.format(dt.fromtimestamp(startTime),dt.fromtimestamp(finish_time),datetime.timedelta(seconds=finish_time - startTime)))
    print(not_in_list)
    print('************************************FINAL LIST****************\n')
    print(final_list)
    return final_list


def get_wikibase_items(langcode: str, main_page_id: int):
    url = "https://{}.wikipedia.org/w/api.php?action=query&format=json&prop=pageprops" \
          "&pageids={}&generator=links&utf8=1&gplnamespace=0&gpllimit=max".format(langcode,main_page_id)
    r = requests.get(url)
    result = parse_wikibase_response(r.json())
    if(len(result)==0):
        print('The {} response with status code{} was URL {} \n HEADERS: {} \n Body: {} \n'.format(langcode,r.reason,r.url,r.headers,r.content))
        raise ValueError('Empty string')

    return result



def get_gendercount_by_lang( langs,start,end):

    conn = sqlite3.connect('/srv/wcdo/src_viz/apps_dev/gender_homepage_visibility.db')
    cursor = conn.cursor()

    #query ="SELECT lang, gender ,COUNT(gender)  FROM persons WHERE lang IN (%s) "%','.join('?'*len(langs))+"GROUP BY lang,gender ORDER BY lang ASC;"
    query = "SELECT p1.lang, p1.gender, COUNT(p1.gender) as count,  p2.c as total FROM persons p1  " \
            "JOIN (SELECT lang, COUNT(gender) as c FROM persons p2 WHERE p2.timestamp BETWEEN ? AND ? GROUP BY lang HAVING c>0 ) p2 on p1.lang = p2.lang " \
            "WHERE p1.lang IN (%s) "%','.join('?'*len(langs))+"" \
            "AND p1.timestamp BETWEEN ? AND ? GROUP BY p1.lang,p1.gender ORDER BY p1.lang ASC;"

    params = (start,end) +tuple(langs) + (start,end)
    print(params)

    cursor.execute(query,params)
    conn.set_trace_callback(print)
    rows = cursor.fetchall()
    conn.close()
    print(rows)
    return rows

def parse_wikibase_response(response: json):  # Return a string with all the values like wd:id1 wd:id2...
    items = ""

    for page_id in response['query']['pages']:

        try:
            Q = response['query']['pages'][page_id]['pageprops']['wikibase_item']

            items += "wd:" + Q + " "
        except KeyError:  # The value is not found in the dict
            continue
        except TypeError:  # The link has no page
            continue
    return items


def parse_sparql_response(response: json, langcode: str, timestamp):
    parsedResult = []

    if len(response["results"]["bindings"]) != 0:

        for row in response["results"]["bindings"]:

            try:
                gender = row["gender"]["value"].split('/')
                person = row["person"]["value"].split('/')
                # Extract the URI and get only the QXXX

                parsedResult.append(tuple([langcode, timestamp, gender[len(gender) - 1], person[len(person) - 1]]))

            except:
                continue
    if(len(parsedResult)==0):
        raise ValueError('The sparql response is empty or has failed')
    return parsedResult


####UNUSED METHODS
#def getPageIDByName(langcode:str,mainPageName: str):
#
#    try:
#        wikipedia.set_lang(langcode)
#        page = wikipedia.page(title=mainPageName)
#        id = page.pageid
#        return id
#
#    except Exception as e:
#        print(e)
#        print('Something wrong with {} and {}'.format(langcode,mainPageName))
#
# def getMainPageTitles():
#    site = pywikibot.Site('wikidata', 'wikidata')
#    repo = site.data_repository()
#    item = pywikibot.ItemPage(repo, "Q5296")
#    sitelinks = item.iterlinks(family='wikipedia')
#
#    lang_dict = {}
#    for link in sitelinks:
#        val = str(link)
#        val = val.replace('[', '')
#        val = val.replace(']', '')
#        val = val.split(':')
#
#        element = {val[0]: val[1]}
#
#        lang_dict.update(element)
#
#    print(lang_dict)


# def safePercent(number, total):
#    if (number == 0 or total == 0): return 0
#    if (number > total): raise ValueError('number cannot be greater than total')
#    return round(number / total * 100, 2)


if __name__ == '__main__':
    #schedule.every().day.at("00:00").do(main)
    main()