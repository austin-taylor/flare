import os
import pandas as pd
import warnings
import sys

if (sys.version_info > (3, 0)):
    import pickle as pickle
else:
    import cPickle as pickle
import tldextract
warnings.filterwarnings("ignore", 'This pattern has match groups')


LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))


class TLDCheck(object):

    """
    Parses out TLD from domains and checks it against IANA.
    """
    TLD_SOURCE = 'http://data.iana.org/TLD/tlds-alpha-by-domain.txt'

    def __init__(self, update=False):
        """
        tld = TLDCheck()
        tld.tld_lookup('google.com')
        tld.tld_lookup('google.asdf')
        :param update: True will update the file with the most recent source
        """

        self.tld_list = os.path.join(LOCAL_DIR, '..', 'data', 'tld', 'tld_list.pkl')
        self.update = update
        self.tld_set = self.create_list()

    def parse_tld_suffix(self, domain):
        return tldextract.extract(domain).suffix

    def tld_lookup(self, tld):
        return self.parse_tld_suffix(tld).upper() in self.tld_set

    def create_list(self):
        if self.update:
            tld_file = pd.read_table(self.TLD_SOURCE,
                                     names=['tld_domain'], skiprows=1)

            tld_set = frozenset(tld_file.tld_domain.dropna().tolist())

            with open(self.tld_list, 'wb') as handle:
                pickle.dump(tld_set, handle, protocol=pickle.HIGHEST_PROTOCOL)
            return tld_set
        else:
            with open(self.tld_list, 'rb') as handle:
                tld_set = pickle.load(handle)
                return tld_set