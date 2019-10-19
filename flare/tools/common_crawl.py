import requests
import zlib
import os

import pandas as pd

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))

CHUNKSIZE = 1024
CC_URL = 'https://commoncrawl.s3.amazonaws.com/projects/hyperlinkgraph/cc-main-2018-19-nov-dec-jan/domain/cc-main-2018-19-nov-dec-jan-domain-ranks.txt.gz'

# The entire gz file in `CC_URL` is around 4GB. So we opt to stream and 
# decompress in chunks to get the first N rows of the file

def get_chunks(r):
    for chunk in r.iter_content(chunk_size=CHUNKSIZE): 
        if chunk: yield chunk

def get_decompressed_chunks(r):
    decomp = zlib.decompressobj(16+zlib.MAX_WBITS)
    for chunk in get_chunks(r):
        yield decomp.decompress(chunk)
        
def get_lines(r):
    prev = b''
    for chunk in get_decompressed_chunks(r):
        prev += chunk
        lines = prev.split(b'\n')
        for l in lines[:-1]:
            yield l
        prev = lines[-1]

def reverse_domain(x):
    return '.'.join(reversed(x.split('.')))
  

def fetch_common_crawl(n = 1000000):
    """Fetches the domain ranks of the common-crawl based on the 
    recent (Nov/Dec/Jan 2018 – 2019) common-crawl web graphs. 

    See https://commoncrawl.org/2019/02/host-and-domain-level-web-graphs-nov-dec-2018-jan-2019/
    
    Here are some of the main columns of the resulting data frame:
    - harmonicc_val: The harmonic centrality measure of the domain
    - pr_val: The page rank value of the domain
    - n_host: The number of unique hosts encountered on the domain
        during the crawl

    The max number of rows returned are 90M.
    
    n (int): Limits the resulting dataframe to the first `n` domains 
        returned by the commmon crawl list
    RETURNS (pandas.DataFrame): A DataFrame of the top `n` domains
        with all the columns of the common-crawl domain stats.
    """
    data = []
    with requests.get(CC_URL, stream = True) as res:
        for idx, chunk in enumerate(get_lines(res)):
            if(idx > n): break
            row = chunk.decode('ascii').split('\t')
            data.append(row)
            
    df = pd.DataFrame(data[1:], columns=[e.strip('#') for e in data[0]])
    df['host'] = df['host_rev'].map(reverse_domain)
    df['harmonicc_pos'] = df['harmonicc_pos'].astype(int)
    df['harmonicc_val'] = df['harmonicc_val'].astype(float)
    df['pr_pos'] = df['pr_pos'].astype(int)
    df['pr_val'] = df['pr_val'].astype(float)
    df['n_hosts'] = df['n_hosts'].astype(int)
    return df


class CommonCrawl(object):
    CC_PATH = os.path.join(
        LOCAL_DIR, '..', 'data', 'common_crawl', 'common-crawl-1m.csv')

    def __init__(self, limit=1000000):
        self.limit = limit

        if limit > 1000000:
            cc_df = fetch_common_crawl(limit)[['host']]
        else:
            cc_df = pd.read_csv(self.CC_PATH).head(limit)

        self.CC_DOMAINS = set(cc_df['host'])

    def domain_in_cc(self, domain):
        return domain in self.CC_DOMAINS

    def __contains__(self, obj):
        return obj in self.CC_DOMAINS

