import pandas as pd
import pickle as pickle
import os

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))


class majesticMillion(object):
    MAJESTIC_TOP1M_PATH = os.path.join(
        LOCAL_DIR, '..', 'data', 'majestic', 'majestic_million.pkl')
    MM_SOURCE = 'http://downloads.majestic.com/majestic_million.csv'

    def __init__(self, limit=1000000, verbose=True, update=True):
        self.update = update
        self.limit = limit
        self.verbose = verbose
        self.majestic_data = self.MAJESTIC_TOP1M_PATH
        self.MAJESTIC_DOMAINS = self.create_list()

    def vprint(self, msg):
        if self.verbose:
            print(msg)

    def update_majestic(self):
        mm = pd.read_csv('http://downloads.majestic.com/majestic_million.csv')
        if len(mm) != 0:
            self.vprint('[ACTION] Majestic Million updated with a limit of %s' % self.limit)
            self.MAJESTIC_DOMAINS = frozenset(mm[:self.limit].Domain.tolist())

    def create_list(self):
        if self.update:
            self.update_majestic()
            with open(self.MAJESTIC_TOP1M_PATH, 'wb') as handle:
                pickle.dump(self.MAJESTIC_DOMAINS, handle, protocol=pickle.HIGHEST_PROTOCOL)
        else:
            with open(self.MAJESTIC_TOP1M_PATH, 'rb') as handle:
                mm_set = pickle.load(handle)
                return mm_set

    def domain_in_majestic(self, domain):
        return domain in self.MAJESTIC_DOMAINS

    def __contains__(self, domain):
        return self.domain_in_majestic(domain)






