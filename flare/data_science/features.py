import math
import os
import re
import tldextract
import warnings
import numpy as np
import pandas as pd
from collections import Counter
from flare.tools.alexa import Alexa


import logging
logging.getLogger("tldextract").setLevel(logging.CRITICAL)


try:
    import sklearn
    from sklearn import ensemble
    from sklearn import feature_extraction
    from sklearn.model_selection import train_test_split
except:
    logging.error("""[-] Could not import sklearn! Some functions may not operate properly. 
        Please visit http://scikit-learn.org/stable/install.html for more information on scikit-learn""")
    pass


LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))


def entropy(s):
    p, lns = Counter(s), float(len(s))
    return -sum(count / lns * math.log(count / lns, 2) for count in list(p.values()))


def levenshtein(source, target):
    # Source
    # https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
    if len(source) < len(target):
        return levenshtein(target, source)

    # So now we have len(source) >= len(target).
    if len(target) == 0:
        return len(source)

    # We call tuple() to force strings to be used as sequences
    # ('c', 'a', 't', 's') - numpy uses them as values by default.
    source = np.array(tuple(source))
    target = np.array(tuple(target))

    # We use a dynamic programming algorithm, but with the
    # added optimization that we only need the last two rows
    # of the matrix.
    previous_row = np.arange(target.size + 1)
    for s in source:
        # Insertion (target grows longer than source):
        current_row = previous_row + 1

        # Substitution or matching:
        # Target and source items are aligned, and either
        # are different (cost of 1), or are the same (cost of 0).
        current_row[1:] = np.minimum(
            current_row[1:],
            np.add(previous_row[:-1], target != s))

        # Deletion (target grows shorter than source):
        current_row[1:] = np.minimum(
            current_row[1:],
            current_row[0:-1] + 1)

        previous_row = current_row

    return previous_row[-1]


def ip_matcher(address):
    # Used to validate if string is an ipaddress
    ip = re.match(
        '^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', address)
    if ip:
        return True
    else:
        return False


def domain_extract(uri):
    # Extracts domain, ex: www.google.com would return google
    try:
        ext = tldextract.extract(uri)
        if (not ext.suffix):
            return np.nan
        else:
            return ext.domain
    except:
        return ''


def domain_tld_extract(domain):
    # Extracts domain and TLD. subdomain.sub.google.com returns google.com
    t = domain.split('.')
    ip_check = ip_matcher(domain)
    if ip_check:
        return domain
    if len(t) > 2:
        domain = '.'.join(t[-2:])
    if len(t) == 2:
        domain = '.'.join(t)
    if ':' in domain:
        return domain.split(':')[0]
    else:
        return domain


def non_alnum_count(string):
    # Returns amount of non-alpha numeric characters
    alnum = 0
    for l in string:
        if l.isalnum() != True and l != ' ':
            alnum += 1
    return alnum


def first_char_check(word):
    # Returns True if the first char is alphanumeric.
    try:
        return word[0].isalnum()
    except:
        return np.nan


def last_char_check(word):
    # Returns True if the last char is alphanumeric.
    try:
        return word.strip()[-1].isalnum()
    except:
        return np.nan

#Real time DGA list: http://osint.bambenekconsulting.com/feeds/dga-feed.txt


class dga_classifier(object):

    def __init__(self):
        print('[*] Initializing... training classifier - Please wait.')
        self.a = Alexa()
        self.dga_path = os.path.join(
            LOCAL_DIR, '..', 'data', 'misc', 'dga_domains.txt')
        self.word_dict_path = os.path.join(
            LOCAL_DIR, '..', 'data', 'misc', 'words.txt')
        self.entropy = entropy
        self.domain_extract = domain_extract


        alexa_df = pd.DataFrame(list(self.a.DOMAINS_TOP1M))
        alexa_df.columns = ['uri']
        alexa_df['domain'] = [self.domain_extract(
            uri) for uri in alexa_df['uri']]
        alexa_df = alexa_df.dropna()
        alexa_df = alexa_df.drop_duplicates()
        alexa_df['class'] = 'legit'
        alexa_df = alexa_df.reindex(np.random.permutation(alexa_df.index))
        alexa_total = alexa_df.shape[0]
        alexa_df = alexa_df[:int(alexa_total * .9)]

        # Read in the DGA domains
        dga_df = pd.read_csv(self.dga_path, names=[
                             'raw_domain'], header=None, encoding='utf-8')

        # Blacklist values just differ by captilization or .com/.org/.info
        dga_df['domain'] = dga_df.applymap(
            lambda x: x.split('.')[0].strip().lower())

        # Cleanup any blank lines or dups
        dga_df = dga_df.dropna()
        dga_df = dga_df.drop_duplicates()
        dga_total = dga_df.shape[0]

        # Set Class
        dga_df['class'] = 'dga'

        # Hold out 10% of DGA
        dga_df = dga_df[:int(dga_total * .9)]

        # Merge Domains
        all_domains = pd.concat([alexa_df, dga_df], ignore_index=True)

        # Features
        all_domains['length'] = [len(x) for x in all_domains['domain']]
        all_domains = all_domains[all_domains['length'] > 6]
        all_domains['entropy'] = [self.entropy(
            x) for x in all_domains['domain']]

        self.clf = ensemble.RandomForestClassifier(n_estimators=20)

        self.alexa_vc = feature_extraction.text.CountVectorizer(
            analyzer='char', ngram_range=(3, 5), min_df=1e-4, max_df=1.0)
        counts_matrix = self.alexa_vc.fit_transform(alexa_df['domain'])
        self.alexa_counts = np.log10(counts_matrix.sum(axis=0).getA1())

        # Read in word dictionary for trigrams
        word_df = pd.read_csv(self.word_dict_path, names=['word'], header=None, dtype={
                              'word': np.str}, encoding='utf-8')
        word_df = word_df[word_df['word'].map(lambda x: str(x).isalpha())]
        word_df = word_df.applymap(lambda x: str(x).strip().lower())
        word_df = word_df.dropna()
        word_df = word_df.drop_duplicates()

        self.dict_vc = feature_extraction.text.CountVectorizer(
            analyzer='char', ngram_range=(3, 5), min_df=1e-5, max_df=1.0)
        counts_matrix = self.dict_vc.fit_transform(word_df['word'])
        self.dict_counts = np.log10(counts_matrix.sum(axis=0).getA1())

        all_domains['alexa_grams'] = self.alexa_counts * \
            self.alexa_vc.transform(all_domains['domain']).T
        all_domains['word_grams'] = self.dict_counts * \
            self.dict_vc.transform(all_domains['domain']).T
        all_domains['diff'] = all_domains[
            'alexa_grams'] - all_domains['word_grams']

        weird_cond = (all_domains['class'] == 'legit') & (
            all_domains['word_grams'] < 3) & (all_domains['alexa_grams'] < 2)
        #weird = all_domains[weird_cond]

        not_weird = all_domains[all_domains['class'] != 'weird']
        X = not_weird.as_matrix(
            ['length', 'entropy', 'alexa_grams', 'word_grams'])

        # Labels (scikit learn uses 'y' for classification labels)
        y = np.array(not_weird['class'].tolist())

        # Train on a 80/20 split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2)
        self.clf.fit(X_train, y_train)
        print('[+] Classifier Ready')

    def ngram_count(self, domain):
        # Multiply and transpose vector
        alexa_match = self.alexa_counts * self.alexa_vc.transform([domain]).T
        dict_match = self.dict_counts * self.dict_vc.transform([domain]).T
        print(('%s Alexa match: %d, Dict match: %d' % (domain, alexa_match, dict_match)))
        return domain, alexa_match, dict_match

    def predict(self, domain):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _alexa_match = self.alexa_counts * \
                self.alexa_vc.transform(
                    [domain]).T  # Matrix multiply and transpose
            _dict_match = self.dict_counts * self.dict_vc.transform([domain]).T
            _X = [len(domain), self.entropy(
                domain), _alexa_match, _dict_match]
            if int(sklearn.__version__.split('.')[1]) > 20:
                _X = [_X]
            return self.clf.predict(_X)[0]
