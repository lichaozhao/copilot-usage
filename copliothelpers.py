import json
import pandas as pd
import ast
from elasticsearch import Elasticsearch
from elasticsearch import helpers 
import configparser 
import logging

# logging config 
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

log.addHandler(handler)

# read config and init es client

def es_client():
    config = configparser.ConfigParser()
    config.read('config.ini')

    ELASTICSEARCH_USERNAME = config.get('es', 'es_username') 
    ELASTICSEARCH_PASSWORD = config.get('es', 'es_password')
    ELASTICSEARCH_URL = config.get('es', 'es_host') 


    es = Elasticsearch(
        [ELASTICSEARCH_URL],
        http_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
        verify_certs=False
    )
    return es


# load_metrics: load metrics from es page
def load_metrics(page): 
    df = pd.DataFrame()

    for hit in page['hits']['hits']:
        # for copilot and chat. 
        # copilot: https://copilot-proxy.githubusercontent.com/v1/engines/copilot-codex/completions
        # chat: https://api.githubcopilot.com/chat/completions
        if hit['_source']['request']['url'].find('completions') != -1:
            line = pd.DataFrame([(hit['_source']['user'], 
                                  "prompt",
                                  hit['_source']['timestamp'], 
                                  hit['_source']['request']['url'], 
                                  hit['_source']['request']['content'], 
                                  hit['_source']['request']['headers'])],
                                columns=['user', 'type', 'time', 'request.url', 'request.content', 'request.headers'])

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

# es_query: query es with query and scroll
def es_query(query):

    es = es_client() 

    page = es.search(
        index='mitmproxy',
        body=query,
        scroll='2m',  # length of time to keep the scroll window open
        size=10  # number of results (documents) to return per batch
    )

    # the reults for the query 
    df = pd.DataFrame()

    # Get the scroll ID
    sid = page['_scroll_id']
    scroll_size = len(page['hits']['hits'])

    # Start scrolling
    while scroll_size > 0:
        print("Scrolling...")
        df = df._append(load_metrics(page), ignore_index=True)
        page = es.scroll(scroll_id=sid, scroll='2m')
        # Update the scroll ID
        sid = page['_scroll_id']
        # Get the number of results that we returned in the last scroll
        scroll_size = len(page['hits']['hits'])
        print("scroll size: " + str(scroll_size))
        # Do something with the obtained page


    return df