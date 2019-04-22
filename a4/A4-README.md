# A4 - BLOCKCHAIN RELATED TWITTER ACCOUNTS SOCIAL ANALYSIS

For the final assignment, I will try to analyse and build a social-network from twitter users that talk about several major Ethereum accounts and topics. Ethereum is one of the bigget and most relevant Blockchains, where the concept of decentralized applications and Smart Contracts was first introduced and implemented within a Blockchain.
Once picked the tweets, we will obtained all users from them and build a social network from them.
We will build a social network based on the followers these people have, and cluster them using sci.kit packages, trying to identify different groups that talk about Ethereum. We probably have clusters that group developers together and normal users in another group, but we will find out what this clustering outputs.
Finally, we will run a sentiment-analysis on the tweets' text and compute what people if general sentiment among different main Ethereum businesses and developers.

## COLLECT PHASE.

We will collect all tweets that talk or mention in some way one of the following Ethereum's blockchain main accounts or users:
- @consenSysAcad: On of the main businesses that develops and mantains Ethereum Blockchain.
- @ethereum: Official Ethereum's Blockchain Twitter Account.
- @VitalikButerin: One of the main Ethereum's Blockchain Founders.
- @gavofyork: Gavin Wood's Account, founder of Parity Technologies (One of the main Ethereum's client), co-founder of Ethereum.
- @trufflesuite: One of the world's most popular ethereum development framework.
- @coinbase: One of the biggest cryptocurrencies Exchange.
- @binance: Another major cryptocurrency Exchange.

With these accounts, we cover etherum's blockchains proper acoount, some major businesses accounts related to Ethereum, some of the most important individuals related to Ethereum's Blockchains, and some public cryptocurrencies exchanges, so that we have a diverse and big picture of users.

We will store theses accounts in a .txt file, and have a python script pick those accounts from that file and obtained all tweets related to those accounts and concepts.
