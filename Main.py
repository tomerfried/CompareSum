#!/usr/bin/env python
# coding: utf-8

# In[ ]:
from GoogleFunctions import best_results, Product, get_all_rankings, products_creator
from PagesFunctions import get_content, titles_union, spaces_check, same_capitals, count_occurrence
import pandas as pd

# all the content of the relevant websites is downloaded
input_string = 'best cheap phones'
urls = best_results(input_string)
sites_content = get_content(urls)

# extraction of relevant text from every website
all_rankings = get_all_rankings(input_string, urls, sites_content)
all_rankings = titles_union(all_rankings)
all_rankings = spaces_check(all_rankings)
all_rankings = same_capitals(all_rankings)

# counts how many websites mention every product 
sites_occur, title_occur = count_occurrence(sites_content, all_rankings)

# appends all rankings and mention counts of the products to a single array
products = products_creator(all_rankings, title_occur, sites_occur)

# creation of a dataframe with all the data that was gathered on the products
columns = ['title', 'weighted_average', 'num_sites', 'title_occur', 'sites_occur']
df = pd.DataFrame(columns=columns)

for title in products:

    if products[title].title_occurrence is not None and len(title) >= 3:
        df = df.append({'title': title,
                        'weighted_average': products[title].weighted_average,
                        'num_sites': products[title].num_sites,
                        'title_occur': products[title].title_occurrence,
                        'sites_occur': products[title].sites_occurrence
                        }, ignore_index=True)

        df['num_sites'] = df['num_sites'].astype(int)
        df['sites_occur'] = df['sites_occur'].astype(int)

# calculation of top 10 rated products and most mentioned products
df.loc[df['sites_occur'] == 0, 'sites_occur'] = 1

df['wa_flip'] = 10 - df['weighted_average']
df['waf_ns'] = df['num_sites'] * df['wa_flip']

most_mentioned_df = df.sort_values(by=['sites_occur'], ascending=False)
top_rated_df = df.sort_values(by=['waf_ns'], ascending=False)

return top_rated_df, most_mentioned_df
