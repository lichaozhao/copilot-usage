# mitmdump --web-host 0.0.0.0 --listen-host 0.0.0.0 --set block_global=false -s <your script path>/sample.py 
# mitmweb --web-host 0.0.0.0 --listen-host 0.0.0.0 --set block_global=false 
# based on Daiel Wang's full feature script. I just simplified it. 
# the original script also contains whitelist of requests and basic authentication.
# Enhanced with Azure Active Directory (AAD) integration

import asyncio
from mitmproxy import http,ctx,connection,proxy
from elasticsearch import Elasticsearch, exceptions
from datetime import datetime
import base64
import re
import os
import functools 
import configparser
from aad_auth import AADAuthenticator

# read es config info from config.ini and init es client
# format: 
# [es]
# es_username=<your es user name>
# es_password=<your es password>
# es_host=<your es url:9200>
config = configparser.ConfigParser()
config.read('<path>/config.ini')

ELASTICSEARCH_USERNAME = config.get('es', 'es_username') 
ELASTICSEARCH_PASSWORD = config.get('es', 'es_password')
ELASTICSEARCH_URL = config.get('es', 'es_host') 

es = Elasticsearch(
    [ELASTICSEARCH_URL],
    http_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
    verify_certs=False
)


class SaveLogtoElasticSearch:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.proxy_authorizations = {} 
        # allowed_users.txt only contains a list of username 
        self.user_list = self.load_users("<path>/allowed_users.txt")
        # Initialize AAD authenticator
        self.aad_auth = AADAuthenticator("<path>/config.ini")
    
    def load_users(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Users file '{file_path}' not found")
        users = []
        with open(file_path, "r") as f:
            for line in f:
                users.append(line.strip())
        return users

    # verify whether the request is allowed 
    def http_connect(self, flow: http.HTTPFlow):
        # Enhanced authentication: support both AAD and legacy proxy auth
        
        # Try Authorization header first (Bearer token for AAD)
        auth_header = flow.request.headers.get("Authorization", "")
        if auth_header:
            username = self.aad_auth.authenticate_user(auth_header)
            if username:
                ctx.log.info(f"Authenticated User via AAD: {username}@{flow.client_conn.address[0]}")
                self.proxy_authorizations[flow.client_conn.address[0]] = username
                return
        
        # Fallback to legacy Proxy-Authorization for backward compatibility
        proxy_auth = flow.request.headers.get("Proxy-Authorization", "")
        if proxy_auth:
            username = self.aad_auth.authenticate_user(proxy_auth)
            if username and (username in self.user_list or not self.aad_auth.fallback_to_userlist):
                ctx.log.info(f"Authenticated User via Proxy-Auth: {username}@{flow.client_conn.address[0]}")
                self.proxy_authorizations[flow.client_conn.address[0]] = username
                return
        
        # No valid authentication found
        ctx.log.warning(f"Authentication failed for {flow.client_conn.address[0]}")
        flow.response = http.Response.make(401, b"Authentication required", {
            "WWW-Authenticate": "Bearer realm=\"Copilot Usage Collection\", Basic realm=\"Legacy Auth\""
        })


    def response(self, flow: http.HTTPFlow):
        # async save request and response to elasticsearch
        asyncio.ensure_future(self.save_to_elasticsearch(flow))

    async def save_to_elasticsearch(self, flow: http.HTTPFlow):
        # only capture requests which contain "completions" and "telemetry"
        if flow.request.url.find("completions") == -1 and flow.request.url.find('telemetry') == -1:
            return

        username = self.proxy_authorizations.get(flow.client_conn.address[0])
        
        # Get additional user information from AAD if available
        user_info = self.aad_auth.get_user_info(username) if username else {}

        # Add "ms" to the end of the timeconsumed string
        timeconsumed = round((flow.response.timestamp_end - flow.request.timestamp_start) * 1000, 2)
        timeconsumed_str = f"{timeconsumed}ms"  
 
        # save to es
        doc = {
            'user': username,
            'user_info': user_info,  # Additional AAD user information
            "timestamp": datetime.utcnow().isoformat(),
            "proxy-time-consumed": timeconsumed_str,  # Use the modified timeconsumed string
            'request': {
                'url': flow.request.url,
                'method': flow.request.method,
                'headers': dict(flow.request.headers),
                'content': flow.request.content.decode('utf-8', 'ignore'),
            },
            'response': {
                'status_code': flow.response.status_code,
                'headers': dict(flow.response.headers),
                'content': flow.response.content.decode('utf-8', 'ignore'),
            }
        }
        
        try:
            #change the index name to your own
            index_func = functools.partial(es.index, index='mitmproxy', body=doc)
            await self.loop.run_in_executor(None, index_func)   
        except exceptions.ConnectionTimeout as e:
            ctx.log.error(f"Connection to Elasticsearch timed out: {e}") 
            ctx.log.info("Retrying request with exponential backoff...")
            # Retry the request with an exponential backoff
            for i in range(3):  # Retry up to 3 times
                try:
                    await asyncio.sleep(2 ** i)  # Wait 2^i seconds before retrying
                    await self.loop.run_in_executor(None, index_func)
                    break  # If the request succeeds, break the loop
                except exceptions.ConnectionTimeout:
                    continue  # If the request still times out, continue to the next iteration
            else:
                ctx.log.error("Failed to connect to Elasticsearch after 3 retries.")
                return             
        except exceptions.ElasticsearchException as e:
            ctx.log.error(f"Failed to save to elasticsearch: {e}")
            return


addons = [
    SaveLogtoElasticSearch()
]
