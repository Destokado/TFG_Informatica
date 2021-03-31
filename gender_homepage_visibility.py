import datetime
import time
import self as self
import pywikibot


# Libraries
# pip install wptools https://github.com/siznax/wptools easy to get info page= wptools.page('Ghandi') --> Page.get_wikidata(), etc.

# WikiRepo --> useful for MAPS and locations --> retrieve locations with specific depth and timespan https://github.com/andrewtavis/wikirepo


def main():
    startTime = time.time()

    dict_count = count_by_lang(lang='ca', page='Pablo Picasso', sister_project='wikipedia')

    show_results(startTime, dict_count)


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
    linkedPages = workingPage.linkedPages(
        namespaces=0)  # Get the outlinks of the namespace 0 (Article)
    repo = site.data_repository()

    maleCount = 0;
    femaleCount = 0;
    othersCount = 0;
    qualifiers = list()
    for linkedpage in linkedPages:

        try:
            qualifier = linkedpage.data_item().getID()
            if qualifier in qualifiers: continue
            qualifiers.append(qualifier)
        except:
            continue

        item = pywikibot.ItemPage(repo, qualifier)
        dict_claims = item.get()['claims']

        try:
            p = dict_claims['P31'][0].getTarget()  # Target page of the property P31
            value = p.title()  # Value of the property 'P31'
            if value == 'Q5':  # Is a human
                # print('The item ' + qualifier + ' is a human and is a')
                gender = dict_claims['P21'][0].getTarget().title()
                print(f'The qualifier {qualifier} represents the person {linkedpage.title()} and')
                if 'Q6581097' == gender:
                    maleCount += 1  # Is a male
                    print('************is a male')
                elif ('Q6581072' == gender):
                    femaleCount += 1  # Is a female
                    print('***************is a female')
                else:
                    othersCount += 1  # Is other gender
                    print('**************is other')
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


def synchronized_add(dict):
    with self._lock:
        # Add dict to the general dict
        # OR
        # Include dict to the database
        print('')

# Previous time 0:04:31.471516
#0:04:21.906243 without restricting list