# coding: utf-8
import sys
from flare.tools.utils import bcolors
from flare.base.config import flareConfig


try:
    import pandas as pd
except:
    print("Please make sure you have pandas installed. pip -r requirements.txt or pip install pandas")
    sys.exit(0)

try:
    from elasticsearch import Elasticsearch, helpers
except:
    print("Please make sure you have elasticsearch module installed. pip -r requirements.txt or pip install elasticsearch")
    sys.exit(0)


from multiprocessing import Process, JoinableQueue, Lock, Manager
from flare.tools.iputils import private_check, multicast_check, reserved_check
from flare.tools.whoisip import WhoisLookup
import time
import warnings
import os
import datetime
import json

warnings.filterwarnings('ignore')

config_default = os.path.join(os.path.dirname(__file__), '..', '..', 'configs/elasticsearch.ini')

class elasticBeacon(object):
    """
    Elastic Beacon is  designed to identify periodic communication between
    network communicatiors. Future updates will allow for dynamic fields to be passed in.

    If you do not allow your elastic search server to communicate externally, you can setup an
    ssh tunnel by using ssh -NfL 9200:localhost:9200 username@yourserver

    Otherwise, you'll need to adjust es_host to the IP address that is exposed to elasticSearch.

    """
    def __init__(self,
                 config_in=None,
                 min_occur=10,
                 min_percent=5,
                 window=2,
                 threads=8,
                 period=24,
                 min_interval=2,
                 es_host='localhost',
                 es_port=9200,
                 es_timeout=480,
                 es_index='logstash-flow-*',
                 kibana_version='4',
                 verbose=True,
                 debug=False):
        """

        :param min_occur: Minimum number of triads to be considered beaconing
        :param min_percent: Minimum percentage of all connection attempts that
         must fall within the window to be considered beaconing
        :param window: Size of window in seconds in which we group connections to determine percentage, using a
         large window size can give inaccurate interval times, multiple windows contain all interesting packets,
         so the first window to match is the interval
        :param threads: Number of cores to use
        :param period: Number of hours to locate beacons for
        :param min_interval: Minimum interval betweeen events to consider for beaconing behavior
        :param es_host: IP Address of elasticsearch host (default is localhost)
        :param es_timeout: Sets timeout to 480 seconds
        :param kibana_version: 4 or 5 (query will depend on version)
        """
        #self.config_in = config_in
        if config_in is not None:
            try:
                self.config = flareConfig(config_in)
                self.es_host = self.config.get('beacon', 'es_host')
                self.es_port = int(self.config.get('beacon', 'es_port'))
                self.es_index = self.config.get('beacon', 'es_index')
                self.MIN_OCCURRENCES = int(self.config.get('beacon','min_occur'))
                self.MIN_PERCENT = int(self.config.get('beacon','min_percent'))
                self.WINDOW = int(self.config.get('beacon','window'))
                self.NUM_PROCESSES = int(self.config.get('beacon','threads'))
                self.period = int(self.config.get('beacon','period'))
                self.min_interval = int(self.config.get('beacon', 'min_interval'))
                self.es_timeout = int(self.config.get('beacon','es_timeout'))
                self.kibana_version = self.config.get('beacon','kibana_version')
                self.beacon_src_ip = self.config.get('beacon','field_source_ip')
                self.beacon_dest_ip = self.config.get('beacon', 'field_destination_ip')
                self.beacon_destination_port = self.config.get('beacon', 'field_destination_port')
                self.beacon_timestamp = self.config.get('beacon', 'field_timestamp')
                self.beacon_flow_bytes_toserver = self.config.get('beacon', 'field_flow_bytes_toserver')
                self.beacon_flow_id = self.config.get('beacon', 'field_flow_id')
                self.beacon_event_type = self.config.get('beacon','event_type')
                self.verbose = self.config.config.getboolean('beacon', 'verbose')
                self.auth_user = self.config.config.get('beacon','username')
                self.auth_password = self.config.config.get('beacon', 'password')
                self.suricata_defaults = self.config.config.getboolean('beacon','suricata_defaults')
                try:
                    self.debug = self.config.config.getboolean('beacon', 'debug')
                except:
                    pass


            except Exception as e:
                print(('{red}[FAIL]{endc} Could not properly load your config!\nReason: {e}'.format(red=bcolors.FAIL, endc=bcolors.ENDC, e=e)))
                sys.exit(0)

        else:
            self.es_host = es_host
            self.es_port = es_port
            self.es_index = es_index
            self.MIN_OCCURRENCES = min_occur
            self.MIN_PERCENT = min_percent
            self.WINDOW = window
            self.NUM_PROCESSES = threads
            self.period = period
            self.min_interval = min_interval
            self.kibana_version = kibana_version
            self.es_timeout = es_timeout
            self.beacon_src_ip = 'src_ip'
            self.beacon_dest_ip = 'dest_ip'
            self.beacon_destination_port = 'dest_port'
            self.beacon_timestamp = '@timestamp'
            self.beacon_flow_bytes_toserver = 'bytes_toserver'
            self.beacon_flow_id = 'flow_id'
            self.beacon_event_type = 'flow'
            self.verbose = verbose
            self.suricata_defaults = False

        self.ver = {'4': {'filtered': 'query'}, '5': {'bool': 'must'}}
        self.filt = list(self.ver[self.kibana_version].keys())[0]
        self.query = list(self.ver[self.kibana_version].values())[0]
        self.debug = debug
        self.whois = WhoisLookup()
        self.info = '{info}[INFO]{endc}'.format(info=bcolors.OKBLUE, endc=bcolors.ENDC)
        self.success = '{green}[SUCCESS]{endc}'.format(green=bcolors.OKGREEN, endc=bcolors.ENDC)
        self.fields = [self.beacon_src_ip, self.beacon_dest_ip, self.beacon_destination_port, 'bytes_toserver', 'dest_degree', 'occurrences', 'percent', 'interval']

        try:
            _ = (self.auth_user, self.auth_password)
        except AttributeError as e:
            self.auth = None

        try:
            self.vprint('{info}[INFO]{endc} Attempting to connect to elasticsearch...'.format(info=bcolors.OKBLUE,
                                                                                        endc=bcolors.ENDC))
            if self.auth == None:
                self.es = Elasticsearch(self.es_host, port=self.es_port, timeout=self.es_timeout, verify_certs=False)
            else:
                self.es = Elasticsearch(self.es_host, port=self.es_port, timeout=self.es_timeout, http_auth=(self.auth_user, self.auth_password), verify_certs=False)
            self.vprint('{green}[SUCCESS]{endc} Connected to elasticsearch on {host}:{port}'.format(green=bcolors.OKGREEN, endc=bcolors.ENDC, host=self.es_host, port=str(self.es_port)))
        except Exception as e:
            self.vprint(e)
            raise Exception(
                "Could not connect to ElasticSearch -- Please verify your settings are correct and try again.")

        self.q_job = JoinableQueue()
        self.l_df = Lock()
        self.l_list = Lock()
        self.high_freq = None
        self.flow_data = self.run_query()


    def vprint(self, msg):
        if self.verbose:
            print(msg)

    def dprint(self, msg):
        if self.debug:
            print(("[DEBUG] " + str(msg)))


    def hour_query(self, h, *fields):
        """

        :param h: Number of hours to look for beaconing (recommend 24 if computer can support it)
        :param fields: Retrieve only these fields -- example "src_ip", "dest_ip", "src_port", "dest_port"
        :return:
        """
        # Timestamp in ES is in milliseconds
        NOW = int(time.time() * 1000)
        SECONDS = 1000
        MINUTES = 60 * SECONDS
        HOURS = 60 * MINUTES
        lte = NOW
        gte = int(NOW - h * HOURS)


        if self.es_index:
            query = {
                "query": {
                    self.filt: {
                        self.query: {
                            "query_string": {
                                "query": "*",
                                "analyze_wildcard": 'true'
                            }
                        },
                        "filter": [{
                            "bool": {
                                "must": [
                                    {
                                        "range": {
                                            self.beacon_timestamp: {
                                                "gte": gte,
                                                "lte": lte,
                                                "format": "epoch_millis"
                                            }
                                        }
                                    }
                                ],
                                "must_not": []
                            }
                        },
                            {"term": {"event_type": self.beacon_event_type}}
                        ]
                    }
                }
            }
        else:
            query = {
                "query": {
                    self.filt: {
                        self.query: {
                            "query_string": {
                                "query": "*",
                                "analyze_wildcard": 'true'
                            }
                        },
                        "filter": {
                            "bool": {
                                "must": [
                                    {
                                        "range": {
                                            "timestamp": {
                                                "gte": gte,
                                                "lte": lte,
                                                "format": "epoch_millis"
                                            }
                                        }
                                    }
                                ],
                                "must_not": []
                            }
                        }
                    }
                }
            }
        if fields:
            query["_source"] = list(fields)
            self.dprint(query)

        return query

    def percent_grouping(self, d, total):
        mx = 0
        interval = 0
        # Finding the key with the largest value (interval with most events)
        mx_key = int(max(iter(list(d.keys())), key=(lambda key: d[key])))

        mx_percent = 0.0

        for i in range(mx_key - self.WINDOW, mx_key + 1):
            current = 0
            # Finding center of current window
            curr_interval = i + int(self.WINDOW / 2)
            for j in range(i, i + self.WINDOW):
                if j in d:
                    current += d[j]
            percent = float(current) / total * 100

            if percent > mx_percent:
                mx_percent = percent
                interval = curr_interval

        return interval, mx_percent

    def run_query(self):
        self.vprint("{info} Gathering flow data... this may take a while...".format(info=self.info))

        FLOW_BYTES = self.beacon_flow_bytes_toserver
        if self.suricata_defaults:
            FLOW_BYTES = 'flow.' + FLOW_BYTES

        query = self.hour_query(self.period, self.beacon_src_ip, self.beacon_dest_ip, self.beacon_destination_port,
                                self.beacon_timestamp, FLOW_BYTES, self.beacon_flow_id)
        self.dprint(query)
        resp = helpers.scan(query=query, client=self.es, scroll="90m", index=self.es_index, timeout="10m")
        df = pd.DataFrame([rec['_source'] for rec in resp])
        if len(df) == 0:
            raise Exception("Elasticsearch did not retrieve any data. Please ensure your settings are correct inside the config file.")

        self.dprint(df)
        df['dest_port'] = df[self.beacon_destination_port].fillna(0).astype(int)

        if 'flow' in df.columns:
            df[self.beacon_flow_bytes_toserver] = df['flow'].apply(lambda x: x.get(self.beacon_flow_bytes_toserver))

        df['triad_id'] = (df[self.beacon_src_ip] + df[self.beacon_dest_ip] + df[self.beacon_destination_port].astype(str)).apply(hash)
        df['triad_freq'] = df.groupby('triad_id')['triad_id'].transform('count').fillna(0).astype(int)
        self.high_freq = list(df[df.triad_freq > self.MIN_OCCURRENCES].groupby('triad_id').groups.keys())
        return df

    def find_beacon(self, q_job, beacon_list):

        while not q_job.empty():
            triad_id = q_job.get()
            self.l_df.acquire()
            work = self.flow_data[self.flow_data.triad_id == triad_id]
            self.l_df.release()
            
            work[self.beacon_timestamp] = pd.to_datetime(work[self.beacon_timestamp])
            work[self.beacon_timestamp] = (work[self.beacon_timestamp].astype(int) / 1000000000).astype(int)
            work = work.sort_values([self.beacon_timestamp])
            work['delta'] = (work[self.beacon_timestamp] - work[self.beacon_timestamp].shift()).fillna(0)
            work = work[1:]

            d = dict(work.delta.value_counts())
            for key in list(d.keys()):
                if key < self.min_interval:
                    del d[key]
            
            # Finding the total number of events
            total = sum(d.values())
            
            if d and total > self.MIN_OCCURRENCES:
                window, percent = self.percent_grouping(d, total)
                if percent > self.MIN_PERCENT and total > self.MIN_OCCURRENCES:
                    PERCENT = str(int(percent))
                    WINDOW = str(window)
                    SRC_IP = work[self.beacon_src_ip].unique()[0]
                    DEST_IP = work[self.beacon_dest_ip].unique()[0]
                    DEST_PORT = str(int(work[self.beacon_destination_port].unique()[0]))
                    BYTES_TOSERVER = work[self.beacon_flow_bytes_toserver].sum()
                    SRC_DEGREE = len(work[self.beacon_dest_ip].unique())
                    OCCURRENCES = total
                    self.l_list.acquire()
                    beacon_list.append([SRC_IP, DEST_IP, DEST_PORT, BYTES_TOSERVER, SRC_DEGREE, OCCURRENCES, PERCENT, WINDOW])
                    self.l_list.release()
            
            q_job.task_done()

    def find_beacons(self, group=True, focus_outbound=False, whois=True, csv_out=None, html_out=None, json_out=None):

        for triad_id in self.high_freq:
            self.q_job.put(triad_id)

        mgr = Manager()
        beacon_list = mgr.list()
        processes = [Process(target=self.find_beacon, args=(self.q_job, beacon_list,)) for thread in
                     range(self.NUM_PROCESSES)]

        # Run processes
        for p in processes:
            p.start()

        # Exit the completed processes
        for p in processes:
            p.join()

        beacon_list = list(beacon_list)
        beacon_df = pd.DataFrame(beacon_list,
                                 columns=self.fields).dropna()
        beacon_df.interval = beacon_df.interval.astype(int)
        beacon_df['dest_degree'] = beacon_df.groupby(self.beacon_dest_ip)[self.beacon_dest_ip].transform('count').fillna(0).astype(int)
        self.vprint('{info} Calculating destination degree.'.format(info=self.info))

        if whois:
            self.vprint('{info} Enriching IP addresses with whois information'.format(info=self.info))
            beacon_df['src_whois'] = beacon_df[self.beacon_src_ip].apply(lambda ip: self.whois.get_name_by_ip(ip))
            beacon_df['dest_whois'] = beacon_df[self.beacon_dest_ip].apply(lambda ip: self.whois.get_name_by_ip(ip))

        if focus_outbound:
            self.vprint('{info} Applying outbound focus - filtering multicast, reserved, and private IP space'.format(info=self.info))
            beacon_df = beacon_df[(beacon_df[self.beacon_src_ip].apply(private_check)) &
                                        (~beacon_df[self.beacon_dest_ip].apply(multicast_check)) &
                                        (~beacon_df[self.beacon_dest_ip].apply(reserved_check)) &
                                        (~beacon_df[self.beacon_dest_ip].apply(private_check))]

        if group:
            self.vprint('{info} Grouping by destination group IP'.format(info=self.info))

            if whois:
                self.fields.insert(self.fields.index(self.beacon_dest_ip), 'dest_whois')
            beacon_df = pd.DataFrame(beacon_df.groupby(self.fields).size())
            beacon_df.drop(0, axis=1, inplace=True)

        if csv_out:
            self.vprint('{success} Writing csv to {csv_name}'.format(csv_name=csv_out, success=self.success))
            beacon_df.to_csv(csv_out, index=False)

        if html_out:
            self.vprint('{success} Writing html file to {html_out}'.format(html_out=html_out, success=self.success))
            beacon_df.to_html(html_out)

        if json_out:
            self.vprint('{success} Writing json file to {json_out}'.format(json_out=json_out, success=self.success))
            now = datetime.datetime.now().isoformat()
            beacon_df['timestamp'] = now
            beacon_df['period'] = self.period
            beacon_df['event_type'] = "beaconing"
            beacons = beacon_df.to_dict(orient="records")

            with open(json_out, 'a') as out_file:
                for beacon in beacons:
                    out_file.write(json.dumps(beacon) + '\n')

        return beacon_df
