## Use the Azure SDK for Python to query Blob Details such as Last Access Time

The following code can be used to query details on storage blobs. This could be usefule for determining whether or not blobs should be moved to another tier or whether lifecycle policies should be added or updated.

The code will query Azure Resource Graph for Storage Accounts in the tenant. Subsequently it will list Containers and Blobs from those Storage Accounts and add the details to a dictionary.

This requires the Storage Blob Data Reader role, otherwise the blobs will not be queried. For the script to continue, the `try-except` block is important, otherwise the script will stop when an access denied error occurs.


### Import Libraries

```python
from azure.identity import AzureCliCredential
from azure.mgmt.resource import SubscriptionClient
from azure.storage.blob import BlobServiceClient, ContainerClient
import azure.mgmt.resourcegraph as arg
import pandas as pd
```

### Get Credential

```python
credential = AzureCliCredential()
```

### Create Resource Graph Query Function

```python
# Create Query Function - See https://learn.microsoft.com/en-us/azure/governance/resource-graph/first-query-python

def resource_graph_query( query ):
    # Get your credentials from Azure CLI (development only!) and get your subscription list
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
    resource_graph_query = arg.models.QueryRequest(subscriptions=subscription_ids_dict, query=query, options=resource_graph_query_options)

    # Run query
    resource_graph_query_results = resource_graph_client.resources(resource_graph_query)

    # Show Python object
    return resource_graph_query_results
```

### Execute the Resource Graph Query

```python
query = "resources | where type =~ 'Microsoft.Storage/storageAccounts'"

storage_accounts = resource_graph_query(query).data
```

### Create Dictionary with Blob Details

```python
all_blobs = []

for storage_account in storage_accounts:
    storage_blob_endpoint = storage_account.get('properties').get('primaryEndpoints').get('blob')
    storage_account_subscription_id = storage_account.get('subscriptionId')
    storage_account_resource_group = storage_account.get('resourceGroup')
    storage_account_location = storage_account.get('location')
    storage_account_name = storage_account.get('name')

    blob_service_client = BlobServiceClient(account_url=storage_blob_endpoint, credential=credential)
    
    try:
        container_list = blob_service_client.list_containers()
        
        for container in container_list:

            container_client = ContainerClient(account_url=storage_blob_endpoint, container_name=container.name, credential=credential)
            blob_list = container_client.list_blobs()

            for blob in blob_list:
                blob_dict = {}
                blob_dict['subscription_id'] = storage_account_subscription_id
                blob_dict['resource_group'] = storage_account_resource_group
                blob_dict['location'] = storage_account_location
                blob_dict['storage_account_name'] = storage_account_name
                blob_dict['container'] = blob.container
                blob_dict['blob_name'] = blob.name
                blob_dict['creation_time'] = blob.creation_time
                blob_dict['blob_tier'] = blob.blob_tier
                blob_dict['blob_type'] = blob.blob_type
                blob_dict['has_legal_hold'] = blob.has_legal_hold
                blob_dict['blob_tier_change_time'] = blob.blob_tier_change_time
                blob_dict['last_accessed_on'] = blob.last_accessed_on
                blob_dict['last_modified'] = blob.last_modified

                all_blobs.append(blob_dict)

    except Exception:
        continue
```

### Add the Results to a Pandas DataFrame and output some of the details

```python
df = pd.DataFrame(all_blobs)
print(df[['subscription_id', 'resource_group', 'storage_account_name', 'container', 'blob_name', 'blob_tier', 'last_modified', 'last_accessed_on']])
```

Output:

```python
                          subscription_id       resource_group storage_account_name      container   blob_name blob_tier             last_modified          last_accessed_on
0    0e27a363-0ceb-4231-b89b-15d368f549e5  resource_group_name           stgacct001   container201   test1.txt      Cool 2022-09-22 19:05:20+00:00                       NaT      
1    0e27a363-0ceb-4231-b89b-15d368f549e5  resource_group_name           stgacct001   container201  test10.txt      Cool 2022-09-22 19:05:20+00:00                       NaT      
2    0e27a363-0ceb-4231-b89b-15d368f549e5  resource_group_name           stgacct001   container201  test12.txt      Cool 2022-09-22 19:05:21+00:00                       NaT      
3    0e27a363-0ceb-4231-b89b-15d368f549e5  resource_group_name           stgacct001   container201  test13.txt      Cool 2022-09-22 19:05:20+00:00                       NaT      
4    0e27a363-0ceb-4231-b89b-15d368f549e5  resource_group_name           stgacct001   container201  test14.txt      Cool 2022-09-22 19:05:21+00:00                       NaT      
..                                    ...                ...                  ...            ...         ...       ...                       ...                       ...      
98   0e27a363-0ceb-4231-b89b-15d368f549e5  resource_group_name           stgacct002    container06  test97.txt       Hot 2022-09-22 19:09:33+00:00                       NaT      
99   0e27a363-0ceb-4231-b89b-15d368f549e5  resource_group_name           stgacct002    container06  test98.txt       Hot 2022-09-22 19:09:33+00:00                       NaT      
100  0e27a363-0ceb-4231-b89b-15d368f549e5  resource_group_name           stgacct002    container06  test99.txt       Hot 2022-09-22 19:09:33+00:00                       NaT      
101  0e27a363-0ceb-4231-b89b-15d368f549e5  resource_group_name           stgacct003  container0102  text15.txt       Hot 2022-09-22 20:12:16+00:00 2022-09-22 20:12:16+00:00      
102  0e27a363-0ceb-4231-b89b-15d368f549e5  resource_group_name           stgacct003  container0102   text6.txt       Hot 2022-09-22 14:17:50+00:00 2022-09-22 20:13:32+00:00      
```

Note: The `last_accessed_on` value is only returned if [Access Time Tracking](https://learn.microsoft.com/en-us/azure/storage/blobs/lifecycle-management-policy-configure?tabs=azure-portal#optionally-enable-access-time-tracking) is enabled on the Storage Account.
