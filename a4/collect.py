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

    Here's a doctest to confirm your implementation is correct.
    >>> read_screen_names('candidates.txt')
    ['DrJillStein', 'GovGaryJohnson', 'HillaryClinton', 'realDonaldTrump']
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
    ### TODO:
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

    >>> twitter = get_twitter()
    >>> users = get_users(twitter, ['twitterapi', 'twitter'])
    >>> [u['id'] for u in users]
    [6253282, 783214]
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

    In this test case, I return the first 5 accounts that I follow.
    >>> twitter = get_twitter()
    >>> get_friends(twitter, 'aronwc')[:5]
    [695023, 1697081, 8381682, 10204352, 11669522]
    """
    print("Inside: Requesting friends for screen_name %s" % screen_name)
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

    >>> twitter = get_twitter()
    >>> users = [{'screen_name': 'aronwc'}]
    >>> add_all_friends(twitter, users)
    >>> users[0]['friends'][:5]
    [695023, 1697081, 8381682, 10204352, 11669522]
    """
    print("Requesting friends for a total of %s users" % len(users))
    for u in users:
        print("Outside: Requesting friends for screen_name %s" % u['screen_name'])
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
        Counter documentation: https://docs.python.org/dev/library/collections.html#collections.Counter

    In this example, friend '2' is followed by three different users.
    >>> c = count_friends([{'friends': [1,2]}, {'friends': [2,3]}, {'friends': [2,3]}])
    >>> c.most_common()
    [(2, 3), (3, 2), (1, 1)]
    """
    result = Counter()
    for u in users:
        result.update(u['friends'])
    return result


def get_followers(twitter, screen_name):
    """ Return a list of Twitter IDs for users that follow this person, up to 2000.
    See https://developer.twitter.com/en/docs/accounts-and-users/follow-search-get-users/api-reference/get-followers-list

    Args:
        twitter.......The TwitterAPI object
        screen_name... a string of a Twitter screen name
    Returns:
        A list of ints, one per friend ID, sorted in ascending order.

    Note: If a user has more than 5000 followers, we will limit ourselves to
    the first 5000 accounts returned.

    In this test case, I return the first 5 accounts that I follow.
    >>> twitter = get_twitter()
    >>> get_friends(twitter, 'aronwc')[:5]
    [695023, 1697081, 8381682, 10204352, 11669522]
    """
    print("Inside: Requesting followers for screen_name %s" % screen_name)
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

    >>> twitter = get_twitter()
    >>> users = [{'screen_name': 'aronwc'}]
    >>> add_all_followers(twitter, users)
    >>> users[0]['followers'][:5]
    [695023, 1697081, 8381682, 10204352, 11669522]
    """
    for u in users:
        print("Outside: Requesting followers for screen_name %s" % u['screen_name'])
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
        Counter documentation: https://docs.python.org/dev/library/collections.html#collections.Counter

    In this example, friend '2' is followed by three different users.
    >>> c = count_friends([{'friends': [1,2]}, {'friends': [2,3]}, {'friends': [2,3]}])
    >>> c.most_common()
    [(2, 3), (3, 2), (1, 1)]
    """
    ###TODO
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

    >>> twitter = get_twitter()
    >>> users = get_users(twitter, ['twitterapi', 'twitter'])
    >>> [u['id'] for u in users]
    [6253282, 783214]
    """
    results = robust_request(twitter, "users/lookup", {'user_id': ids})
    return sorted(results.json(), key=lambda x: x['screen_name'])


def store_users(users, file):
    # Save users list of dicts to a users.json file
    with open(file, 'a+') as fout:
        json.dump(users, fout)
    

def read_users_from_json(file):
    with open(file, 'r') as fin:
        return json.load(fin)


#def friend_overlap(users):
#    """
#    Compute the number of shared accounts followed by each pair of users.
#
#    Args:
#        users...The list of user dicts.
#
#    Return: A list of tuples containing (user1, user2, N), where N is the
#        number of accounts that both user1 and user2 follow.  This list should
#        be sorted in descending order of N. Ties are broken first by user1's
#        screen_name, then by user2's screen_name (sorted in ascending
#        alphabetical order). See Python's builtin sorted method.
#
#    In this example, users 'a' and 'c' follow the same 3 accounts:
#    >>> friend_overlap([
#    ...     {'screen_name': 'a', 'friends': ['1', '2', '3']},
#    ...     {'screen_name': 'b', 'friends': ['2', '3', '4']},
#    ...     {'screen_name': 'c', 'friends': ['1', '2', '3']},
#    ...     ])
#    [('a', 'c', 3), ('a', 'b', 2), ('b', 'c', 2)]
#    """
#    ###TODO
#    # l = []
#    # actual = 0
#    # for u in users:
#    #     users_comparation = users[actual:(len(users)-1)]
#
#    #     for friend in u['friends']:
#    #         if friend == 
#    result = []
#    for i, u1 in enumerate(users):
#        for j, u2 in enumerate(users[i+1:]):
#            overlap = len(set(u1['friends']) & set(u2['friends']))
#            results.append((u1['screen_name'], u2['screen_name'], overlap))
#        return sorted(results, key=lambda x: (-x[2], x[0], x[1]))
#
#def followed_by_hillary_and_donald(users, twitter):
#    """
#    Find and return the screen_names of the Twitter users followed by both Hillary
#    Clinton and Donald Trump. You will need to use the TwitterAPI to convert
#    the Twitter ID to a screen_name. See:
#    https://dev.twitter.com/rest/reference/get/users/lookup
#
#    Params:
#        users.....The list of user dicts
#        twitter...The Twitter API object
#    Returns:
#        A list of strings containing the Twitter screen_names of the users
#        that are followed by both Hillary Clinton and Donald Trump.
#    """
#    ###TODO
##    dt_friends = get_friends(twitter, 'realDonaldTrump')
##    hc_friends = get_friends(twitter, 'HillaryClinton')
##
##    result = []
##    ids = [user['id'] for user in users]
##    def i2dscreen():
#    pass
#
#
#
#def create_graph(users, friend_counts):
#    """ Create a networkx undirected Graph, adding each candidate and friend
#        as a node.  Note: while all candidates should be added to the graph,
#        only add friends to the graph if they are followed by more than one
#        candidate. (This is to reduce clutter.)
#
#        Each candidate in the Graph will be represented by their screen_name,
#        while each friend will be represented by their user id.
#
#    Args:
#      users...........The list of user dicts.
#      friend_counts...The Counter dict mapping each friend to the number of candidates that follow them.
#    Returns:
#      A networkx Graph
#    """
#    ###TODO
#    # Create a graph
#    graph = nx.Graph()
#    friends = Counter()
#    for u in users:
#        graph.add_node(u['screen_name'])
#        friends = u['friends']
#        for f in friends:
#            if (friend_counts.get(f)>1):
#                graph.add_edge(u['screen_name'], f)
#    return graph
#
#
#def draw_network(graph, users, filename):
#    """
#    Draw the network to a file. Only label the candidate nodes; the friend
#    nodes should have no labels (to reduce clutter).
#
#    Methods you'll need include networkx.draw_networkx, plt.figure, and plt.savefig.
#
#    Your figure does not have to look exactly the same as mine, but try to
#    make it look presentable.
#    """
#    ###TODO
#    pass

    
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
    # Pick the 100 most common followers and users
    most_common_100 = friend_and_followers_counts.most_common(100)
    print('Most common friends and followers:\n%s' % str(friend_and_followers_counts.most_common(5)))
    # Store in a list all the id's of the 100 most common users
    most_common_100_ids = [user_tuple[0] for user_tuple in most_common_100]
    
    
    # 5 - For each of the most common 100 users, obtain the user object and append it to the list of users' dict.
    new_users = get_users_by_ids(twitter, most_common_100_ids)
    print('found %d users with screen_names %s' %
        (len(new_users), str([u['screen_name'] for u in new_users])))
    
    # 6 - Find the friends and followers for each of the 100 most common followed users.
    add_all_friends(twitter, new_users)
    add_all_followers(twitter, new_users)
    
    # 7 - Add new_users to the initial users list and store it in the file users.json
    users_total = users + new_users
    print(len(users_total)) # Obtain total number of users to store
    store_users(users_total, 'users.json')
    users_read = read_users_from_json('users.json')
    print(len(users_read)) # Check if len the read users equals the total users stored


if __name__ == "__main__":
    main()