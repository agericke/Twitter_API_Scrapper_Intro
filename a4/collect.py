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
from TwitterAPI import TwitterAPI


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


def robust_request_iterate(twitter, resource, params, max_pages=5):
    """ Function for managing pagination of results
    It will sequentially obtain all the pages using the cursor provided by Twittter.
    Args:
      twitter .... A TwitterAPI object.
      resource ... A resource string to request
      params ..... A parameter dict for the request, e.g., to specify
                   parameters like screen_name or count.
      max_pages .. The maximum number of pages to ask for.
    Returns:
      A TwitterResponse object, or None if failed.
    """
    cursor = -1
    # Add cursor parameter to params:
    params['cursor'] = cursor
    print(params)
    results = []
    while True:
        response = robust_request(twitter, resource, params)
        results.extend(response)
        print(response)
        next_cursor = response.json()['next_cursor']
        print(next_cursor)
        params['cursor'] = next_cursor
        if (next_cursor == 0):
            break
    return results


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
    # Save users list of dicts to a users.json file
    with open(filename, 'a+') as fout:
        json.dump(users, fout)
    

def read_users_from_json(filename):
    with open(filename, 'r+') as fin:
        return json.load(fin)


def main():
    # 0 - Create twitter connection
    twitter = get_twitter('twitter.cfg')
    print('Established Twitter connection.')
    
    # 1 - Read the screen names we want to build the network from.
    screen_names = read_screen_names('ethereum-accounts.txt')
    print('Read screen names: %s' % screen_names)
    
    # 2 - Get the user's twitter accounts
    users = sorted(get_users_by_screen_name(twitter, screen_names), key=lambda x: x['screen_name'])
    print('found %d users with screen_names %s' %
          (len(users), str([u['screen_name'] for u in users])))
        
    # 3 - Get the user's each of this user follows (their "friends")
    # Obtain all friends
    add_all_friends(twitter, users)
    print('Friends per candidate:')
    print_num_friends(users)
    friend_counts = count_friends(users)
    print('Most common friends:\n%s' % str(friend_counts.most_common(5)))
    
    # Who follows this person?
    # Pick the first 5.000 people that follow this person.
    # 4 - Get the user's that follow this user(their "followers")
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
    
    
    # 5 - For each of the most common 100 users, obtain the user object and append it to the list of users' dict.
    new_users = get_users_by_ids(twitter, most_common_ids)
    print('found %d users with screen_names \n%s' %
        (len(new_users), str([u['screen_name'] for u in new_users])))
    
    # 6 - Find the friends and followers for each of the 100 most common followed users.
    add_all_friends(twitter, new_users)
    add_all_followers(twitter, new_users)
    
    # 7 - Add new_users to the initial users list and store it in the file users.json
    users_total = users + new_users
    print(len(users_total)) # Obtain total number of users to store
    store_users(users_total, 'data/collect/users.json')
    users_read = read_users_from_json('data/collect/users.json')
    print(len(users_read)) # Check if len the read users equals the total users stored


if __name__ == "__main__":
    main()