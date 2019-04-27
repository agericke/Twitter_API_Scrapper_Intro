"""
Collect data.

First we will get all the accounts form the file ethereum-accounts.txt, the followers for this accounts and their friends.
Then we will find the 100 most folllowed accounts and also pick their friends and followers.
"""
# coding: utf-8
from collections import Counter
import matplotlib.pyplot as plt
import networkx as nx
import sys
import time
import json
import configparser
import pickle
import requests
from TwitterAPI import TwitterAPI


# Fetch male/female names from Census.

def get_census_names():
    """ Fetch a list of common male/female names from the census.
    For ambiguous names, we select the more frequent gender."""
    males = requests.get('http://www2.census.gov/topics/genealogy/1990surnames/dist.male.first').text.split('\n')
    females = requests.get('http://www2.census.gov/topics/genealogy/1990surnames/dist.female.first').text.split('\n')
    males_pct = dict([(m.split()[0].lower(), float(m.split()[1])) for m in males if m])
    females_pct = dict([(f.split()[0].lower(), float(f.split()[1])) for f in females if f])
    male_names = set([m for m in males_pct if m not in females_pct or males_pct[m] > females_pct[m]])
    female_names = set([f for f in females_pct if f not in males_pct or females_pct[f] > males_pct[f]])
    filename = "data/collect/male_names.pkl"
    pickle.dump(male_names, open(filename,'wb'))
    print("Census male names file saved to %s" % filename)
    filename = "data/collect/female_names.pkl"
    pickle.dump(female_names, open(filename,'wb'))   
    print("Census female names file saved to %s" % filename)
    return male_names, female_names


def get_twitter(config_file):
    """ Read the config_file and construct an instance of TwitterAPI.
    Args:
      config_file ... A config file in ConfigParser format with Twitter credentials
    Returns:
      An instance of TwitterAPI.
    """
    config = configparser.ConfigParser()
    config.read(config_file)
    twitter = TwitterAPI(
                   config.get('twitter', 'consumer_key'),
                   config.get('twitter', 'consumer_secret'),
                   config.get('twitter', 'access_token'),
                   config.get('twitter', 'access_token_secret'))
    return twitter


def read_screen_names(filename):
    """
    Read a text file containing Twitter screen_names, one per line.

    Params:
        filename....Name of the file to read.
    Returns:
        A list of strings, one per screen_name, in the order they are listed
        in the file.
    """
    file = open(filename)
    r = sorted([l.strip() for l in file])
    file.close()
    return r


def robust_request(twitter, resource, params, max_tries=5):
    """ If a Twitter request fails, sleep for 15 minutes.
    Do this at most max_tries times before quitting.
    Args:
      twitter .... A TwitterAPI object.
      resource ... A resource string to request
      params ..... A parameter dict for the request, e.g., to specify
                   parameters like screen_name or count.
      max_tries .. The maximum number of tries to attempt.
    Returns:
      A TwitterResponse object, or None if failed.
    """
    for i in range(max_tries):
        request = twitter.request(resource, params)
        if request.status_code == 200 or request.status_code == 404:
            return request
        else:
            print('Got error %s \n with status code %s\nsleeping for 15 minutes.' % (request.text, request.status_code))
            sys.stderr.flush()
            time.sleep(61 * 15)


def get_first_name(tweet):
    """
    Get the first name from a twitter object.
    
    Params:
        tweet....The Twitter object from where to pick the user name.
    Returns:
        The user first name in lower letters.
    """
    if 'user' in tweet and 'name' in tweet['user']:
        parts = tweet['user']['name'].split()
        if len(parts) > 0:
            return parts[0].lower()


def get_realtime_tweets(twitter, limit, words, male_names, female_names, filename):
    """Retrieve real time tweets objects that match any of the words provided, are written in english and located 
    in the U.S.
    
    Store only those tweets that include a user name that matches either a male or female name from the census.
    
    Params:
        twitter........The TwitterAPI object.
        limit..........The number of tweets we want to retrieve.
        words..........A list of strings, defining all the words that a tweet can match.
        male_names.....List of all male names retrieved from the census.
        female_names...List of all female names retrieved from the census.
        filename.......Name of the file for storing the real time tweets picked.
    Returns:
        A list of dicts, one per tweet, containing all the tweet information
    """
    tweets = []
    while True:
        try:
            # Restrict to U.S.
            for response in twitter.request('statuses/filter',
                        {'track': words, 'locations':'-124.637,24.548,-66.993,48.9974', 'language': 'en'}):
                # Check if Twitter object contains user description.
                if 'user' in response:
                    # Obtain First name from user description dict.
                    name = get_first_name(response)
                    #Append tweet only if name is in any of male or female names
                    if name in male_names or name in female_names:
                        tweets.append(response)
                        if len(tweets) % 100 == 0:
                            print('found %d tweets' % len(tweets))
                        if len(tweets) >= limit:
                            return tweets
        except:
            print("Unexpected error:", sys.exc_info()[0])
    pickle.dump(tweets, open(filename, 'wb'))
    print("Real time tweets saved to %s" % filename)
    return tweets


def get_users_by_screen_name(twitter, screen_names):
    """Retrieve the Twitter user objects for each screen_name.
    Params:
        twitter........The TwitterAPI object.
        screen_names...A list of strings, one per screen_name
    Returns:
        A list of dicts, one per user, containing all the user information
        (e.g., screen_name, id, location, etc)
    """
    results = []
    for s in screen_names:
        results.extend(robust_request(twitter, "users/lookup", {'screen_name': s}))
    return results


def get_friends(twitter, screen_name):
    """ Return a list of Twitter IDs for users that this person follows, up to 5000.
    See https://dev.twitter.com/rest/reference/get/friends/ids

    Args:
        twitter.......The TwitterAPI object
        screen_name... a string of a Twitter screen name
    Returns:
        A list of ints, one per friend ID, sorted in ascending order.

    Note: If a user follows more than 5000 accounts, we will limit ourselves to
    the first 5000 accounts returned.
    """
    #print("Inside: Requesting friends for screen_name %s" % screen_name)
    request = robust_request(twitter, "friends/ids", 
                              {'screen_name': screen_name, 'count':5000})
    if (request.status_code != 404):
        return sorted(request.json()['ids'])
    else:
        return str(request.status_code)

      
def add_all_friends(twitter, users):
    """ Get the list of accounts each user follows.

    Store the result in each user's dict using a new key called 'friends'.

    Args:
        twitter...The TwitterAPI object.
        users.....The list of user dicts.
    Returns:
        Nothing
    """
    #print("Requesting friends for a total of %s users" % len(users))
    for u in users:
        #print("Outside: Requesting friends for screen_name %s" % u['screen_name'])
        # Make the requst only if the user is not protected, else store friends as an empty list
        if u['protected'] != True:
            response = get_friends(twitter, u['screen_name'])
            if response == "404":
                u['friends'] = []
            else:
                u['friends'] = response
        else:
            #
            u['friends'] = []


def print_num_friends(users):
    """Print the number of friends per candidate, sorted by candidate name.
    See Log.txt for an 
    example.
    Args:
        users....The list of user dicts.
    Returns:
        Nothing
    """
    print('\n'.join('%s %d' % (u['screen_name'], len(u['friends'])) for u in users))


def count_friends(users):
    """ Count how often each friend is followed.
    Args:
        users: a list of user dicts
    Returns:
        a Counter object mapping each friend to the number of candidates who follow them.
    """
    result = Counter()
    for u in users:
        result.update(u['friends'])
    return result


def get_followers(twitter, screen_name):
    """ Return a list of Twitter IDs for users that follow this person, up to 2000.

    Args:
        twitter.......The TwitterAPI object
        screen_name... a string of a Twitter screen name
    Returns:
        A list of ints, one per friend ID, sorted in ascending order.

    Note: If a user has more than 5000 followers, we will limit ourselves to
    the first 5000 accounts returned.
    """
    #print("Inside: Requesting followers for screen_name %s" % screen_name)
    request = robust_request(twitter, "followers/ids", 
                              {'screen_name': screen_name, 'count':5000})
    if (request.status_code != 404):
        return sorted(request.json()['ids'])
    else:
        return str(request.status_code)
    

def add_all_followers(twitter, users):
    """ Get all the followers a user has.

    Store the result in each user's dict using a new key called 'followers'.

    Args:
        twitter...The TwitterAPI object.
        users.....The list of user dicts.
    Returns:
        Nothing
    """
    for u in users:
        #print("Outside: Requesting followers for screen_name %s" % u['screen_name'])
        if u['protected'] != True:
            response = get_followers(twitter, u['screen_name'])
            if response == "404":
                u['followers'] = []
            else:
                u['followers'] = response
        else:
            u['followers'] = []


def print_num_followers(users):
    """Print the number of followers per candidate, sorted by candidate name.
    Args:
        users....The list of user dicts.
    Returns:
        Nothing
    """
    print('\n'.join('%s %d' % (u['screen_name'], len(u['followers'])) for u in users))


def count_friends_and_followers(users):
    """ Count how often each user is followed or follows the defined users.
    Args:
        users: a list of user dicts
    Returns:
        a Counter object mapping each friend to the number of candidates who follow them.
    """
    result = Counter()
    for u in users:
        result.update(u['friends'])
        result.update(u['followers'])
    return result


def get_users_by_ids(twitter, ids):
    """Retrieve the Twitter user objects for each id.
    Params:
        twitter........The TwitterAPI object.
        ids............A list of strings, one per id
    Returns:
        A list of dicts, one per user, containing all the user information
        (e.g., screen_name, id, location, etc)
    """
    results = robust_request(twitter, "users/lookup", {'user_id': ids})
    return sorted(results.json(), key=lambda x: x['screen_name'])


def store_users(users, filename):
    pickle.dump(users, open(filename, 'wb'))
    print("Users file saved to %s" % filename)
    

def read_users(filename):
    pickle.load(open(filename, 'rb'))


def main():
    # 0 - Create twitter connection and pick census names
    male_names, female_names = get_census_names()
    print('found %d female and %d male names' % (len(female_names), len(male_names)))
    print('male name sample:', list(male_names)[:5])
    print('female name sample:', list(female_names)[:5])
    twitter = get_twitter('twitter.cfg')
    print('Established Twitter connection.')

    # 1 - Retrieve real time tweets that match Blockchain related words
    # Create list of blockchain related words
    words = ['ethereum', 'eth', 'bitcoin', 'btc', 'blockchain', 'cryptocurrencies', 'cryptocurrency', 'crypto', 'token', 'tokens',
            'solidity', 'litecoin', 'hyperledger','eos','dapp', 'dapps', 'smart contract', 'smart contracts', 'neo', 'miner', 'mining',
            'sidechain','pos','pow', 'dlt', 'polkadot']
    filename = 'data/collect/real-time-tweets.pkl'
    print("Pick tweets realted to Blockchain words %s" % words)
    tweets = get_realtime_tweets(twitter, 5000, words, male_names, female_names, filename)
    print("NUMBER OF TWEETS SAMPLED:")
    print('sampled %d tweets' % len(tweets))
    print('top names:', Counter(get_first_name(t) for t in tweets).most_common(10))
    
    # 2 - Read the screen names we want to build the network from.
    screen_names = read_screen_names('data/collect/ethereum-accounts.txt')
    print('Read screen names: %s' % screen_names)
    
    # 3 - Get the user's twitter accounts
    users = sorted(get_users_by_screen_name(twitter, screen_names), key=lambda x: x['screen_name'])
    print('found %d users with screen_names %s' %
          (len(users), str([u['screen_name'] for u in users])))
        
    # 4 - Get the user's each of this user follows (their "friends")
    # Obtain all friends
    add_all_friends(twitter, users)
    print('Friends per candidate:')
    print_num_friends(users)
    friend_counts = count_friends(users)
    print('Most common friends:\n%s' % str(friend_counts.most_common(5)))
    
    # Who follows this person?
    # Pick the first 5.000 people that follow this person.
    # 5 - Get the user's that follow this user(their "followers")
    # Obtain all followers for each user
    add_all_followers(twitter, users)
    print('Followers per candidate:')
    print_num_followers(users)
    friend_and_followers_counts = count_friends_and_followers(users)
    # Pick the 10 most common followers and users
    most_common = friend_and_followers_counts.most_common(10)
    print('Most common friends and followers:\n%s' % str(friend_and_followers_counts.most_common(10)))
    # Store in a list all the id's of the 10 most common users
    most_common_ids = [user_tuple[0] for user_tuple in most_common]
    
    # 6 - For each of the most common 100 users, obtain the user object and append it to the list of users' dict.
    new_users = get_users_by_ids(twitter, most_common_ids)
    print('found %d users with screen_names \n%s' %
        (len(new_users), str([u['screen_name'] for u in new_users])))
    
    # 7 - Find the friends and followers for each of the 100 most common followed users.
    add_all_friends(twitter, new_users)
    add_all_followers(twitter, new_users)
    
    # 8 - Add new_users to the initial users list and store it in the file users.json
    users_total = users + new_users
    print("total user objects obtained with friends and followers %d" % len(users_total)) # Obtain total number of users to store
    store_users(users_total, 'data/collect/users.pkl')


if __name__ == "__main__":
    main()