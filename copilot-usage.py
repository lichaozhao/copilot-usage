# Path: copilot-usage.py
import json
import pandas as pd
from elasticsearch import Elasticsearch
from elasticsearch import helpers 
import copliothelpers as ch
import importlib 
import asyncio


importlib.reload(ch)

query = ch.get_query("2023-11-01T00:00:00", "2023-12-30T23:59:59", "copilot")

df = ch.es_query(query)
# dataframe which combines each request.content which gets more that one line. 
content_df = pd.DataFrame() 

# columns in request.content json format 
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
    # request.content is a string which contains lots of rows, we can split it to multiple lines by '\n'
    lines = contents.splitlines() 

    # handling telemetry data 
    for line in lines: 
        # the raw data may have some escape characters, so need to remove them
        # line = line.replace('\\\\', '').replace('"{', '{').replace('}"', '}').replace('"[[', '{').replace(']]"', '}').replace(',[]', ':[]')
        # line = line.replace('\\"','').replace('\\','')
        # only get the event which we are interested in
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

        tmp['user'] = row['user']
        content_df = content_df._append(tmp, ignore_index=True)


# save to local
content_df.to_csv('copilot-usage.csv', index=False)

# save to azure blob
# asyncio.run(ch.write_df_to_azure_blob(content_df, "2023-11-01T00:00:00", "2023-11-30T23:59:59", "copilot"))

