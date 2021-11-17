#!/usr/bin/env python
# coding: utf-8

# In[3]:

from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
import re
import inflect
import aiohttp
import asyncio
from aiohttp import ClientPayloadError, ClientConnectorCertificateError, \
    ClientConnectorSSLError


# synchronous function: getting from single result, heart of the algorithm
async def fetch(session, url):
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        async with session.get(url, timeout=timeout) as response:
            if response.status == 200:
                #   response.raise_for_status()
                try:
                    return await response.text()
                except ClientPayloadError:
                    return 0
                except asyncio.TimeoutError:
                    return 0
                except UnicodeDecodeError:
                    return 0
            else:
                return 0
    except asyncio.TimeoutError:
        return 0
    except ClientConnectorCertificateError:
        return 0
    except ClientConnectorSSLError:
        return 0


# synchronous function: getting from all results
async def fetch_all(session, urls):
    tasks = []
    for url in urls:
        task = asyncio.create_task(fetch(session, url))
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    return results


# main asynchronous function
async def main(urls):
    async with aiohttp.ClientSession() as session:
        sites_content = await fetch_all(session, urls)
    return sites_content


# this function executes the asynchronous content receiving from the sites
def get_content(urls):
    loop = asyncio.get_event_loop()
    try:
        sites_content = loop.run_until_complete(main(urls))
    finally:
        loop.close()

    return sites_content


def get_titles_list(all_rankings):

    titles_list = []

    for site in all_rankings:
        rank_keys = site[1].keys()
        for rank in rank_keys:
            titles = site[1][rank]
            for title in titles:
                titles_list.append(title)

    return titles_list


# check common suffix of first string with prefix of second string
def common_fix(s1, s2):
    steps = range(min(len(s1), len(s2)) - 1, -1, -1)
    return next((s2[:n] for n in steps if s1[-n:] == s2[:n]), '')


# recognize same titles with minor changes and join them
def titles_union(all_rankings):
    rates = [site[1] for site in all_rankings]
    titles = []
    for dict_rates in rates:
        for k in dict_rates:
            for t in dict_rates[k]:
                titles.append(t)
    uniques = list(set(titles))


# Count Vectorizer is not in use, but the data frame is
    vectorizer = CountVectorizer().fit_transform(uniques)
    vectors = vectorizer.toarray()
    csim = cosine_similarity(vectors)

    df = pd.DataFrame(csim, index=uniques, columns=uniques)

    trans_dict = {}
    for index in df:
        reduced_index = index.replace(index.split()[0] + ' ', '')

        for column in df.columns:
            reduced_column = column.replace(column.split()[0] + ' ', '')

            if index != column:

                if reduced_index == column:
                    trans_dict[column] = index

                elif reduced_column == index:
                    trans_dict[index] = column

                elif index.lower() == column.lower():

                    index_capitals = len(re.findall(r'[A-Z]', index))
                    column_capitals = len(re.findall(r'[A-Z]', column))

                    if index_capitals > column_capitals:
                        trans_dict[column] = index
                    else:
                        trans_dict[index] = column

    for site in all_rankings:
        for key in site[1].keys():
            for i in range(len(site[1][key])):
                if site[1][key][i] in trans_dict.keys():
                    site[1][key][i] = trans_dict[site[1][key][i]]

    return all_rankings


# add spaces to titles without ones
def spaces_check(all_rankings):

    titles_list = get_titles_list(all_rankings)

    titles_list_no_spaces = [title.replace(' ', '') for title in titles_list]

    for site in all_rankings:
        rank_keys = site[1].keys()
        for rank in rank_keys:
            titles = site[1][rank]
            for i in range(len(titles)):

                title_no_space = titles[i].replace(' ', '')

                matches_indices = []
                for idx, title in enumerate(titles_list_no_spaces):
                    if title_no_space == title:
                        matches_indices.append(idx)
                matches_titles = [titles_list[i] for i in matches_indices]

                titles[i] = max(matches_titles, key=len)

    return all_rankings


# match capital letters of titles of the same product
def same_capitals(all_rankings):

    titles_list_capitals = get_titles_list(all_rankings)

    titles_list_lowers = [title.lower() for title in titles_list_capitals]

    for site in all_rankings:
        rank_keys = site[1].keys()
        for rank in rank_keys:
            titles = site[1][rank]
            for i in range(len(titles)):

                title_lower = titles[i].lower()

                matches_indices = []
                for idx, title in enumerate(titles_list_lowers):
                    if title_lower == title:
                        matches_indices.append(idx)
                matches_titles = [titles_list_capitals[i] for i in matches_indices]

                c_max = len(re.findall(r'[A-Z]', matches_titles[0]))
                c_max_idx = 0
                for idx, title in enumerate(matches_titles):
                    c_sum = len(re.findall(r'[A-Z]', title))

                    if c_sum > c_max:
                        c_max = c_sum
                        c_max_idx = idx

                titles[i] = matches_titles[c_max_idx]

    return all_rankings


# get ranked products from a website
def get_rankings(req, input_string):
    soup = BeautifulSoup(req, 'html.parser')

    headlines = {'h1': [], 'h2': [], 'h3': [], 'li': []}

    for key in headlines:
        key_object = soup.find_all(key)
        for tag in key_object:
            headlines[key].append(tag.text)

    # recognize the relevant headlines

    rankings = {}

    for key in headlines:
        for text in headlines[key]:

            edited_text = None

            if 40 > len(text) > 4:
                if text[0].isdigit() and (text[1] == '.'):
                    if text[2] == ' ':
                        edited_text = text[3:]
                    elif text[2].isalpha():
                        edited_text = text[2:]
                    rank = text[0]

                elif text[0:2].isnumeric() and (text[2] == '.'):
                    if text[3] == ' ':
                        edited_text = text[4:]
                    elif text[3].isalpha():
                        edited_text = text[3:]
                    rank = text[0:2]

                elif text[0].isdigit() and (text[1] == ' '):
                    if text[2].isalpha():
                        edited_text = text[2:]
                    elif text[2:4] == '- ':
                        edited_text = text[4:]
                    elif text[2:4] == '. ':
                        edited_text = text[4:]
                    rank = text[0]

                elif text[0:2].isnumeric() and (text[2] == ' '):
                    if text[3].isalpha():
                        edited_text = text[3:]
                    elif text[3:5] == '- ':
                        edited_text = text[5]
                    elif text[3:5] == '. ':
                        edited_text = text[5:]
                    rank = text[0:2]

                elif text[0].isdigit() and text[1].isupper():
                    edited_text = text[1:]
                    rank = text[0]

                elif text[0:2].isnumeric() and text[2].isupper():
                    edited_text = text[2:]
                    rank = text[0:2]

                elif text[0] == '#' and text[1].isdigit() and not text[2].isdigit():
                    if text[2] == ' ' and text[3].isupper():
                        edited_text = text[3:]
                    elif text[2:4] == '. ':
                        edited_text = text[4:]
                    elif text[2:5] == ' - ':
                        edited_text = text[5:]
                    rank = text[1]

                elif text[0] == '#' and text[1:3].isnumeric():
                    if text[3] == ' ' and text[4].isalpha():
                        edited_text = text[4:]
                    elif text[3:6] == ' - ':
                        edited_text = text[6:]
                    elif text[3:5] == '. ':
                        edited_text = text[5:]
                    rank = text[1:3]

                elif text[0].isdigit() and text[1:3].islower() and text[3:6] == ' - ':
                    edited_text = text[6:]
                    rank = text[0]

                elif text[0:2].isnumeric() and text[2:4].islower() and text[4:7] == ' - ':
                    edited_text = text[7:]
                    rank = text[0:2]

                if edited_text is not None:

                    if rank not in rankings.keys():
                        rankings[rank] = edited_text.strip().replace('(', '').replace(')', '').replace(' Plus',
                                                                                                       '+').replace(
                            ' and ', ' & ')

                    else:
                        if type(rankings[rank]) is str:
                            rankings[rank] = [rankings[rank],
                                              edited_text.strip().replace('(', '').replace(')', '').replace('Plus',
                                                                                                            '+').replace(
                                                  ' and ', ' & ')]
                        elif type(rankings[rank]) is list:
                            rankings[rank].append(
                                edited_text.strip().replace('(', '').replace(')', '').replace('Plus', '+').replace(
                                    ' and ', ' & '))

        # get rid of websites without relevant rankings

    rank_nums = set(map(int, rankings.keys()))
    if len(rankings) < 5 or not set([1, 2, 3]).issubset(rank_nums):
        rankings = {}

    # check for 'and' or '/' and split if necessary
    add_words = [' / ', ' & ', '/', '&', ' - ', ' or ', ', ']
    for key in rankings:

        for word in add_words:

            if type(rankings[key]) is str:

                rankings[key] = rankings[key].split(word)

            elif type(rankings[key]) is list:
                titles = [t.split(word) for t in rankings[key]]
                rankings[key] = [title for sublist in titles for title in sublist]

    # check for unnecessary characters and remove them
    for key in rankings:

        temp = None

        for i in range(len(rankings[key])):

            if ' :' in rankings[key][i]:
                rankings[key][i] = rankings[key][i].split(' :')[0]
            elif ':' in rankings[key][i]:
                rankings[key][i] = rankings[key][i].split(':')[0]
            if ', from $' in rankings[key][i]:
                rankings[key][i] = rankings[key][i].split(', from $')[0]
            if ', from £' in rankings[key][i]:
                rankings[key][i] = rankings[key][i].split(', from £')[0]
            if ' - £' in rankings[key][i]:
                rankings[key][i] = rankings[key][i].split(' - £')[0]
            if ' - $' in rankings[key][i]:
                rankings[key][i] = rankings[key][i].split(' - $')[0]
            if ' £' in rankings[key][i]:
                rankings[key][i] = rankings[key][i].split(' £')[0]
            if ' $' in rankings[key][i]:
                rankings[key][i] = rankings[key][i].split(' $')[0]

            if '\xa0' in rankings[key][i]:
                rankings[key][i] = rankings[key][i].replace('\xa0', '')

            if '\u200b' in rankings[key][i]:
                rankings[key][i] = rankings[key][i].replace('\u200b', '')

            if '"' in rankings[key][i]:
                while '"' in rankings[key][i]:
                    rankings[key][i] = rankings[key][i].replace('"', '')

            if '“' in rankings[key][i]:
                while '“' in rankings[key][i]:
                    rankings[key][i] = rankings[key][i].replace('“', '')

            if '”' in rankings[key][i]:
                while '”' in rankings[key][i]:
                    rankings[key][i] = rankings[key][i].replace('”', '')

            if rankings[key][i][-2:] == ' |':
                rankings[key][i] = rankings[key][i].replace(' |', '')



            for word in ['-inch', 'inch']:
                if word in rankings[key][i].lower():
                    rankings[key][i] = rankings[key][i].replace(word, ' ').replace(word.title(), ' ').replace(word.upper(), ' ')

            for year in [' 2020', ' 2019', ' 2018', ' 2017', ' 2016', ' 2015', ' 2014', ' 2013', ' 2012', ' 2011',
                         ' 2010',
                         '2020 ', '2019 ', '2018 ', '2017 ', '2016 ', '2015 ', '2014 ', '2013 ', '2012 ', '2011 ',
                         '2010 ']:
                if year in rankings[key][i]:
                    rankings[key][i] = rankings[key][i].replace(year, '')

            input_variations = input_string.lower().split() + input_string.upper().split() + input_string.title().split()
            engine = inflect.engine()
            without_s = lambda w: engine.singular_noun(w) if (engine.singular_noun(w)) else w
            input_v_singulars = list(map(without_s, input_variations))
            input_variations = list(set((input_variations + input_v_singulars)))

            for word in input_variations:
                if ' ' + word in rankings[key][i]:
                    rankings[key][i] = rankings[key][i].replace(' ' + word, '')

    # add cropped title to short splits
    for key in rankings:

        for i in range(len(rankings[key])):

            if i + 1 < len(rankings[key]):

                common_word = common_fix(rankings[key][i], rankings[key][i + 1])
                try:
                    if len(rankings[key][i + 1]) <= 5 and len(common_word) < 3:
                        if rankings[key][i + 1][0:len(common_word)] == common_word:
                            rankings[key][i + 1] = rankings[key][i] + rankings[key][i + 1].replace(common_word, '')
                        else:
                            rankings[key][i + 1] = rankings[key][i] + ' ' + rankings[key][i + 1]
                except IndexError:
                    pass

                if len(common_word) >= 3:
                    copy = rankings[key][i]
                    rankings[key][i + 1] = copy.replace(common_word, rankings[key][i + 1])

    # remove unnecessary spaces in each title
    for key in rankings:

        for i in range(len(rankings[key])):
            rankings[key][i] = rankings[key][i].strip()

    return rankings


# counts in how many sites a product appears, and how many times mentioned all sites in total
def count_occurrence(sites_content, all_rankings):

    titles_list = get_titles_list(all_rankings)

    unique_titles = list(set(titles_list))

    filtered_titles = {}

    for title in unique_titles:
        irrelevant = False

        words = title.split()
        for word in words:
            if word.islower() and word.isalpha():
                irrelevant = True
                continue

        if not irrelevant:
            filtered_titles[title] = 0

    sorted_len = {k: v for k, v in sorted(filtered_titles.items(), key=lambda item: len(item[0]), reverse=True)}
    sites_occur = {title: 0 for title in sorted_len.keys()}
    for i, v in enumerate(sites_content):
        for title in sorted_len.keys():
            if sites_content[i] != 0:

                if title in sites_content[i]:
                    sites_occur[title] += 1
                    filtered_titles[title] += sites_content[i].count(title)
                    sites_content[i] = sites_content[i].replace(title, '')

                elif title.replace(' +', ' Plus') in sites_content[i]:

                    sites_occur[title] += 1
                    filtered_titles[title] += sites_content[i].count(title.replace(' +', ' Plus'))
                    sites_content[i] = sites_content[i].replace(title.replace(' +', ' Plus'), '')

                elif title.replace('+', ' Plus') in sites_content[i]:

                    sites_occur[title] += 1
                    filtered_titles[title] += sites_content[i].count(title.replace('+', ' Plus'))
                    sites_content[i] = sites_content[i].replace(title.replace('+', ' Plus'), '')

    sorted_count = {k: v for k, v in sorted(filtered_titles.items(), key=lambda item: item[1], reverse=True)}

    return sites_occur, sorted_count
