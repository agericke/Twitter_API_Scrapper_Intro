"""
Classify data.
"""
# Guessing gender
# Collect 1500 tweets matching words related to Blockchain
import configparser
import sys
import re
import pickle
from itertools import product
from collections import defaultdict
from collections import Counter
from scipy.sparse import lil_matrix
from sklearn.model_selection import KFold
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
import numpy as np
from TwitterAPI import TwitterAPI
import matplotlib.pyplot as plt


def read_census_names():
    """
    Read census names collected in the collect python script.

    Returns:
        Two lists of male_names and female_names
    """
    male_names = pickle.load(open('data/collect/male_names.pkl', 'rb'))
    female_names = pickle.load(open('data/collect/female_names.pkl', 'rb'))
    return male_names, female_names


def read_real_time_tweets(filename):
    """Read real time tweets retrieved during collect phase
    
    Params:
        filename.....The file where the tweets are stored.
    Returns:
        The list of real time tweets
    """
    return pickle.load(open(filename, 'rb'))


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


def tokenize(string, lowercase, keep_punctuation, prefix, collapse_urls, collapse_mentions):
    """ 
    Split a string into tokens.
    If keep_internal_punct is False, then return only the alphanumerics (letters, numbers and underscore).
    If keep_internal_punct is True, then also retain punctuation that
    is inside of a word. E.g., in the example below, the token "isn't"
    is maintained when keep_internal_punct=True; otherwise, it is
    split into "isn" and "t" tokens
    
    Params:
        string................The string that needs to be tokenized.
        lowercase.............Boolean indicating if we want the text to be convert to lowercase.
        keep_punctuation......Boolean indicating if we want to keep punctuation
        prefix................Prefix to add to each obtained token. (will use for identifying what part is being tokenized, e.g. prefix d= for description)
        collapse_urls.........Boolean indicating if we ant to collapse the urls in the text. (e.g. @something)
        collapse_meentions....Boolean indicating if we ant to collapse the mmentions in the text. (e.g. #smth)
    Returns:
        An array containing the tokenized string.
    """
    if not string:
        return []
    if lowercase:
        string = string.lower()
    tokens = []
    if collapse_urls:
        string = re.sub('http\S+', 'THIS_IS_A_URL', string)
    if collapse_mentions:
        string = re.sub('@\S+', 'THIS_IS_A_MENTION', string)
    if keep_punctuation:
        tokens = string.split()
    else:
        tokens = re.sub('\W+', ' ', string).split()
    if prefix:
        tokens = ['%s%s' % (prefix, t) for t in tokens]
    return tokens


def tweet2tokens(tweet, use_descr=True, lowercase=True, keep_punctuation=True, descr_prefix='d=', collapse_urls=True, collapse_mentions=True):
    """
    Convert a tweet into a list of tokens, from the tweet text and optionally the
    user description.
    
    Params:
        tweet.................The tweet that needs to be tokenized.
        user_descr............Boolean to indicate if we want to tokenize the user description too.
        lowercase.............Boolean indicating if we want the text to be convert to lowercase.
        keep_punctuation......Boolean indicating if we want to keep punctuation
        descr_prefix..........Prefix to add to the tokenization of the description.
        collapse_urls.........Boolean indicating if we ant to collapse the urls in the text. (e.g. @something)
        collapse_meentions....Boolean indicating if we ant to collapse the mmentions in the text. (e.g. #smth)
    """
    # When tokenizing the text, do not add any prefix.
    tokens = tokenize(tweet['text'], lowercase, keep_punctuation, None, collapse_urls, collapse_mentions)
    if use_descr:
        tokens.extend(tokenize(tweet['user']['description'], lowercase, keep_punctuation, descr_prefix,
                               collapse_urls, collapse_mentions))
    return tokens


def generate_all_opts():
    """
    Enumerate all possible classifier settings and compute.
    """
    use_descr_opts = [True, False]
    lowercase_opts = [True, False]
    keep_punctuation_opts = [True, False]
    descr_prefix_opts = ['d=', '']
    url_opts = [True, False]
    mention_opts = [True, False]
    argnames = ['use_descr', 'lower', 'punct', 'prefix', 'url', 'mention']
    option_iter = product(use_descr_opts, lowercase_opts, keep_punctuation_opts,
                       descr_prefix_opts, url_opts, mention_opts)
    
    return argnames, option_iter


def make_vocabulary(tokens_list):
    vocabulary = defaultdict(lambda: len(vocabulary))
    for tokens in tokens_list:
        for token in tokens:
            vocabulary[token]
    return vocabulary

 
def make_feature_matrix(tweets, tokens_list, vocabulary):
    X = lil_matrix((len(tweets), len(vocabulary)))
    for i, tokens in enumerate(tokens_list):
        for token in tokens:
            if token in vocabulary.keys():
                j = vocabulary[token]
                X[i,j] += 1
    return X.tocsr()


def get_gender(tweet, male_names, female_names):
    # Let 1=Female, 0=Male.
    name = get_first_name(tweet)
    if name in female_names:
        return 1
    elif name in male_names:
        return 0
    else:
        return -1


def do_cross_val(X, y, nfolds=5):
    """
    Compute the average testing accuracy over k folds of cross-validation.
    Params:
      X........A csr_matrix of features.
      y........The true labels for each instance in X
      nfolds...The number of cross-validation folds.

    Returns:
      The average testing accuracy of the classifier
      over each fold of cross-validation.
    """
    cv = KFold(n_splits=nfolds, random_state=42, shuffle=True)
    accuracies = []
    for train_idx, test_idx in cv.split(X):
        clf = LogisticRegression()
        clf.fit(X[train_idx], y[train_idx])
        predicted = clf.predict(X[test_idx])
        acc = accuracy_score(y[test_idx], predicted)
        accuracies.append(acc)
    avg = np.mean(accuracies)
    return avg


def run_all(tweets, labels, use_descr=True, lowercase=True, keep_punctuation=True, descr_prefix=None,
            collapse_urls=True, collapse_mentions=True):
    
    tokens_list = [tweet2tokens(t, use_descr, lowercase, keep_punctuation, descr_prefix,
                            collapse_urls, collapse_mentions) for t in tweets]
    vocabulary = make_vocabulary(tokens_list)
    X = make_feature_matrix(tweets, tokens_list, vocabulary)
    acc = do_cross_val(X, labels, 5)
    return acc


def eval_all_combinations(tweets, labels):
    results = []
    argnames, option_iter = generate_all_opts()
    for options in option_iter:
        acc = run_all(tweets, labels, *options)
        options_parsed_dict = {name: opt for name, opt in zip(argnames, options)}
        results.append((acc, options_parsed_dict))
    results_sorted = sorted(results, key=lambda x: -x[0])
    return results_sorted


def plot_sorted_accuracies(results, filename):
    """
    Plot all accuracies from the result of eval_all_combinations
    in ascending order of accuracy.
    Save to "accuracies.png".
    """
    accuracies = [res_tuple[0] for res_tuple in results]
    plt.figure()
    plt.plot(sorted(accuracies))
    plt.xlabel('setting')
    plt.ylabel('accuracy')
    plt.savefig(filename)


def mean_accuracy_per_setting(results):
    """
    To determine how important each model setting is to overall accuracy,
    we'll compute the mean accuracy of all combinations with a particular
    setting.

    Params:
      results...The output of eval_all_combinations
    Returns:
      A list of (accuracy, setting) tuples, SORTED in
      descending order of accuracy.
    """
    appearances = defaultdict(lambda: 0)
    setting_total = Counter()
    
    for result_tuple in results:
        accuracy = result_tuple[0]
        for key,value in result_tuple[1].items():
            if key != 'accuracy':
                appearances["%s=%s" % (key,value)] += accuracy
                setting_total.update(["%s=%s" % (key,value)])
    
    for key,value in appearances.items():
        appearances[key] = value/setting_total[key]
        
    ret = [(value, key) for key,value in appearances.items()]
    
    return sorted(ret, key=lambda x:-x[0])


def fit_best_classifier(tweets, labels, best_result):
    """
    Using the best setting from eval_all_combinations,
    re-vectorize all the training data and fit a
    LogisticRegression classifier to all training data.
    (i.e., no cross-validation done here)

    Params:
      docs..........List of training document strings.
      labels........The true labels for each training document (0 or 1)
      best_result...Element of eval_all_combinations
                    with highest accuracy
    Returns:
      clf.....A LogisticRegression classifier fit to all
            training data.
      vocab...The dict from feature name to column index.
    """
    tokens_list = [tweet2tokens(t, best_result[1]['use_descr'], best_result[1]['lower'], best_result[1]['punct'], 
                                best_result[1]['prefix'], best_result[1]['url'], best_result[1]['mention']) for t in tweets]
    vocabulary = make_vocabulary(tokens_list)
    X = make_feature_matrix(tweets, tokens_list, vocabulary)
    model = LogisticRegression()
    model.fit(X, labels)
    return model, vocabulary
    

def top_coefs(clf, label, n, vocab):
    """
    Find the n features with the highest coefficients in
    this classifier for this label.
    See the .coef_ attribute of LogisticRegression.

    Params:
      clf.....LogisticRegression classifier
      label...1 or 0; if 1, return the top coefficients
              for the female class; else for male.
      n.......The number of coefficients to return.
      vocab...Dict from feature name to column index.
    Returns:
      List of (feature_name, coefficient) tuples, SORTED
      in descending order of the coefficient for the
      given class label.
    """
    coef = clf.coef_[0]
    if label==1:
        # Sort them in descending order.
        top_coef_ind = np.argsort(coef)[::-1][:n]
    else:
        top_coef_ind = np.argsort(coef)[:n]
    
    # Get the names of those features.
    idx2word = dict((v,k) for k,v in vocab.items())
    top_coef_terms = [idx2word[i] for i in top_coef_ind]
    # Get the weights of those features
    top_coef = coef[top_coef_ind]
    return [x for x in zip(top_coef_terms, top_coef)]


def get_test_gender(tweet):
    """
    Get the gender stored in a tweet
    """
    return tweet['user']['gender']
    
    
def parse_test_data(best_result, vocabulary):
    """
    Using the vocabulary fit to the training data, read
    and vectorize the testing data. Note that vocab should
    be passed to the vectorize function to ensure the feature
    mapping is consistent from training to testing.

    Note: use read_data function defined above to read the
    test data.

    Params:
      best_result...Element of eval_all_combinations
                    with highest accuracy
      vocabulary....dict from feature name to column index,
                    built from the training data.
    Returns:
      test_tweets.....List of strings, one per testing document,
                    containing the raw.
      test_labels...List of ints, one per testing document,
                    1 for positive, 0 for negative.
      X_test........A csr_matrix representing the features
                    in the test data. Each row is a document,
                    each column is a feature.
    """
    test_tweets = pickle.load(open('data/collect/real-time-tweets-test-dataset.pkl', 'rb'))
    test_labels = np.array([get_test_gender(t) for t in test_tweets])
    tokens_list = [tweet2tokens(t, best_result[1]['use_descr'], best_result[1]['lower'], best_result[1]['punct'], 
                                best_result[1]['prefix'], best_result[1]['url'], best_result[1]['mention']) for t in test_tweets]
    X_test = make_feature_matrix(test_tweets, tokens_list, vocabulary)    
    return test_tweets, test_labels, X_test
    

def print_top_misclassified(test_tweets, test_labels, X_test, clf, n):
    """
    Print the n testing documents that are misclassified by the
    largest margin. By using the .predict_proba function of
    LogisticRegression <https://goo.gl/4WXbYA>, we can get the
    predicted probabilities of each class for each instance.
    We will first identify all incorrectly classified documents,
    then sort them in descending order of the predicted probability
    for the incorrect class.
    E.g., if document i is misclassified as positive, we will
    consider the probability of the positive class when sorting.

    Params:
      test_docs.....List of strings, one per test document
      test_labels...Array of true testing labels
      X_test........csr_matrix for test data
      clf...........LogisticRegression classifier fit on all training
                    data.
      n.............The number of documents to print.

    Returns:
      Nothing; see Log.txt for example printed output.
    """
    predictions = clf.predict(X_test)
    errors_ind = np.where(test_labels!=predictions)[0]
    proba_vals = clf.predict_proba(X_test)[errors_ind]
    wrong_tweets = []
    for idx in errors_ind:
        wrong_tweets.append(test_tweets[idx])
    predictions = predictions[errors_ind]
    test_labels = test_labels[errors_ind]
    
    proba_vals_class = [elem[0][elem[1]] for elem in zip(proba_vals, predictions)]
    
    # Sort them in descending order.
    sort_ind = np.argsort(proba_vals_class)[::-1][:n]
   
    for i in sort_ind:
        wrong_tweet = wrong_tweets[i]
        print("truth=%d predicted=%d proba=%6f name=%s description=%s" % (test_labels[i], predictions[i], proba_vals_class[i], wrong_tweet['user']['name'], wrong_tweet['user']['description']))


def main():
	
	# 0 - Establish twitter connection and read all the names picked from the U.S. census.
    male_names, female_names = read_census_names()
    print('found %d female and %d male names' % (len(female_names), len(male_names)))

	# 1 - Retrieve the real time tweets
    filename = 'data/collect/real-time-tweets.pkl'
    tweets = read_real_time_tweets(filename)
    print('Read %d tweets for training data' % len(tweets))
    print('top names:', Counter(get_first_name(t) for t in tweets).most_common(10))


    # 2 - Obtain accuracies for all possible options
    labels = np.array([get_gender(t, male_names, female_names) for t in tweets])
    argnames, option_iter = generate_all_opts()
    results_sorted  = eval_all_combinations(tweets, labels)
    

    # 3- Print information about these results.
    best_result = results_sorted[0]
    best_result_opt = []
    for name, opt in best_result[1].items():
        best_result_opt.extend([str(name)+"="+str(opt)])
    worst_result = results_sorted[-1]
    worst_result_opt = []
    for name, opt in worst_result[1].items():
        worst_result_opt.extend([str(name)+"="+str(opt)])
    print('best cross-validation result:\n%s\nwith options\n%s' % (str(best_result[0]), best_result_opt))
    print("\n")
    print('worst cross-validation result:\n%s\nwith options\n%s' % (str(worst_result[0]), worst_result_opt))
    
    filename = 'images/classify/accuracies.png'
    plot_sorted_accuracies(results_sorted, filename)
    print("Sorted accuracies plot saved to %s" % filename)
    
    print('\nMean Accuracies per Setting:')
    print('\n'.join(['%s: %.5f' % (s,v) for v,s in mean_accuracy_per_setting(results_sorted)]))

    # 4 - Fit best classifier.
    clf, vocabulary = fit_best_classifier(tweets, labels, best_result)

    # 5 - Print top coefficients per class.
    print('\nTOP COEFFICIENTS PER CLASS:')
    print('Male tokens:')
    print('\n'.join(['%s: %.5f' % (t,v) for t,v in top_coefs(clf, 0, 5, vocabulary)]))
    print('\nFemale tokens:')
    print('\n'.join(['%s: %.5f' % (t,v) for t,v in top_coefs(clf, 1, 5, vocabulary)]))

    # 6 -Parse test data
    test_tweets, test_labels, X_test = parse_test_data(best_result, vocabulary)

    test_counter = Counter(test_labels)
    print("Number of female instances %d" % test_counter[1])
    male_instances = sum(test_counter[1])
    print("Number of male instances %d" % test_counter[0])
    # Evaluate on test set.
    predictions = clf.predict(X_test)
    print('testing accuracy=%f' % accuracy_score(test_labels, predictions))

    print('\nTOP MISCLASSIFIED TEST DOCUMENTS:')
    print_top_misclassified(test_tweets, test_labels, X_test, clf, 5)


if __name__ == "__main__":
    main()