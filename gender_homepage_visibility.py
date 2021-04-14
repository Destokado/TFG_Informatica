import datetime
import json
import time
import wikipedia
import pywikibot
from pywikibot.data import mysql
from pywikibot.data.sparql import SparqlQuery
from pywikibot import pagegenerators
# Libraries
# pip install wptools https://github.com/siznax/wptools easy to get info page= wptools.page('Ghandi') --> Page.get_wikidata(), etc.

# WikiRepo --> useful for MAPS and locations --> retrieve locations with specific depth and timespan https://github.com/andrewtavis/wikirepo

# startregion
queryQ = """SELECT DISTINCT ?person ?personLabel  ?genderLabel 
   WHERE
   {
     ?person ?transcluded wd:qualifier.
     ?person wdt:P31 wd:Q5.
     ?person wdt:P21 ?gender.
     SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
   }"""

queryCounter = """SELECT ?gender ?genderLabel (count(distinct ?person) as ?number) 
   WHERE
   {
     ?person ?transclude wd:qualifier.
     ?person wdt:P31 wd:Q5.
     ?person wdt:P21 ?gender.
     SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en".
   ?gender rdfs:label ?genderLabel.}
   }
   GROUP BY  ?gender ?genderLabel """


# endregion

def main():
    # Get the languageCode and the name of the main page #TODO: Store languageCode and the page_id of the main page
    with open('langcode_mainPage_ID.json.json', encoding="utf8") as f:
        langcode_pageid_dict = json.load(f)

    get_gender_data(langcode_pageid_dict)


def get_gender_data(langcode_pageid_dict):
    final_dict = {}
    for langcode in langcode_pageid_dict.keys():
        timestamp = time.time()

        articleNames = getOutlinkNames(langcode=langcode, page_id=langcode_pageid_dict[langcode])
        site = pywikibot.Site(langcode, 'wikipedia')
        queryValues = createQueryValues(site, articleNames)

        wikiquery = SparqlQuery()
        query = query.replace('qualifier', queryValues)
        queryResult_dict = wikiquery.select(query)
        # make SPARQL query and get a JSON of this format #https://www.w3.org/TR/2013/REC-sparql11-results-json-20130321
        final_dict[langcode] = {queryResult_dict, timestamp}
    return final_dict


def getOutlinkNames(page_id:int,langcode:str):
    # TODO Format tuples to match return
    namesQuery = "SELECT pagelinks.pl_title FROM pagelinks INNER JOIN page ON pagelinks.pl_title = page.page_title WHERE pagelinks.pl_from = %s AND pagelinks.pl_from_namespace = 0 AND pagelinks.pl_namespace = 0"
    #%s is a replacement for the page_id to look for
    result = mysql.mysql_query(namesQuery,params=page_id, dbname=langcode+'wiki')
    generator = pagegenerators.MySQLPageGenerator(namesQuery)

    r = result.__next__()
    t = next(result)
    print(t)

    #print(tuples.gi_yieldfrom)
    return ['not implemented']


def createQueryValues(site: pywikibot.Site,
                      article_names: list):  # Return a string with all the values like wd:id1 wd:id2...
    valuesString = ""

    for a in article_names:
        qid = getWikiDataId(site, a)
        valuesString += 'wd:' + qid + " "
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


def show_results(startTime, dict_count):
    print('The gender count is as follows:')
    print('Males: ', dict_count['counter']['males'])
    print('Females: ', dict_count['counter']['females'])
    print('Others: ', dict_count['counter']['others'])
    print('The gender outlinks percentage of this article is:')
    finish_time = time.time()
    print(
        f'Males: {dict_count["percentage"]["males"]} Females: {dict_count["percentage"]["females"]} and Others: {dict_count["percentage"]["others"]}')
    print(f'Script ended in {datetime.timedelta(seconds=finish_time - startTime)}')


if __name__ == '__main__':
    main()
