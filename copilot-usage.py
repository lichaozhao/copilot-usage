# Path: copilot-usage.py
import json
import pandas as pd
import ast
from elasticsearch import Elasticsearch
from elasticsearch import helpers 
import configparser 
import copliothelpers as ch
import importlib 



importlib.reload(ch)
# read es config info from config.ini and init es client
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

# Define the search query
# https://copilot-proxy.githubusercontent.com/v1/engines/copilot-codex/completions
# https://copilot-telemetry.githubusercontent.com/telemetry 

query = {
    "query": {
        "bool": {
            "must": [
                {
                    "match": {
                        "request.url": "telemetry"
                    }
                },
                {
                    "range": {
                        "timestamp": {
                            "gte": "2023-11-01T00:00:00",
                            "lte": "2023-11-30T23:59:59"
                        }
                    }
                }
            ]
        }
    }
}

# query = {
#     "query": {
#         "bool": {
#             "must": [
#                 {
#                     "match": {
#                         "request.url": "completions"
#                     }
#                 },
#                 {
#                     "range": {
#                         "timestamp": {
#                             "gte": "2023-11-01T00:00:00",
#                             "lte": "2023-11-30T23:59:59"
#                         }
#                     }
#                 }
#             ]
#         }
#     }
# }
# Initialize the scroll
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
    page = es.scroll(scroll_id=sid, scroll='2m')
    df = df._append(ch.load_metrics(page), ignore_index=True)
    # Update the scroll ID
    sid = page['_scroll_id']
    # Get the number of results that we returned in the last scroll
    scroll_size = len(page['hits']['hits'])
    print("scroll size: " + str(scroll_size))
    # Do something with the obtained page


# dataframe which combines each request.content which gets more that one line. 
content_df = pd.DataFrame() 
cols_chosen = [
           'time', 
           'data.baseData.name', 
           'data.baseData.measurements.numLines', 
           'data.baseData.properties.languageId', 
           'data.baseData.properties.common_vscodeversion',
           'data.baseData.properties.common_extname', 
           'data.baseData.properties.common_extversion']

for index, row in df.iterrows(): 
    contents = row['request.content']
    jsons = [] 
    lines = contents.splitlines() 

    if row['type'] == 'telemetry':    
        for line in lines: 
            # the raw data may have some escape characters, so need to remove them
            # line = line.replace('\\\\', '').replace('"{', '{').replace('}"', '}').replace('"[[', '{').replace(']]"', '}').replace(',[]', ':[]')
            # line = line.replace('\\"','').replace('\\','')

            # only get the event which we are interested in
                # 'copilot-chat/conversation.suggestionShown',
                # 'copilot-chat/conversation.acceptedInsert',
                # 'copilot-chat/conversation.acceptedCopy',
            event_strs = [
                'copilot/ghostText.shown',
                'copilot/ghostText.accepted',
                'agent/ghostText.accepted',
                'agent/ghostText.shown'
            ]

            if any(event_str in line for event_str in event_strs):
                data = json.loads(line)
                jsons.append(data) 
        
        # append data to content_df and rename columns
        if len(jsons) > 0:
            tmp = pd.json_normalize(jsons) 
            tmp = tmp[cols_chosen].rename(
                columns={
                'data.baseData.name': 'eventname',
                'data.baseData.measurements.numLines': 'numLines', 
                'data.baseData.properties.languageId': 'languageId', 
                'data.baseData.properties.common_vscodeversion': 'ide',
                'data.baseData.properties.common_extname': 'extname', 
                'data.baseData.properties.common_extversion': 'extversion'
                }
            )
            content_df = content_df._append(tmp, ignore_index=True)
            content_df['user'] = row['user'] 


content_df.to_csv('contents.csv', index=False)  # Write the DataFrame to a CSV file


# do some analysis based on the content_df 

content_df['time'] = pd.to_datetime(content_df['time'])

# 使用groupby()函数和agg()函数统计每个用户的登录次数和最新一次登录的时间
user_stats = content_df.groupby('user').agg(
    login_count=('time', 'count'),
    latest_login=('time', 'max')
)

print(user_stats)

