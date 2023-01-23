##########################
# List Azure VM Extensions
##########################

from azure.identity import AzureCliCredential
from azure.mgmt.compute import ComputeManagementClient

def list_vm_extensions(credential, subscription_id, resource_group_name, vm_name):
    compute_client = ComputeManagementClient(credential=credential, subscription_id=subscription_id)
    vm_extensions = compute_client.virtual_machine_extensions.list(resource_group_name=resource_group_name, vm_name=vm_name)

    result_dict = []
    for vm_extension in vm_extensions.value:
        result_dict.append(vm_extension.as_dict())

    return result_dict

if __name__ == '__main__':
    # Get token from current Azure CLI Credentials
    my_credential = AzureCliCredential()

    # Define variables relevant for identifying the Virtual Machine of which the Extensions should be listed
    my_subscription_id = '{subscription-id}'
    my_resource_group_name = '{resource-group-name}'
    my_vm_name = '{vm-name}'

    # Execute Function to list VM Extensions
    my_vm_extensions = list_vm_extensions(my_credential, my_subscription_id, my_resource_group_name, my_vm_name)

    # Output
    print(my_vm_extensions)