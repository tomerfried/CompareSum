#!/usr/bin/env python
# coding: utf-8

# In[1]:

from bs4 import BeautifulSoup
import requests
import inflect
import http.client
import urllib.request
import json

from PagesFunctions import get_content, get_rankings

http.client._MAXHEADERS = 1000


# In[7]:

# every Product object will be created for every product in the rating,
# in order to organize and manipulate the ratings all together
class Product:

    def __init__(self):
        self.name = None
        self.sites = []
        self.num_sites = 0
        self.ranks = []
        self.weighted_average = None
        self.title_occurrence = None
        self.sites_occurrence = None

    def add_site(self, rank, site):
        self.sites.append(site)
        self.num_sites += 1
        self.ranks.append(rank)
        self.weighted_average = sum(self.ranks) / self.num_sites


# In[2]:

# check if the keywords of the input appear in the results title and description,
# in order to to get only the relevant results
def contains_check(input_string, text):
    input_string = input_string.lower()
    text = text.lower()
    split = input_string.split(' ')
    engine = inflect.engine()
    without_s = lambda w: engine.singular_noun(w) if (engine.singular_noun(w)) else w
    for word in split:
        if (word not in text) and (without_s(word) not in text):
            return False
    return True


# In[27]:

# set different headers in order to surpass Google's blocking for requests
def get_random_ua():
    ua_file = 'ua-file.txt'
    try:
        with open(ua_file) as f:
            lines = f.readlines()
        if len(lines) > 0:
            import random2
            idx = random2.randint(0, len(lines))
            random_ua = lines[idx]
    except Exception as ex:
        print('Exception in random_ua')
        print(str(ex))
    finally:
        return random_ua


# this function filters unwanted results by getting rid of the results without all keywords
def best_results(input_str):
    with urllib.request.urlopen("http://api.serpstack.com/search?access_key=ebf60243ccdea529795d153fdbea3e05&query=" +
                                f"{input_str.replace(' ', '+')}&num=100&period=last_year") as url:
        data = json.loads(url.read().decode())

    results = data['organic_results']
    good_links = []

    for result in results:
        if contains_check(input_str, result['title']):
            good_links.append(result['url'])

    return good_links


def get_all_rankings(input_string, urls, sites_content):
    all_rankings = []

    print(len([page for page in sites_content if page != 0]))
    print(len([page for page in sites_content if page == 0]))
    for idx, site in enumerate(sites_content):

        if site != 0:
            rankings = get_rankings(site, input_string)
            if rankings != {}:
                all_rankings.append((urls[idx], rankings))

    return all_rankings


# creates an object for product with all of its details
def products_creator(all_rankings, title_occur, sites_occur):
    products = {}
    for site in all_rankings:
        rank_keys = site[1].keys()
        for rank in rank_keys:
            titles = site[1][rank]
            for title in titles:

                irrelevant = ['comments', '4k', 'resolution', 'cost', 'verdict', 'best', 'comparison', '128 gb ssd',
                              'd world', 'gb memory', 'purpose', 'screen size', 'apps', 'software', 'tablet',
                              'processor', 'storage', 'keyboard', 'battery life', 'standard lenses', 'sensor size',
                              'manual mode', 'k movies', 'k movies.', 'megapixels mp', 'macro lenses',
                              'image burst rate', 'kit lenses', 'image stabilization', 'camera body', 'other features',
                              'mp megapixels.', 'sennheiser', 'Audio-Technica', 'beyersdynamic', 'sony', 'oneodio',
                              'behringer', 'tascam', 'lyxpro', 'final thoughts', 'cowin', 'akg', 'features',
                              'activities', 'budget', 'precession', 'mid-range', 'high-end', 'Satellite GPS', 'battery',
                              'water-proofing', 'antivirus', 'antivirus free', 'gb ram', ]

                irrelevant_upper = [title.upper() for title in irrelevant]
                irrelevant_capitals = [title.title() for title in irrelevant]

                if (title not in irrelevant
                        and title not in irrelevant_upper
                        and title not in irrelevant_capitals):

                    if title not in products.keys():
                        products[title] = Product()
                        products[title].name = title
                        products[title].add_site(int(rank), site[0])

                    else:
                        if not (site[0] in products[title].sites):
                            products[title].add_site(int(rank), site[0])

                    if title in title_occur.keys():
                        products[title].title_occurrence = title_occur[title]
                    if title in sites_occur.keys():
                        products[title].sites_occurrence = sites_occur[title]

    return products
