
![logo resized](https://github.com/tomerfried/CompareSum-/assets/68680809/1fdc40ab-f513-4c8d-a84e-208a8927207f)

A project which summarizes ratings of various products, based on Google Search results:

- Scrapes data from product comparison websites
- The data is processed and added to a dataframe
- "Top 10 rated" and "Most mentioned" lists of products are returned as an output from the dataframe

Main.py - main file of the algorithm, gets the input, calculates the results using GoogleFunctions.py and PagesFunctions.py and returns the output
GoogleFunctions.py - methods related to the Google search results of the input
PagesFunctions - methods related to inside-website analysis of the Google search results

Examples:

The opens with this screen. Here, The query "camera phones" is typed:
![צילום מסך 1](https://github.com/tomerfried/CompareSum-/assets/68680809/54c9e989-3790-4616-8fd2-a60e3f4d098f)
Loading screen, while information is gathered and calculated:
![צילום מסך 2](https://github.com/tomerfried/CompareSum-/assets/68680809/175a0af1-5fea-4ca8-8e07-e3a917f89d7f)
Finally, the results are presented as a scrolling list, in a descnding order from top to bottom, according to chosen criteria (Top Rated/Most Mentioned):
![צילום מסך 3](https://github.com/tomerfried/CompareSum-/assets/68680809/d7d8c1f0-04fb-476a-9e49-397f98f8a316)
