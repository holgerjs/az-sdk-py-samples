## Python: Use Azure Resource Graph to extract Storage Account Security Settings

Querying Azure Resource Graph is a super-fast way to get information across multiple subscriptions within am Azure tenant. In the example below I played around with the Python SDK to query some Storage Account security configuration settings.

### Import Libraries

```python
from azure.identity import AzureCliCredential
from azure.mgmt.resource import SubscriptionClient
import azure.mgmt.resourcegraph as arg
import pandas as pd
```

### Create Query Function

The code is taken from here: https://learn.microsoft.com/en-us/azure/governance/resource-graph/first-query-python

```python
def resource_graph_query(query_string):
    # Get your credentials from Azure CLI (development only!) and get your subscription list
    credential = AzureCliCredential()
    subs_client = SubscriptionClient(credential)
    subscriptions_dict = []
    
    for subscription in subs_client.subscriptions.list():
        subscriptions_dict.append(subscription.as_dict())
    
    subscription_ids_dict = []
    
    for subscription in subscriptions_dict:
        subscription_ids_dict.append(subscription.get('subscription_id'))

    # Create Azure Resource Graph client and set options
    resource_graph_client = arg.ResourceGraphClient(credential)
    resource_graph_query_options = arg.models.QueryRequestOptions(result_format="objectArray")

    # Create query
    resource_graph_query = arg.models.QueryRequest(subscriptions=subscription_ids_dict, query=query_string, options=resource_graph_query_options)

    # Run query
    resource_graph_query_results = resource_graph_client.resources(resource_graph_query)

    # Return Python object
    return resource_graph_query_results
```

### Define the Query

```python
storage_accounts_sec_settings_query = """
resources
| where type =~ 'Microsoft.Storage/storageAccounts'
| extend allowBlobPublicAccess = parse_json(properties).allowBlobPublicAccess
| extend allowSharedKeyAccess = parse_json(properties).allowSharedKeyAccess
| extend naclsDefaultAction = parse_json(properties).networkAcls.defaultAction
| extend naclsBypass = parse_json(properties).networkAcls.bypass
| extend minimumTlsVersion = parse_json(properties).minimumTlsVersion
| extend supportsHttpsTrafficOnly = parse_json(properties).supportsHttpsTrafficOnly
| extend skuName = parse_json(sku).name
| extend blobServiceEncryptionKeyType = parse_json(properties).encryption.services.blob.keyType
| extend fileServiceEncryptionKeyType = parse_json(properties).encryption.services.file.keyType
| extend requireInfrastructureEncryption = parse_json(properties).encryption.requireInfrastructureEncryption
| extend allowCrossTenantReplication = parse_json(properties).allowCrossTenantReplication
| extend defaultToOAuthAuthentication = parse_json(properties).defaultToOAuthAuthentication
| project subscriptionId, resourceGroup, name, kind, skuName, allowBlobPublicAccess, allowSharedKeyAccess, naclsDefaultAction, naclsBypass, minimumTlsVersion, supportsHttpsTrafficOnly, blobServiceEncryptionKeyType, fileServiceEncryptionKeyType, requireInfrastructureEncryption, allowCrossTenantReplication, defaultToOAuthAuthentication
"""
```

### Execute the Query

```python
storage_accounts_sec_settings = resource_graph_query(storage_accounts_sec_settings_query)
```

### Create a DataFrame

```python
df = pd.DataFrame(storage_accounts_sec_settings.data)
```

### Filter for certain Criteria

Instead of the full DataFrame, we can filter for certain settings, i.E. see how many storage accounts still support the outdated TLS1.0 protocol.

```python
print(df['minimumTlsVersion'].value_counts())
```

Output:

```python
TLS1_2    10
TLS1_0     2
Name: minimumTlsVersion, dtype: int64
```

If we wanted to know which accounts in question have the specific protocol enabled, we can display them accordingly.

```python
df_tls_outdated = df.loc[df['minimumTlsVersion'] != 'TLS1_2']
print(df_tls_outdated.iloc[:,0:3])
```

Output:

```python
                         subscriptionId       resourceGroup                  name
0  66a91fdb-0732-4656-a87a-158b9efe1dab     test_rg_name_01         stgacctname01
6  66a91fdb-0732-4656-a87a-158b9efe1dab     test_rg_name_02         stgacctname02
```
