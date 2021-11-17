A project which summarizes ratings of various products, based on Google Search results:

- Scrapes data from product comparison websites
- The data is processed and added to a dataframe
- "Top 10 rated" and "Most mentioned" lists of products are returned as an output from the dataframe

Main.py - main file of the algorithm, gets the input, calculates the results using GoogleFunctions.py and PagesFunctions.py and returns the output
GoogleFunctions.py - methods related to the Google search results of the input
PagesFunctions - methods related to inside-website analysis of the Google search results
