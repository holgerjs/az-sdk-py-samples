## How to retrieve a Bearer Token for Azure in Python

Although it might not be necessary (since there is a well-maintained SDK for Azure), it could sometimes be helpful to create a Bearer token. This way one could connect to the Azure REST API directly and use the corresponding capabilities. Here is an example on how to us the Azure REST API in order to check whether a storage account name is already taken.

```python
from azure.identity import AzureCliCredential
import requests

# Get the logged on credentials - only for development purposes
credential = AzureCliCredential()

# Get the access token
access_token = credential.get_token("https://management.core.windows.net/")

# Add the Bearer prefix
bearer_token = f"Bearer {access_token.token}"

# Generate the details to create the REST request
r_url = 'https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Storage/checkNameAvailability?api-version=2022-09-01'
r_header = {'Content-Type': 'application/json', 'Authorization' : bearer_token}
r_body = {'name': '{storage_account_name}','type': 'Microsoft.Storage/storageAccounts'}

# Query the REST API
result = requests.post(headers=r_header,url=r_url,json=r_body)

# Print the details
print(result.json())
```
