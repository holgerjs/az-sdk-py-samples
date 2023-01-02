## Azure SDK for Python - How to check for Available Resource Names

If we wanted to check in Azure whether or not a given resource name is still available, we can do so relatively easily within the Azure Portal by navigating to the _All resources_ blade, making sure the subscription filter has all relevant subscriptions in scope and typing in the name that we want to check. This is fine for a manual approach - but how could we do this programmatically?

### Azure REST API

One option would be to use the [Azure REST API](https://learn.microsoft.com/en-us/rest/api/azure/) [1]. Most Azure services include a REST API capability for checking for available resource names - let's take [Storage Accounts](https://learn.microsoft.com/en-us/rest/api/storagerp/storage-accounts/check-name-availability?tabs=HTTP) as an example [2].

We could create a `POST` request against `https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.Storage/checkNameAvailability?api-version=2022-09-01` in order to verify the availability:

```python
from azure.identity import AzureCliCredential
import requests

credential = AzureCliCredential()
access_token = credential.get_token("https://management.core.windows.net/")
bearer_token = f"Bearer {access_token.token}"

r_url = 'https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Storage/checkNameAvailability?api-version=2022-09-01'
r_header = {'Content-Type': 'application/json', 'Authorization' : bearer_token}
r_body = {'name': '{storage_account_name}','type': 'Microsoft.Storage/storageAccounts'}

result = requests.post(headers=r_header,url=r_url,json=r_body)

print(result.json())
```

If the storage account name was already used, the response should be:

```python
{'nameAvailable': False, 'reason': 'AlreadyExists', 'message': 'The storage account named storage_account_name is already taken.'}
```

Otherwise, the response would simply be:

```python
{'nameAvailable': True}
```

As you can see, this works well, however, there are drawbacks:

- Not all Azure services offer the capability for checking the available name through the Azure REST API.
- If they do, we need to know the REST API URL.
- We can only run the query against a single subscription.

To resolve the third point, we could first receive a list of available subscriptions and then iterate through each subscription and query the REST API on a per-subscription basis. This would work as well, however the other two drawbacks would still apply.

### Azure SDK for Python

A simpler approach - since we are using Python anyways in this example - would be to use the [Azure SDK for Python](https://learn.microsoft.com/en-us/azure/developer/python/sdk/azure-sdk-overview) [6].

```python
from azure.identity import AzureCliCredential
from azure.mgmt.storage import StorageManagementClient
credential = AzureCliCredential()

subscription_id = '{subscription_id}'
storage_account_name = '{storage_account_name}'

storage_client = StorageManagementClient(credential, subscription_id)



availability_result = storage_client.storage_accounts.check_name_availability(
    { 
        "name": storage_account_name
    }
)

print(availability_result)
```

Similar to what we saw when querying the Azure REST API, the result indicating that the name was already used would look like this:

```python
{'additional_properties': {}, 'name_available': False, 'reason': 'AlreadyExists', 'message': 'The storage account named storage_account_name is already taken.'}
```

If the name was still available, the response would be:

```python
{'additional_properties': {}, 'name_available': True, 'reason': None, 'message': None}
```

This approach includes similar drawbacks as using the REST API directly.

- Not all Azure services offer the capability for checking the available name.
- If they, do we need to import the corresponding Python library.
- We can only run the query against a single subscription.

Again, the last point can be remediated by using the [SubscriptionClient Class](https://learn.microsoft.com/en-us/python/api/azure-mgmt-subscription/azure.mgmt.subscription.subscriptionclient?view=azure-python) [4], generating a list of subscription id's and iterating through it - however, the approach might not be very flexible.

### Azure Resource Graph

Fortunately, Azure offers a great capability called [Azure Resource Graph](https://learn.microsoft.com/en-us/azure/governance/resource-graph/overview) [3], which we can also use through the Azure SDK for Python.

Below, we see two functions created. `resource_graph_query` is used to run a [query against Azure Resource Graph](https://learn.microsoft.com/en-us/azure/governance/resource-graph/first-query-python) [5]. `check_name_availability` is then used to create and execute the query against a specific name - and optionally, resource type.

```python
from azure.identity import AzureCliCredential
from azure.mgmt.resource import SubscriptionClient
import azure.mgmt.resourcegraph as arg

credential = AzureCliCredential()

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

def check_name_availability(resource_name, resource_type=None):
    
    if(resource_type):
        rg_query = f"Resources | where name =~ '{resource_name}' | where type =~ '{resource_type}'"
    else:
        rg_query = f"Resources | where name =~ '{resource_name}'"
    
    
    rg_results = resource_graph_query(rg_query)
    
    results_dict = []

    if(rg_results.data):
        availability = False
    else:
        availability = True

    results_dict = dict({
        'resource_name': resource_name,
        'available': availability
    })
    
    return results_dict

r_name = '{storage_account_name}'
r_type = 'Microsoft.Storage/storageAccounts'

result = check_name_availability(resource_name=r_name, resource_type=r_type)

print(result)
```

Thanks to Azure Resource Graph, we can just pass a list of subscription id's and query them all at once with a single call. Particularly when checking hundreds or thousands of subscriptions at one, Resource Graph improves performance significantly.

The results of above code would be like this (but could obviously be improved or extended) if the resource existed already:

```python
{'resource_name': 'storage_account_name', 'available': False}
```

Contrarily, if the resource did not exist yet, the response would be `True`:

```python
{'resource_name': 'storage_account_name', 'available': True}
```

### References

| # | Title | URL |
| --- | --- | --- |
| 1 | Azure REST API reference | https://learn.microsoft.com/en-us/rest/api/azure/ |
| 2 | Storage Accounts - Check Name Availability | https://learn.microsoft.com/en-us/rest/api/storagerp/storage-accounts/check-name-availability?tabs=HTTP |
| 3 | What is Azure Resource Graph? | https://learn.microsoft.com/en-us/azure/governance/resource-graph/overview |
| 4 | SubscriptionClient Class | https://learn.microsoft.com/en-us/python/api/azure-mgmt-subscription/azure.mgmt.subscription.subscriptionclient?view=azure-python |
| 5 | Quickstart: Run your first Resource Graph query using Python | https://learn.microsoft.com/en-us/azure/governance/resource-graph/first-query-python |
| 6 | Use the Azure libraries (SDK) for Python | https://learn.microsoft.com/en-us/azure/developer/python/sdk/azure-sdk-overview |
