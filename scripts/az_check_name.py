from azure.identity import AzureCliCredential
from azure.mgmt.resource import SubscriptionClient
import azure.mgmt.resourcegraph as arg
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--name", type=str)
parser.add_argument("-t", "--type", type=str)

args = parser.parse_args()

r_name = args.name
r_type = args.type

# Authenticate
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

result = check_name_availability(resource_name=r_name, resource_type=r_type)
result_as_json = json.dumps(result)

print(result_as_json)
