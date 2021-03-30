import datetime
import time

import dash
import pandas as pd
import plotly as px

import pywikibot

startTime = time.time()

# Libraries
# pip install wptools https://github.com/siznax/wptools easy to get info page= wptools.page('Ghandi') --> Page.get_wikidata(), etc.

# WikiRepo --> useful for MAPS and locations --> retrieve locations with specific depth and timespan https://github.com/andrewtavis/wikirepo


# Press the green button in the gutter to run the script.
def safePercent(number, total):
    if (number == 0 or total ==0): return 0
    if (number > total): raise ValueError('number cannot be greater than total')
    return number/total*100

site = pywikibot.Site('en', 'wikipedia')
pages = pywikibot.Page(site, 'Pablo Picasso').linkedPages(namespaces=0,total=100)  # Get the outlinks of the namespace 0 (Article)
repo = site.data_repository()
maleCount = 0;
femaleCount = 0;
othersCount = 0;

for page in pages:

    try:

        qualifier = page.data_item()
        qualifier = qualifier.getID()
        print(qualifier)
    except:
        print('x')
        continue

    #newSite = pywikibot.Site("wikidata", "wikidata")

    item = pywikibot.ItemPage(repo, qualifier)
    dict_claims = item.get()['claims']

    # print(property_dict)
    if dict_claims:
        try:
            p = dict_claims['P31'][0].getTarget()  # Target page of the property P31
            p.get()
            value = p.title()  # Value of the property 'P31'

            if value == 'Q5':
                print('The item ' + qualifier + ' is a human and is a')
                gender = dict_claims['P21'][0].getTarget().title()
                #  gender = gender.title()
                if (gender):
                    if 'Q6581097' in gender:
                        maleCount += 1  # Is a male
                        print('************is a male')
                    elif ('Q6581072' in gender):
                        femaleCount += 1  # Is a female
                        print('***************is a female')

                    else:
                        othersCount += 1  # Is other
                        print('**************is other')
        except KeyError as err:

            print('Keyerror, continuing the loop', err)
            continue

print('The gender count is as follows:')
print('Males: ', maleCount)
print('Females: ', femaleCount)
print('Others: ', othersCount)
print('The gender outlinks percentage of this article is:')
totalCount = maleCount + femaleCount + othersCount
finishTIme = time.time()
print(f'Males: {safePercent(maleCount,totalCount)} Females: {safePercent(femaleCount,totalCount)} and Others: {safePercent(othersCount,totalCount)}')

print(f'Script ended in { datetime.timedelta(seconds=finishTIme-startTime)}')



