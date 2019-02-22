
<p align="center" style="width:400px"><img src="https://github.com/austin-taylor/flare/blob/master/docs/source/logo.png" style="width:400px"></p>

---

Flare is a network analytic framework designed for data scientists, security researchers, and network professionals. Written in Python, it is designed for rapid prototyping and development of behavioral analytics, and intended to make identifying malicious behavior in networks as simple as possible.

Getting Started
---------------

Currently supports python 2.7 and python 3

```python
sudo pip install -r requirements.txt
python setup.py install
```

Core Features
-------------
####
*   Command and Control Analytics
    *   Identify Beaconing in your environment (works with Suricata output and ElasticSearch)
*   Feature Extraction
    *   Helper utility functions to filter out the noise.
*   Alexa, Umbrella, and Majestic Million (coming soon)
*   WHOIS IP Lookup
*   Pre-build machine learning classifiers
*   So much more...


Analytics
=========

Beaconing
---------
Designed for elasticsearch and Suricata, elasticBeacon will connect to your elasticsearch server, retrieve all IP addresses and identify periodic activity.

You may need to forward port 9200 to your localhost with **ssh -NfL 9200:localhost:9200 user@x.x.x.x**

```python
from flare.analytics.command_control import elasticBeacon

eb = elasticBeacon(es_host='localhost')
beacons = eb.find_beacons(group=True, focus_outbound=True)
```

Also available in commandline:

```bash
CSV OUTPUT
flare_beacon --whois --focus_outbound -mo=100 --csv_out=beacon_results.csv

HTML OUTPUT
flare_beacon --group --whois --focus_outbound -c configs/elasticsearch.ini -html beacons.html

JSON OUTPUT (for SIEM)
flare_beacon --whois --focus_outbound -c /opt/flare-master/configs/selks4.ini -json beacon.json -v

```

Full writeup [here](http://www.austintaylor.io/detect/beaconing/intrusion/detection/system/command/control/flare/elastic/stack/2017/06/10/detect-beaconing-with-flare-elasticsearch-and-intrusion-detection-systems/)

Domain Features
===============


Alexa
-----
```python
from flare.tools.alexa import Alexa
alexa = Alexa(limit=1000000)

print alexa.domain_in_alexa('google.com') # Returns True
print alexa.subdomain_in_alexa('www') # Returns True

print alexa.DOMAINS_TOP1M #Displays domains (in this case top 100)
```

IP Utilities
------------
```python

from flare.tools.whoisip import WhoisLookup

whois = WhoisLookup()
whois.get_name_by_ip('8.8.8.8')

OUT: 'GOOGLE - Google Inc., US'

from flare.tools.iputils import hex_to_ip, ip_to_hex

ip_to_hex('8.8.8.8'), hex_to_ip('08080808')

OUT: (u'08080808', '8.8.8.8')

```
*   Convert Hex to IP and vice/versa
*   Check for Private, Multicast, or Reserved domains
*   Identify the owner of a public IP address

Data Science Features
---------------------
```python
from flare.data_science.features import dga_classifier

dga_c = dga_classifier()

print dga_c.predict('facebook')
Legit

print dga_c.predict('39al31ak3')
dga
```


```python
from flare.data_science.features import entropy
from flare.data_science.features import ip_matcher
from flare.data_science.features import domain_extract
from flare.data_science.features import levenshtein
from flare.data_science.features import domain_tld_extract

# Entropy example
print entropy('akd93ka8a91a')
2.58496250072

# IP Matcher Example
print ip_matcher('8.8.8.8')
True

print ip_matcher('39.993.9.1')
False

# Domain Extract Example
domain_extract('longsubdomain.huntoperator.com')
'huntoperator'

# Domain TLD Extract
domain_tld_extract('longsubdomain.huntoperator.com')
'huntoperator.com'

# Levenshtein example
a = ['google.com']
b = ['googl3.com']
print levenshtein(a, b)
'Difference of:' 1

```

and many more features for data extraction...
