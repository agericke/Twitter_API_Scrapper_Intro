# Social Community Analysis of Ethereum Main Accounts.

This project analyses twitter users related to Ethereum's Blockchain. It makes a deep analysis of those Twitter accounts, thei rfollowers and their users. Then it analyses also tweets made by those accounts for making a gender calssification system according to the vectorized words from the accounts.

The project consists of three parts:

1. **Collect**: The project collects raw data from specific Twitter accounts social network. site (Twitter, Facebook, Reddit, Instagram, etc.) It also collects data for census names. Additionally, we collect real time tweets related to pecified blockchain related words.
2. Perform **community detection** to cluster users into communities.
3. Perform **supervised classification** to annotate messages and/or users according to some criterion.
4. Analyze the results and **summarize** your conclusions. 

The project picks main Ethereum's Blockchain realated twitter accounts, obtains their friends and followers, and for the top 10 most frequent twitter accounts also picks all their frineds and followers.

For the classifying part, we have picked 5.000 real time tweets that contain 
Blockchain related words, and our aim is to classify those users that made those tweets as female or male and see whether there is a strong difference in gender related to the active people on twitter talking about Blockchain stuff or not. For testing the model, we picked in the same way 500 real time tweets realted to the same words, and manually labeled their gender.

Regarding the clustering, we can see that the different methods tested cluster the community in 3 different clusters. When analyzing the members for each cluster, we focused in trying to analyze how the different main initial 
accounts where clustered. We saw that as more or less expected, ConsesnsyAcademy, gavoyfork and trufflesuite are nearly always clustered together, as they are accounts focused on development of Smart Contracts in Ethereum mainly and gavoforky is one of the founders of Ethereum, but is more active regarding development than is Vitalik.
On the other hand, binance and coinbase, the two crypto exchanges are always clustered together and oftenly clustered with Vitalik Buterin and ethereum official account. The only account that is in one case cluster alone, is trufflesuite, and this can be due to the distinct services they have not strictly realted to Ethereum Blockchain.

Finally, regarding the classification by gender, we can see that we have a best accuracy of 0.74 more or less, and if we see the plot of accuracies, we can see a bg difference between the settings that use the description for tokenization of the tokens, and the ones that do not use it. so it is really important to use the description, actually you can see a summary of mean accuracies per setting, being the use description setting the best one. We can also see in the summary of top missclassified, that many of them are due to the user's writting in their description something about their families for example. You can see in one example that one female has in the description "very proud of my  husband", and husband is a strong coefficient for males and that causes the missclassification. So we conclude that mainly the errors are because of description about other people distinct to the user using terms that are strong coefficients for the other users'.

If you ran summary.py, it will call all the other 3 python scripts andyou will see a summary of the results of all of them.

I have enabled an argument to be passed to summary.py, as the Girvan Newman algorithm takes more than 4 hours to run, if you do not pass the first argument as True to summarize.py, i.e. run it as:
python summarize.py True
it will only run the other two clustering algorithms which are much faster.

The main goals are to:
1. **Collect** raw data from some online social networking site (Twitter, Facebook, Reddit, Instagram, etc.)
2. Perform **community detection** to cluster users into communities.
3. Perform **supervised classification** to annotate messages and/or users according to some criterion.
4. Analyze the results and **summarize** your conclusions.

To grade your project, I will run the following commands:
```
python collect.py
python cluster.py
python classify.py
python summarize.py
```
So, your a4 folder should have (at least) those four files. **Please check that your files are named correctly, including using lower case letters!!!**

Here is what each script should do:

- `collect.py`: This should collect data used in your analysis. This may mean submitting queries to Twitter or Facebook API, or scraping webpages. The data should be raw and come directly from the original source -- that is, you may not use data that others have already collected and processed for you (e.g., you may not use [SNAP](http://snap.stanford.edu/data/index.html) datasets). Running this script should create a file or files containing the data that you need for the subsequent phases of analysis.
- `cluster.py`: This should read the data collected in the previous step and use any community detection algorithm to cluster users into communities. You may write any files you need to save the results.
- `classify.py`: This should classify your data along any dimension of your choosing (e.g., sentiment, gender, spam, etc.). You may write any files you need to save the results. This method should used supervised learning, which means you may have a secondary file containing any labeled data for the problem.
- `summarize.py`: This should read the output of the previous methods to write a textfile called `summary.txt` containing the following entries:
  - Number of users collected:
  - Number of messages collected:
  - Number of communities discovered:
  - Average number of users per community:
  - Number of instances per class found:
  - One example from each class:

Additionally, you should create a plain text file called 'description.txt' that contains a brief summary of what your code does and any conclusions you have made from the analysis (3-5 paragraphs).

Other notes:

- You may use any of the algorithms in scikit-learn, networkx, scipy, numpy, nltk to perform your analysis. You do not need to implement the methods from scratch.
- It is expected that when I run your `collect.py` script, I may get different data than you collected when you tested your code. While the final results of the analysis may differ, your scripts should still work on new datasets.
- You may checkin to Github any configuration or data files that your code needs. For example, if you've used manually annotated training data to fit a classifier, you may store that in Github. However, you should not store large data files (e.g., >50Mb). However, please ensure that your code will run using the commands above. Ensure that you use *relative*, not *absolute* paths when needed. (E.g., don't put "C:/Aron/data" as a path.) I recommend checking that your code works on another system prior to submission.
- If you use any non-standard libraries, please include a list of the library names in a file `requirements.txt`. I should then be able to install the with the command `pip install -r requirements.txt`.
