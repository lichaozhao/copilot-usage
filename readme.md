# GitHub Copilot for Business Usage Data Collection

This solution enables the collection of usage data for Copilot for Business clients using mitmproxy. 

- `sample.py` is used as the mitmproxy script. 
- `copilot-usage.py` is used to collect Copilot usage data. 
- `copilotchat-usage.py` is used to collect Copilot chat usage data. 
- `copilot-prompt.py` is used to collect all prompts, including Copilot and chat. 

## Prerequisites

Ensure the following prerequisites are met:

- Mitmproxy version 8.0.0
- Python version 3.8.10+
- Linux-5.15.0-1050-azure-x86_64-with-glibc2.29 platform
- Required Python packages (install with `pip install -r requirements.txt`)

Configure GitHub Copilot proxy settings by referring to the [GitHub Copilot Proxy Config](https://docs.github.com/en/copilot/configuring-github-copilot/configuring-network-settings-for-github-copilot?tool=vscode) documentation.

Install and configure Elasticsearch on AKS or use an existing Elasticsearch cluster. To install Elasticsearch on AKS, follow the steps in the [Install Elasticsearch on AKS](https://www.elastic.co/cn/blog/how-to-run-elastic-cloud-on-kubernetes-from-azure-kubernetes-service) guide.

Install mitmproxy on your server and download the required Python libraries. For more information, refer to the [mitmproxy documentation](https://docs.mitmproxy.org/archive/v8/).

### Azure Active Directory (AAD) Integration

This solution now supports Azure Active Directory authentication for enhanced security:

1. **Create an Azure AD App Registration:**
   - Register a new application in Azure AD
   - Note the `Client ID`, `Client Secret`, and `Tenant ID`
   - Configure appropriate API permissions if needed

2. **Configure AAD in config.ini:**
   ```ini
   [aad]
   tenant_id=your-tenant-id
   client_id=your-client-id
   client_secret=your-client-secret
   enable_aad_auth=true
   fallback_to_userlist=true
   ```

3. **Authentication Methods:**
   - **Bearer Token (Recommended)**: Use `Authorization: Bearer <jwt-token>` header
   - **Legacy Basic Auth**: Use `Proxy-Authorization: Basic <base64-credentials>` header

## Usage

Follow these steps to use the solution:

1. Start mitmproxy with the desired parameters. Choose from the following options:
     - `mitmproxy`, `mitmdump`, and `mitmweb` are three different models of mitmproxy.
     - Examples of starting the proxy server:
         - `mitmproxy --listen-host 0.0.0.0 --set block_global=false -s <your script file path> -p <port>`
         - `mitmweb --web-host 0.0.0.0 --listen-host 0.0.0.0 --set block_global=false -s <script.py>`
             (The default port for the proxy is 8080, and the default web port is 8081.)
         - `mitmdump --listen-host 0.0.0.0 --set block_global=false -s <your script file path> -p <port>`

     - After starting the proxy server, configure your browser to use the proxy and access http://mitm.it to download the certificate.

2. Additional information:
     - For VS Code users:
         - Install the `win-ca` extension to make the customized proxy certificate work.
         - To collect data, the proxy server address should be: `http://<user>@<server_address>:<port>`, no password is required.
     - For JetBrains users:
         - Enable the option 'accept non-trusted certificates automatically' in `Settings -> Tools -> Server Certificates`.
         - Fill in the 'host name', 'port number', choose 'Proxy authentication', and enter your username in 'Login'. No password is required.

3. Provide your own information to start the proxy server, including:
     - `allowed_users.txt` file with a list of usernames. For example:
        ```
        user1 
        user2 
        ...
        usern
        ```
     - Config file containing Elasticsearch information and AAD settings (copy from `config-sample.ini`)
     - For AAD authentication, configure your Azure AD app registration details

4. **Authentication Setup:**
   - **With AAD**: Set `enable_aad_auth=true` in config.ini and provide AAD credentials via Bearer token
   - **Legacy Mode**: Keep `enable_aad_auth=false` and use the traditional username list with basic auth
   - **Hybrid Mode**: Enable both AAD and fallback to userlist for backward compatibility

5. Start the proxy server using the provided command.

6. Run `copilot-usage.py` or other file to obtain a CSV file. You can then perform any desired actions using a spreadsheet.

## Known Issues

If you encounter an error message indicating compatibility issues between mitmproxy and Python 3.8, you may need to reinstall certain packages with specific versions as prompted. 

## Next Plan ?

