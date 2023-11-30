# Path: copilot-prompt.py
import json
import pandas as pd
import copliothelpers as ch
import importlib 

importlib.reload(ch)

# get prompts, both copilot and chat. 
query = ch.get_query("2023-11-01T00:00:00", "2023-11-30T23:59:59", "prompt")

df = ch.es_query(query) 
content_df = pd.DataFrame() 

# choose columns from request.content json format
cols_content = [
                'user',
                'time',
                'prompt', 
                'suffix', 
                'language',
                'ide_version', 
                'copilot_version']

for index, row in df.iterrows():

    # request.headers is a dictionary. 
    headers = row['request.headers']
    ide_version = headers['editor-version']
    copilot_version = headers['editor-plugin-version']

    # request.content is a string. 
    contents = row['request.content']
    contents_json = json.loads(contents)

    # chat prompt contains lots of rows in content. 
    if row['request.url'].find('chat') != -1:
        tmp = pd.DataFrame()
        chat_msgs = contents_json['messages']
        for line in chat_msgs:
            # skip system message
            if line['role'] == 'system':
                continue
            
            user = row['user'] 
            time = row['time']             
            prompt = line['content'] 
            suffix = "Chat-Only"
            language = "Chat-Only"
            tmp = tmp._append(pd.DataFrame([(user, time, prompt, suffix, language, ide_version, copilot_version)], columns=cols_content), ignore_index=True)

        content_df = content_df._append(tmp, ignore_index=True)

    else:
        prompt = contents_json['prompt']
        suffix = contents_json['suffix']
        language = contents_json['extra']['language']

        user = row['user']
        time = row['time'] 

        tmp = pd.DataFrame([(user, time, prompt, suffix, language, ide_version, copilot_version)], columns=cols_content)
        content_df = content_df._append(tmp, ignore_index=True)

content_df.to_csv('copilot-prompt.csv', index=False)