from setuptools import find_packages, setup

setup(
    name='Flare',
    version='0.4',
    platforms=["any"],  # or more specific, e.g. "win32", "cygwin", "osx"
    license="""MIT License

    Copyright (c) 2016 Austin Taylor

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.""",
    long_description='Flare is a network analytic framework designed for data scientists, security researchers, and network professionals. Written in Python, it is designed for rapid prototyping and development of behavioral analytics, and intended to make identifying malicious behavior in networks as simple as possible.',
    packages=find_packages(),
    scripts=['bin/hextoip', 'bin/iptohex', 'bin/ipwhois', 'bin/flare_beacon'],
    data_files=[('flare/data/whoisip/', [
        'flare/data/whoisip/asn_names.pkl',
        'flare/data/whoisip/ipasn.dat']),
        ('flare/data/majestic', [
            'flare/data/majestic/majestic_million.pkl']),
        ('flare/data/tld', [
            'flare/data/tld/tld_list.pkl']),
        ('flare/data/alexa', [
            'flare/data/alexa/subdomains-top1mil.txt',
            'flare/data/alexa/top-1m.csv']),
        ('flare/data/tld', [
            'flare/data/tld/tld_list.pkl']),
        ('flare/data/misc', [
            'flare/data/misc/dga_domains.txt',
            'flare/data/misc/words.txt'])],
     extras_require={
        ':python_version == "2.7"': [
            'ipaddr==2.1.11',
        ],
    }
)

