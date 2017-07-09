# -*- coding: utf-8 -*-
import pyasn
import sys
import json
import os
import argparse
import datetime

if (sys.version_info > (3, 0)):
    from urllib.request import urlopen
    from html.parser import HTMLParser
    import _pickle as pickle
else:
    from urllib2 import urlopen
    import cPickle as pickle
    from HTMLParser import HTMLParser


LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))


class WhoisLookup:

    def __init__(self, asn_dat=None, asn_map=None):

        if asn_dat is not None:
            self.asndb = pyasn.pyasn(asn_dat)
        else:
            self.asndb = pyasn.pyasn(os.path.join(
                LOCAL_DIR, '..', 'data', 'whoisip', 'ipasn_20160916.1200.dat'))


        if asn_map is not None:
            with open(asn_map, 'rb') as f:
                self.names = json.loads(f.read())
        else:
            pkl_path = os.path.join(
                LOCAL_DIR, '..', 'data', 'whoisip', 'asn_names_20160930.pkl')
            with open(pkl_path, 'rb') as f:
                if (sys.version_info > (3, 0)):
                    self.names = pickle.load(f, encoding='bytes')
                else:
                    self.names = pickle.load(f)

    def get_asn(self, ip):
        asn, netmask = self.asndb.lookup(ip)
        return asn

    def get_asn_netmask(self, ip):
        return self.asndb.lookup(ip)

    def get_name_by_ip(self, ip):
        query_msg = "IP Not Found"
        try:
            if (sys.version_info > (3, 0)):
                asn = str(self.get_asn(ip)).encode()
                if asn in self.names:
                    query_msg = self.names[asn].decode()
            elif (sys.version_info < (3,0)):
                asn = str(self.get_asn(ip))
                if asn in self.names:
                    query_msg = self.names[asn]
            return query_msg
        except ValueError:
            except_msg = "Invalid input"
            return except_msg

    def domain_in_ip_whois_match(self, domain, ip):
        """
        Takes a domain and IP address and
        compares if the IP WHOIS is in the domain description
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
    parser = argparse.ArgumentParser(description='Whois IP Utilities')
    parser.add_argument('--asn_names', action='store_true', dest='asn_names', default=False)
    args = parser.parse_args()
    if args.asn_names:
        asn_map = WhoisLookup.create_new_asn_mapping2(verbose=True)

        now = datetime.datetime.now()
        file_name = 'asn_names_%s.pkl' % now.strftime('%Y%m%d')
        print(('Saving %d entries to %s' % (len(list(asn_map.keys())), file_name)))
        with open(file_name, 'wb') as f:
            pickle.dump(asn_map, f)
