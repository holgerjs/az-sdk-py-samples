## Python: List Storage Account Lifecycle Policies

I was looking into a way to list Storage Accounts that have (or do not have) [Lifecycle Policies](https://learn.microsoft.com/en-us/azure/storage/blobs/lifecycle-management-overview) enabled and output them as JSON.
The [Azure Samples Repository](https://github.com/Azure-Samples) does have a [sample for polices](https://github.com/Azure-Samples/azure-samples-python-management/blob/main/samples/storage/manage_management_policy.py), however, I couldn't figure out how to list policies since the sample only includes examples for Creating, Updating, Deleting and _Getting_ a specific policy. 
The latter requires the _Resource Group Name_, _Storage Account Name_ and _Management Policy Name_ as parameter which did not seem helpful.

However, a check against the REST API documentation for [Management Policies (Get)](https://learn.microsoft.com/en-us/rest/api/storagerp/management-policies/get?tabs=HTTP) reveals that the [URI Parameter](https://learn.microsoft.com/en-us/rest/api/storagerp/management-policies/get?tabs=HTTP#managementpolicyname) `managementPolicyName` should always be `default`.

Based on aforementioned sample, the following would work.

### Import Libraries

```python
from azure.identity import AzureCliCredential
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.storage import StorageManagementClient
import azure.mgmt.resourcegraph as arg
import json
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

In order to narrow down the results by a bit, I only queried Storage Accounts from one particular region.

```python
query = "resources | where type =~ 'Microsoft.Storage/storageAccounts' | where location =~ 'eastus'"

storage_accounts = resource_graph_query(query).data
```

### Retrieve the Storage Account Lifecycle Policies

```python
for storage_account in storage_accounts:
    storage_client = StorageManagementClient(credential=credential, subscription_id=storage_account.get('subscriptionId'))
    try:
        print(json.dumps(storage_client.management_policies.get(
            account_name=storage_account.get('name'), 
            resource_group_name=storage_account.get('resourceGroup'), 
            management_policy_name='default').as_dict()))
    except Exception:
        continue
```

If this worked, the output would be something like this:

```json
{
    "id": "/subscriptions/b5b916fd-22f9-4006-8344-372f9276562f/resourceGroups/resource_group_name/providers/Microsoft.Storage/storageAccounts/storageaccountname/managementPolicies/default",
    "name": "DefaultManagementPolicy",
    "type": "Microsoft.Storage/storageAccounts/managementPolicies",
    "last_modified_time": "2022-09-23T09:00:20.182687Z",
    "policy": {
        "rules": [
            {
                "enabled": true,
                "name": "Move Blobs to Cool After 1 Day",
                "type": "Lifecycle",
                "definition": {
                    "actions": {
                        "base_blob": {
                            "tier_to_cool": {
                                "days_after_modification_greater_than": 1.0
                            }
                        }
                    },
                    "filters": {
                        "blob_types": [
                            "blockBlob"
                        ]
                    }
                }
            }
        ]
    }
}
```
