## Generate List of Storage Accounts along with Policy Settings

In order to get an overview of storage accounts across the tenant and whether or not they have [(Lifecycle) Policies](py-list-storage-account-lifecycle-policies.md) enabled, the following Python code can help to generate a dictionary for a quick analysis. The aim was to see if storage accounts have Lifecycle (or similar) Policies enabled at all in order to derive recommendations for resource owners.

### Import Libraries

```python
from azure.identity import AzureCliCredential
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.storage import StorageManagementClient
import azure.mgmt.resourcegraph as arg
import pandas as pd
```

### Create the Credential Client

```python
credential = AzureCliCredential()
```

### Create the Resource Graph Query Function

This is taken from: https://learn.microsoft.com/en-us/azure/governance/resource-graph/first-query-python

```python
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

### Query all Storage Accounts

The Resource Graph query below would simply all Storage Accounts across the tenant. 

```python
query = "resources | where type =~ 'Microsoft.Storage/storageAccounts'"

storage_accounts = resource_graph_query(query).data
```

### Query Service- and Management Policy Settings

The code below would iterate through all Storage Accounts, get the corresponding Service and Policy Settings and add them to a dictionary.

```python
storage_account_lifecycle_results = []

for storage_account in storage_accounts:
    storage_client = StorageManagementClient(credential=credential, subscription_id=storage_account.get('subscriptionId'))
    
    storage_account_temp_dict = {}
    storage_account_temp_dict['subscription_id'] = storage_account.get('subscriptionId')
    storage_account_temp_dict['resource_group_name'] = storage_account.get('resourceGroup')
    storage_account_temp_dict['storage_account_name'] = storage_account.get('name')
    storage_account_temp_dict['kind'] = storage_account.get('kind')
    storage_account_temp_dict['sku_name'] = storage_account.get('sku').get('name')
    storage_account_temp_dict['has_lifecycle_policy'] = False
    storage_account_temp_dict['lifecycle_policy_enabled'] = False

    
    try:
        services = storage_client.blob_services.list(
            account_name=storage_account.get('name'), 
            resource_group_name=storage_account.get('resourceGroup'))

        for service in services:
            storage_account_temp_dict['delete_retention_policy_enabled'] = service.as_dict().get('delete_retention_policy').get('enabled')
            storage_account_temp_dict['restore_policy_enabled'] = service.as_dict().get('restore_policy').get('enabled')
            storage_account_temp_dict['delete_retention_policy_enabled'] = service.as_dict().get('delete_retention_policy').get('enabled')
            storage_account_temp_dict['container_delete_retention_policy_enabled'] = service.as_dict().get('container_delete_retention_policy').get('enabled')
            storage_account_temp_dict['last_access_time_tracking_policy_enabled'] = service.as_dict().get('last_access_time_tracking_policy').get('enable')

            if service.as_dict().get('last_access_time_tracking_policy').get('enable') == True:
                storage_account_temp_dict['tracking_granularity_in_days'] = service.as_dict().get('last_access_time_tracking_policy').get('tracking_granularity_in_days')
            else:
                storage_account_temp_dict['tracking_granularity_in_days'] = ''


        try:
            policies = storage_client.management_policies.get(
                account_name=storage_account.get('name'), 
                resource_group_name=storage_account.get('resourceGroup'), 
                management_policy_name='default').as_dict()

            if policies:
                for rule in (policies.get('policy').get('rules')):
                    if rule.get('type') == 'Lifecycle':
                        storage_account_temp_dict['has_lifecycle_policy'] = True
                        if rule.get('enabled') == True:
                            storage_account_temp_dict['lifecycle_policy_enabled'] = True    
            
        except Exception:
            storage_account_lifecycle_results.append(storage_account_temp_dict)
            continue
    
    except Exception:
            storage_account_lifecycle_results.append(storage_account_temp_dict)
            continue

    storage_account_lifecycle_results.append(storage_account_temp_dict)
```

### Further Processing

We can then add the dictionary to a Pandas DataFrame and display the information we want. I.E. if I wanted to know whether Storage Accounts have a lifecycle policy and whether they have last access time tracking enabled: 

```python
df = pd.DataFrame(storage_account_lifecycle_results)
df[['subscription_id', 'resource_group_name', 'storage_account_name', 'has_lifecycle_policy', 'last_access_time_tracking_policy_enabled']]
```

Output:

```python
                         subscription_id             resource_group_name  storage_account_name  has_lifecycle_policy last_access_time_tracking_policy_enabled
0   0667527a-2784-4689-9c5b-64bb4acb9690                          rg_001            stgacct001                 False                                      NaN
1   0667527a-2784-4689-9c5b-64bb4acb9690                          rg_002            stgacct002                 False                                      NaN
2   0667527a-2784-4689-9c5b-64bb4acb9690                          rg_003            stgacct003                 False                                      NaN
3   0667527a-2784-4689-9c5b-64bb4acb9690                          rg_003            stgacct004                 False                                      NaN
4   0667527a-2784-4689-9c5b-64bb4acb9690                          rg_003            stgacct005                 False                                      NaN
5   0667527a-2784-4689-9c5b-64bb4acb9690                          rg_003            stgacct006                 False                                      NaN
6   0667527a-2784-4689-9c5b-64bb4acb9690                          rg_003            stgacct007                 False                                      NaN
7   0667527a-2784-4689-9c5b-64bb4acb9690                          rg_004            stgacct008                 False                                      NaN
8   0667527a-2784-4689-9c5b-64bb4acb9690                          rg_005            stgacct009                 False                                      NaN
9   0667527a-2784-4689-9c5b-64bb4acb9690                          rg_006            stgacct010                  True                                     True
10  0667527a-2784-4689-9c5b-64bb4acb9690                          rg_007            stgacct011                 False                                      NaN
11  0667527a-2784-4689-9c5b-64bb4acb9690                          rg_008            stgacct012                 False                                     True
```
