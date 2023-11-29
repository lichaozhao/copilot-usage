
# GitHub Copilot for business usage data collection  

## Prerequisites

1. My environment is:
    - Mitmproxy: 8.0.0
    - Python:    3.8.10
    - Platform:  Linux-5.15.0-1050-azure-x86_64-with-glibc2.29

2. GitHub Copilot proxy setting : [github copilot proxy config](https://docs.github.com/en/copilot/configuring-github-copilot/configuring-network-settings-for-github-copilot?tool=vscode)

3. Install and config ES on aks, or you can use your existed ES cluster. 
    - create aks cluster on Azure. 
    - deploy elasticsearch cluster according to [intall es on AKS](https://www.elastic.co/cn/blog/how-to-run-elastic-cloud-on-kubernetes-from-azure-kubernetes-service) 

4. Install mitmproxy on your server and download requisite python libraries. To find more info from [mitmproxy](https://docs.mitmproxy.org/archive/v8/)

5. Start mitmproxy with correct parameters, choose what you like. 
    - mitmproxy, mitmdump, mitmweb are 3 different mitmproxy model. 
    - some examples for start proxy server : 
        - mitmproxy --listen-host 0.0.0.0 --set block_global=false -s <your script file path> -p <port>
        - mitmweb --web-host 0.0.0.0 --listen-host 0.0.0.0 --set block_global=false -s <script.py>

          default port of proxy is 8080, default web port is 8081. 
        - mitmdump --listen-host 0.0.0.0 --set block_global=false -s <your script file path> -p <port>

    - After start proxy server, please config your brsower using proxy and access http://mitm.test to download certificate. 

6. Other info 
    - For VS Code users  
        - you may need to install win-ca extension to make proxy customized certificate work. 
        - to collect data, the proxy server address should be: http://<user>@<server_address>:<port>, no password needed. 
    - For Jerbrains users
        - you need to allow the option 'accept non-trusted certificates automatically' in settings -> tools -> server certificates 
        - please fill 'host name', 'port number', chose 'Proxy authentication' and type your user name in 'Login'. No password needed. 

## How to use it? 

1. using you own info to start the proxy server. the info you must provide includes: 
    - allowed_users.txt file, a sample content will be like list of user name:
      
        user1
        user2
    - config file which includes elastic search info. 
2. start proxy server using the command provided above. 
3. run copilot-usage.py, you will get a csv file. then you can do anything you want using spreadsheet.
        

