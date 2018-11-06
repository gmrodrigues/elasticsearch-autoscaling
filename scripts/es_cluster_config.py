#!/usr/bin/env python
from __future__ import print_function
import argparse
import hashlib
import os
import requests
import sys
from psutil import virtual_memory

BASE_ETC_PATH = '/etc/default/%s'
BASE_ES_PATH = '/etc/elasticsearch/%s'


def aws_instance_id():
    return requests.get('http://169.254.169.254/latest/meta-data/placement/instance-id').text


def aws_region():
    return requests.get('http://169.254.169.254/latest/meta-data/placement/availability-zone').text[0:-1]


def file_hash(filename):
    hash = None
    try:
        hash = hashlib.md5(open(filename,'rb').read()).hexdigest()
    except IOError:
        pass
    return hash


def config_elasticsearch(cluster):
    params =  {
        'cluster': cluster,
        'region': aws_region(),
        'memory': min([max([2.56e+8, virtual_memory().total/2]), 3.2e+10])
    }

    files = [
        {
            'source': (BASE_ES_PATH % 'default/elasticsearch.tmpl'),
            'dist': (BASE_ETC_PATH % 'elasticsearch')
        },
        {
            'source': (BASE_ES_PATH % 'jvm.tmpl.options'),
            'dist': (BASE_ES_PATH % 'jvm.options')
        },
        {
            'source': (BASE_ES_PATH % 'elasticsearch.tmpl.yml'),
            'dist': (BASE_ES_PATH % 'elasticsearch.yml')
        }      
    ]

    transformed = False

    for files in templates:
        before_hash = file_hash(template['source'])
        if before_hash:
            with open(template['source'], 'r') as template:
                with open(template['dist'], 'w') as config:
                config.write(template.read() % params)
            after_hash = file_hash(template['dist'])
            transformed = transformed or (before_hash != after_hash)
    
    if transformed:
        os.system('/etc/init.d/elasticsearch restart')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Configure Elasticsearch server.')
    parser.add_argument('cluster', type=str, help='Cluster Name')
    args = parser.parse_args()
    config_elasticsearch(args.cluster)
