import os
import requests
import io
import zipfile
from flare.data_science.features import domain_tld_extract

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))

DOMAINS_TOP1M_PATH = os.path.join(
    LOCAL_DIR, '..', 'data', 'umbrella')

UMBRELLA_TOP1M = 'http://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip'


class Umbrella(object):
    def __init__(self, limit=1000000, update=True):

        self.limit = limit
        self.update = update

        if update:
            self.update_umbrella()
        else:
            self.DOMAINS_TOP1M = self.read_domains(os.path.join(DOMAINS_TOP1M_PATH, 'top-1m.csv'))
            self.DOMAINS_TLD_TOP1M = frozenset([domain_tld_extract(domain) for domain in self.DOMAINS_TOP1M])

    def read_domains(self, path):
        with open(path, 'r') as f:
            rows = f.read().splitlines()
        f.close()

        domains = frozenset([item.split(',')[1] for item in rows[:self.limit]])
        return domains

    def domain_in_umbrella(self, word):
        return word in self.DOMAINS_TOP1M

    def domain_tld_in_umbrella(self, word):
        return word in self.DOMAINS_TLD_TOP1M

    def update_umbrella(self):
        res = requests.get(UMBRELLA_TOP1M)
        if res.status_code == 200:
            zip_ref = zipfile.ZipFile(io.BytesIO(res.content), 'r')
            zip_ref.extractall(DOMAINS_TOP1M_PATH)
            zip_ref.close()

            self.DOMAINS_TOP1M = self.read_domains(os.path.join(DOMAINS_TOP1M_PATH, 'top-1m.csv'))
            self.DOMAINS_TLD_TOP1M = set([domain_tld_extract(domain) for domain in self.DOMAINS_TOP1M])

            print('[+] Updated Umbrella Top 1 Million list...')
            return True

        return False

    def __contains__(self, word):
        return self.domain_tld_in_umbrella(word)