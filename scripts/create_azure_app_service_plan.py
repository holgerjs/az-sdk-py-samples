###############################################
# Example Script: Create Azure App Service Plan
###############################################

import uuid
import json

from azure.identity import AzureCliCredential
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.web.models import AppServicePlan, SkuDescription

# Create a random number
unique_deployment_number = str(uuid.uuid4().time_low)

# Provide Subscription / Resource Group details
my_subscription_id = '{subscription-id}'
my_resource_group_name = '{resource-group-name}'

# Authenticate to Azure and create client
my_credential = AzureCliCredential()
webapp_client = WebSiteManagementClient(credential=my_credential, subscription_id=my_subscription_id)

# Create the App Service Plan
create_plan = webapp_client.app_service_plans.begin_create_or_update(
    name = 'plan-'+unique_deployment_number,
    resource_group_name = my_resource_group_name,
    app_service_plan = AppServicePlan(
        location = 'westeurope',
        kind = 'linux',
        reserved = True,
        sku = SkuDescription(
            name = 'F1',
            capacity = 1,
            tier = 'Free'
        )
    )
)

# Output of the results as JSON
print(json.dumps(create_plan.result().as_dict(), sort_keys=True, indent=2))