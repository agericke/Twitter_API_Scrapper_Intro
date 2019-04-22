"""
Collect data.

First we will get all the accounts form the file accounts.txt, the followers for this accounts and their frineds.
Then we will collect a toal of a 500 tweets that mention each account. For all those 500 tweets we will obtain
the screen_namefor each tweet and the friends for each screen_name.
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


# I've provided the method below to handle Twitter's rate limiting.
# You should call this method whenever you need to access the Twitter API.
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
        if request.status_code == 200:
            return request
        else:
            print('Got error %s \nsleeping for 15 minutes.' % request.text)
            sys.stderr.flush()
            time.sleep(61 * 15)


def get_users(twitter, screen_names):
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
    ###TODO
    results = []
    for s in screen_names:
        results.extend(robust_request(twitter, "users/lookup", {'screen_name': s}))
    return results

def get_friends(twitter, screen_name):
    """ Return a list of Twitter IDs for users that this person follows, up to 5000.
    See https://dev.twitter.com/rest/reference/get/friends/ids

    Note, because of rate limits, it's best to test this method for one candidate before trying
    on all candidates.

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
    ###TODO
    results = []
    request = robust_request(twitter, "friends/ids", 
                              {'screen_name': screen_name, 'count':5000})
    return sorted(request.json()['ids'])

def add_all_friends(twitter, users):
    """ Get the list of accounts each user follows.
    I.e., call the get_friends method for all 4 candidates.

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
    ###TODO
    for u in users:
        u['friends'] = get_friends(twitter, u['screen_name'])


def print_num_friends(users):
    """Print the number of friends per candidate, sorted by candidate name.
    See Log.txt for an example.
    Args:
        users....The list of user dicts.
    Returns:
        Nothing
    """
    ###TODO
    for u in users:
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
    ###TODO
    result = Counter()
    for u in users:
        result.update(u['friends'])
    return result 


def friend_overlap(users):
    """
    Compute the number of shared accounts followed by each pair of users.

    Args:
        users...The list of user dicts.

    Return: A list of tuples containing (user1, user2, N), where N is the
        number of accounts that both user1 and user2 follow.  This list should
        be sorted in descending order of N. Ties are broken first by user1's
        screen_name, then by user2's screen_name (sorted in ascending
        alphabetical order). See Python's builtin sorted method.

    In this example, users 'a' and 'c' follow the same 3 accounts:
    >>> friend_overlap([
    ...     {'screen_name': 'a', 'friends': ['1', '2', '3']},
    ...     {'screen_name': 'b', 'friends': ['2', '3', '4']},
    ...     {'screen_name': 'c', 'friends': ['1', '2', '3']},
    ...     ])
    [('a', 'c', 3), ('a', 'b', 2), ('b', 'c', 2)]
    """
    ###TODO
    # l = []
    # actual = 0
    # for u in users:
    #     users_comparation = users[actual:(len(users)-1)]

    #     for friend in u['friends']:
    #         if friend == 
    result = []
    for i, u1 in enumerate(users):
        for j, u2 in enumerate(users[i+1:]):
            overlap = len(set(u1['friends']) & set(u2['friends']))
            results.append((u1['screen_name'], u2['screen_name'], overlap))
        return sorted(results, key=lambda x: (-x[2], x[0], x[1]))

def followed_by_hillary_and_donald(users, twitter):
    """
    Find and return the screen_names of the Twitter users followed by both Hillary
    Clinton and Donald Trump. You will need to use the TwitterAPI to convert
    the Twitter ID to a screen_name. See:
    https://dev.twitter.com/rest/reference/get/users/lookup

    Params:
        users.....The list of user dicts
        twitter...The Twitter API object
    Returns:
        A list of strings containing the Twitter screen_names of the users
        that are followed by both Hillary Clinton and Donald Trump.
    """
    ###TODO
#    dt_friends = get_friends(twitter, 'realDonaldTrump')
#    hc_friends = get_friends(twitter, 'HillaryClinton')
#
#    result = []
#    ids = [user['id'] for user in users]
#    def i2dscreen():
    pass



def create_graph(users, friend_counts):
    """ Create a networkx undirected Graph, adding each candidate and friend
        as a node.  Note: while all candidates should be added to the graph,
        only add friends to the graph if they are followed by more than one
        candidate. (This is to reduce clutter.)

        Each candidate in the Graph will be represented by their screen_name,
        while each friend will be represented by their user id.

    Args:
      users...........The list of user dicts.
      friend_counts...The Counter dict mapping each friend to the number of candidates that follow them.
    Returns:
      A networkx Graph
    """
    ###TODO
    # Create a graph
    graph = nx.Graph()
    friends = Counter()
    for u in users:
        graph.add_node(u['screen_name'])
        friends = u['friends']
        for f in friends:
            if (friend_counts.get(f)>1):
                graph.add_edge(u['screen_name'], f)
    return graph


def draw_network(graph, users, filename):
    """
    Draw the network to a file. Only label the candidate nodes; the friend
    nodes should have no labels (to reduce clutter).

    Methods you'll need include networkx.draw_networkx, plt.figure, and plt.savefig.

    Your figure does not have to look exactly the same as mine, but try to
    make it look presentable.
    """
    ###TODO
    pass

    


#def main():
#    """ Main method. You should not modify this. """
#    twitter = get_twitter()
#    screen_names = read_screen_names('candidates.txt')
#    print('Established Twitter connection.')
#    print('Read screen names: %s' % screen_names)
#    users = sorted(get_users(twitter, screen_names), key=lambda x: x['screen_name'])
#    print('found %d users with screen_names %s' %
#          (len(users), str([u['screen_name'] for u in users])))
#    print(users)
#    prof_friends = get_friends(twitter, 'aronwc')
#    print('Complete response')
#    print(prof_friends)
#    [695023, 1697081, 8381682, 10204352, 11669522]
#    add_all_friends(twitter, users)
#    print('Friends per candidate:')
#    print_num_friends(users)
#    friend_counts = count_friends(users)
#    print('Most common friends:\n%s' % str(friend_counts.most_common(5)))
#    print('Friend Overlap:\n%s' % str(friend_overlap(users)))
#    print('User followed by Hillary and Donald: %s' % str(followed_by_hillary_and_donald(users, twitter)))
#
#    graph = create_graph(users, friend_counts)
#    print('graph has %s nodes and %s edges' % (len(graph.nodes()), len(graph.edges())))
#    draw_network(graph, users, 'network.png')
#    print('network drawn to network.png')


# That's it for now! This should give you an introduction to some of the data we'll study in this course.

def main():
    twitter = get_twitter('./twitter.cfg')
    screen_names = read_screen_names('ethereum-accounts.txt')
    print('Established Twitter Connection.')
    print('Read screen names: %s' % screen_names)
    users = sorted(get_users(twitter, screen_names), key=lambda x: x['screen_name'].lower())
    print('found %d users with screen_names %s' %
          (len(users), str([u['screen_name'] for u in users])))
    print(users)

if __name__ == "__main__":
    main()