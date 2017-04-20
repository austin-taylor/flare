from setuptools import find_packages, setup

setup(
    name='Flare',
    version='0.1alpha',
    platforms=["any"],  # or more specific, e.g. "win32", "cygwin", "osx"
    license='',
    long_description='',
    packages=find_packages(),
    scripts=['bin/hextoip', 'bin/iptohex', 'bin/ipwhois'],
    data_files=[('flare/data/whoisip/', [
        'flare/data/whoisip/asn_names_20160930.pkl',
        'flare/data/whoisip/ipasn_20160916.1200.dat']),
        ('flare/data/alexa', [
            'flare/data/alexa/subdomains-top1mil.txt',
            'flare/data/alexa/top-1m.csv']),
        ('flare/data/misc', [
            'flare/data/misc/dga_domains.txt',
            'flare/data/misc/words.txt'])]
)