import json
import pandas as pd
import ast
from elasticsearch import Elasticsearch
from elasticsearch import helpers 
import configparser 
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

log.addHandler(handler)

# load_metrics: load metrics from es page
def load_metrics(page): 
    df = pd.DataFrame(columns=['user', 'type', 'time', 'request.url', 'request.content'])

    for hit in page['hits']['hits']:
        if hit['_source']['request']['url'] == 'https://copilot-proxy.githubusercontent.com/v1/engines/copilot-codex/completions':
            line = pd.DataFrame([(hit['_source']['user'], 
                                  "prompt",
                                  hit['_source']['timestamp'], 
                                  hit['_source']['request']['url'], 
                                  hit['_source']['request']['content'])], 
                                columns=['user', 'type', 'time', 'request.url', 'request.content'])

        elif hit['_source']['request']['url'] == 'https://copilot-telemetry.githubusercontent.com/telemetry':
            line = pd.DataFrame([(hit['_source']['user'], 
                                  "telemetry",
                                  hit['_source']['timestamp'],
                                  hit['_source']['request']['url'], 
                                  hit['_source']['request']['content'])], 
                                columns=['user', 'type', 'time', 'request.url', 'request.content'])
        else:
            log.info("don't need to be collected url: " + hit['_source']['request']['url'])
            continue
        
        df = df._append(line, ignore_index=True) 
    
    return df