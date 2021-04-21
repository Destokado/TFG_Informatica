import datetime
import json
import sqlite3
import time
import traceback
from datetime import datetime as dt

import requests



def main():
    with open('langcode_mainPage_ID.json', encoding="utf8") as f:
        langcode_pageid_dict = json.load(f)

    result = get_gender_data(langcode_pageid_dict)
    print(result)
    conn = sqlite3.connect('gender_homepage_visibility_db')
    cursor = conn.cursor()
    query = "INSERT INTO persons (lang,timestamp ,gender,person) VALUES (?,?,?,?) ;"

    cursor.executemany(query, result)
    print('Inserted', cursor.rowcount, 'records to the table.')
    conn.commit()
    conn.close()


def create_gender_homepage_visibility_db():
    conn = sqlite3.connect('gender_homepage_visibility_db')
    cursor = conn.cursor()
    query = f"CREATE TABLE IF NOT EXISTS persons (lang varchar NOT NULL ,timestamp timestamp NOT NULL, gender integer NOT NULL , person integer NOT NULL ,PRIMARY KEY (lang,timestamp,gender,person ))"
    cursor.execute(query)
    conn.commit()
    conn.close()


def get_gender_data(langcode_pageid_dict):
    startTime = time.time()
    print(f'Fetch started at {dt.fromtimestamp(startTime)}')

    counter = len(langcode_pageid_dict.keys())
    final_list = []
    not_in_list = []
    url = 'https://query.wikidata.org/sparql'
    headers = {'Content-type': 'application/sparql-query'}

    query = "SELECT ?gender ?person WHERE { VALUES ?person { %s } ?person wdt:P31 wd:Q5; wdt:P21 ?gender. }"
    for langcode in langcode_pageid_dict.keys():

        timestamp = time.time()
        try:
            queryValues = get_wikibase_items(langcode, langcode_pageid_dict[langcode])
        except KeyError:
            print(f'Something wrong with {langcode} when getting the query values')
            traceback.print_exc()
            print('*********************CONTINUING EXECUTION************************')
            not_in_list.append({'lang': langcode, 'error': 'Query Values'})
            counter -= 1
            continue
        newquery = query.replace('%s', queryValues)
        r = requests.post(url, params={'format': 'json'}, data=newquery, headers=headers)

        try:
            response = r.json()
        except json.decoder.JSONDecodeError:
            not_in_list.append({'lang': langcode, 'error': 'Converting query to json'})
            counter -= 1
            continue

        parsed_sparql_response = parse_sparql_response(response, langcode, timestamp)
        if (len(parsed_sparql_response) == 0):
            not_in_list.append({'lang': langcode, 'error': 'Parsed response is empty'})
            counter -= 1
            continue

        final_list.extend(
            parsed_sparql_response)  # We use extend to append every element on the list. Otherwise, its appended as a single element
        elapsedTime = datetime.timedelta(seconds=time.time() - startTime)

        counter -= 1
        print(f' Current Elapsed time: {elapsedTime} language(s) remaining: {counter} ')

    finish_time = time.time()
    print(
        f'Script started at {dt.fromtimestamp(startTime)} and ended at {dt.fromtimestamp(finish_time)}. Duration of :{datetime.timedelta(seconds=finish_time - startTime)}')
    print(not_in_list)
    return final_list


def get_wikibase_items(langcode: str, main_page_id: int):
    url = f"https://{langcode}.wikipedia.org/w/api.php?action=query&format=json&prop=pageprops&pageids={main_page_id}&generator=links&utf8=1&gplnamespace=0&gpllimit=max"
    r = requests.get(url)
    result = parse_wikibase_response(r.json())
    return result


def get_gendercount_by_lang( langs):

    conn = sqlite3.connect('gender_homepage_visibility_db')
    cursor = conn.cursor()

    #query ="SELECT lang, gender ,COUNT(gender)  FROM persons WHERE lang IN (%s) "%','.join('?'*len(langs))+"GROUP BY lang,gender ORDER BY lang ASC;"
    query = "SELECT p1.lang, p1.gender, COUNT(p1.gender) as count,  p2.c as total FROM persons p1  JOIN (SELECT lang, COUNT(gender) as c FROM persons p2 GROUP BY lang HAVING c>0) p2 on p1.lang = p2.lang WHERE p1.lang IN (%s) "%','.join('?'*len(langs))+"GROUP BY p1.lang,p1.gender ORDER BY p1.lang ASC;"
    cursor.execute(query,langs)
    rows = cursor.fetchall()
    conn.close()
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
#        print(f'Something wrong with {langcode} and {mainPageName}')
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
    main()
