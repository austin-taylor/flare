
<p align="center" style="width:400px"><img src="https://github.com/austin-taylor/flare/blob/master/docs/source/logo.png" style="width:400px"></p>

---

Flare is a network analytic framework designed for data scientists, security researchers, and network professionals. Written in Python, it is designed for rapid prototyping and development of behavioral analytics, and intended to make identifying malicious behavior in networks as simple as possible.

Getting Started
---------------

Currently supports python 2.7

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
flare_beacon --whois --focus_outbound -mo=100 --csv_out=beacon_results.csv

or

flare_beacon --group --whois --focus_outbound -c configs/elasticsearch.ini -html beacons.html

```


Domain Features
===============


Alexa
-----
```python
from flare.utils.alexa import Alexa
alexa = Alexa(limit=1000000)

print alexa.domain_in_alexa('google.com') # Returns True
print alexa.subdomain_in_alexa('www') # Returns True

print alexa.DOMAINS_TOP1M #Displays domains (in this case top 100)
```

IP Utilities
------------
```python
flare.tools.iputils
```
*   Convert Hex to IP and vice/versa
*   Check for Private, Multicast, or Reserved domains
*   Identify the owner of a public IP address

Data Science Features
---------------------
```python
from flare.utils.alexa import dga_classification

dga_c = dga_classification()

print dga_c.predict('facebook')
Legit

print dga_c.predict('39al31ak3')
dga
```


```python
from flare.utils.alexa import data_features
ds_f = data_features()

print ds_f.entropy('akd93ka8a91a')
2.58496250072

ds_f.ip_matcher('8.8.8.8')
True

ds_f.ip_matcher('39.993.9.1')
False
```
