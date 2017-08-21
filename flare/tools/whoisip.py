import pyasn
import json
import sys
import os
import argparse
import datetime
import logging
import lxml.html

if (sys.version_info > (3, 0)):
    from urllib.request import urlopen
    from html.parser import HTMLParser
    import pickle
else:
    from urllib2 import urlopen
    import cPickle as pickle
    from HTMLParser import HTMLParser

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))
LOG_PATH = os.path.join(LOCAL_DIR, '..','data', 'log.txt')



class WhoisLookup:
    """
    Utility which returns ip and asn information for provided domains
    """

    def __init__(self, asn_dat=None, asn_map=None):

        if asn_dat is not None:
            self.asndb = pyasn.pyasn(asn_dat)
        else:

            self.asndb = pyasn.pyasn(os.path.join(
                LOCAL_DIR, '..', 'data', 'whoisip', 'ipasn.dat'))

        if asn_map is not None:
            with open(asn_map, 'rb') as f:
                self.names = json.loads(f.read())
        else:
            pkl_path = os.path.join(
                LOCAL_DIR, '..', 'data', 'whoisip', 'asn_names.pkl')
            with open(pkl_path, 'rb') as f:
                if (sys.version_info > (3, 0)):
                    self.names = pickle.load(f, encoding='latin1')
                else:
                    self.names = pickle.load(f)

    def get_asn(self, ip):
        asn, netmask = self.asndb.lookup(ip)
        return asn

    def get_asn_netmask(self, ip):
        return self.asndb.lookup(ip)

    def get_name_by_ip(self, ip):
        try:
            asn = self.get_asn(ip)
            if str(asn) in self.names:
                return self.names[str(asn)]
            else:
                query_msg = "IP not found"
                return query_msg
        except ValueError:
            except_msg = "Invalid input"

            return except_msg

    def domain_in_ip_whois_match(self, domain, ip):
        """
        Takes a domain and IP address and
        compares if the IP WHOIS is in the domain description
        :param domain: domain description
        :param ip: IP address to check
        :return: domain_list or Exception e
        **REQUIRES DOMAIN TO BE BARE** www.google.com should be google**
        """
        try:
            domain_ip_desc = self.get_name_by_ip(ip).lower().split(' ')
            domain_list = domain.lower()
            return domain_list in domain_ip_desc
        except Exception as e:
            return e

    @staticmethod
    def create_new_asn_mapping(verbose=True):
        asnames_url = 'http://thyme.apnic.net/current/data-used-autnums'
        if verbose:
            print('Downloading asn names from http://thyme.apnic.net/current/data-used-autnums')
        http = urlopen(asnames_url)
        data = http.read()
        http.close()
        if verbose:
            print('Parsing asn file')
        asn_map = {}
        for line in data.split('\n'):
            if len(line) > 0:
                asn, description = line.strip().split(' ', 1)
                asn_map[asn] = description

        return asn_map

    @staticmethod
    def create_new_asn_mapping2(verbose=True):
        asnames_url = 'http://www.cidr-report.org/as2.0/autnums.html'
        if verbose:
            print('Downloading asn names from http://www.cidr-report.org/as2.0/autnums.html')
        http = urlopen(asnames_url)
        data = http.read()
        http.close()
        if verbose:
            print('Parsing asn file')

        parser = ASNHTMLParser()
        parser.feed(data)

        return parser.asn_map


class ASNHTMLParser(HTMLParser, object):

    def __init__(self):
        super(ASNHTMLParser, self).__init__()
        self.current_tag = None
        self.current_asn = None
        self.asn_map = {}

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.current_tag = tag

    def handle_endtag(self, tag):
        self.current_tag = None

    def handle_data(self, data):
        if self.current_tag == 'a' and data.startswith('AS'):
            self.current_asn = data[2:].strip()
        elif self.current_tag == None and self.current_asn != None:
            self.asn_map[self.current_asn] = data.strip('\n').strip(' ')
            self.current_asn = None


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(message)-30s %(asctime)s\n", "%Y-%m-%d   %H:%M:%S")
    file_handle = logging.FileHandler(LOG_PATH)
    file_handle.setFormatter(formatter)
    logger.addHandler(file_handle)

    logger.info('[UPDATE START]\t\t')
    logger.info('[STARTED] \t\twhoisip.py')
    try:
        parser = argparse.ArgumentParser(description='Whois IP Utilities')
        parser.add_argument('--asn_names', action='store_true',
                            dest='asn_names', default=False)
        args = parser.parse_args()
        if args.asn_names:
            # asn_map = WhoisLookup.create_new_asn_mapping(verbose=True)
            asn_map = WhoisLookup.create_new_asn_mapping2(verbose=True)

            now = datetime.datetime.now()
            file_name = os.path.join(LOCAL_DIR,'..','data','whoisip','asn_names.pkl')
            print('Saving %d entries to %s' % (len(asn_map.keys()), file_name))
            with open(file_name, 'wb') as f:
                pickle.dump(asn_map, f)

        today = datetime.datetime.now()
        if today.month < 10:
            month = '0'+str(today.month)
        else:
            month = str(today.month)
        datem = (str(today.year) + '.' + month)

        url = 'http://routeviews.org/bgpdata/%s/RIBS' % datem
        connection = urlopen(url)
        dom = lxml.html.fromstring(connection.read())
        all_files = []
        for link in dom.xpath('//a/@href'):
            if 'bz2' in link:
                all_files.append(link)
        latest_file = all_files[-1]

        url = urlopen(url + '/' + latest_file)

        rib_path = str(os.path.join(LOCAL_DIR,'..','data','whoisip' , latest_file))
        dat_path = str(os.path.join(LOCAL_DIR,'..','data','whoisip', 'ipasn.dat'))
        with open(rib_path, 'wb') as output:
            output.write(url.read())
        os.system('pyasn_util_convert.py --single %s %s' %(rib_path,dat_path))
        logger.info('[SUCCESS] \t\twhoisip.py')
        os.system('rm %s' % rib_path)

    except:
        logger.info('[FAILURE] \t\twhoisip.py')