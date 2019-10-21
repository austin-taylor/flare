import os

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))

SUBDOMAINS_TOP1M_PATH = os.path.join(
    LOCAL_DIR, '..', 'data', 'alexa',
    'subdomains-top1mil.txt')

DOMAINS_TOP1M_PATH = os.path.join(
    LOCAL_DIR, '..', 'data',
    'alexa', 'top-1m.csv')


class Alexa(object):

    def __init__(self, limit=1000000):

        self.limit = limit
        self.SUBDOMAINS_TOP1M = frozenset(open(SUBDOMAINS_TOP1M_PATH).read().strip('\n').splitlines()[:self.limit])
        self.DOMAINS_TOP1M = frozenset(open(DOMAINS_TOP1M_PATH).read().strip('\n').splitlines()[:self.limit])

    def domain_in_alexa(self, word):
        return word in self.DOMAINS_TOP1M

    def subdomain_in_alexa(self, word):
        return word in self.SUBDOMAINS_TOP1M

    def __contains__(self, word):
        return self.domain_in_alexa(word)


# EXAMPLES

#alexa = Alexa(limit=100)
#print alexa.domain_in_alexa('google.com')
#print 'google.com' in alexa
#print alexa.subdomain_in_alexa('com')

#print alexa.DOMAINS_TOP1M
