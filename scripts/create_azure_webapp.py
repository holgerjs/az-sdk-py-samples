#####################################
# Example Script: Create Azure WebApp
#####################################

import json

from azure.identity import AzureCliCredential
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.web.models import Site, SiteConfig

# Provide Subscription / Resource Group / App Service Plan / Web App details
my_subscription_id = '{subscription-id}'
my_resource_group_name = '{resource-group-name}'
my_app_service_plan_name = '{app-service-plan-name}'
my_webapp_name = '{webapp-name}'

# Authenticate to Azure and create client
my_credential = AzureCliCredential()
webapp_client = WebSiteManagementClient(credential=my_credential, subscription_id=my_subscription_id)

try:
    app_service_plan = webapp_client.app_service_plans.get(
        name = my_app_service_plan_name,
        resource_group_name = my_resource_group_name
    )
except Exception:
    print(f'Error: App Service Plan {my_app_service_plan_name} not found.')

availability_check = webapp_client.check_name_availability(
    name = my_webapp_name,
    type = 'Microsoft.Web/sites'
)

if availability_check.name_available == True:
    create_website = webapp_client.web_apps.begin_create_or_update(
        name = my_webapp_name,
        resource_group_name = my_resource_group_name,
        site_envelope = Site(
            location = 'westeurope',
            server_farm_id = app_service_plan.id,
            site_config = SiteConfig(
                python_version = '3.11',
                linux_fx_version = 'PYTHON|3.11'
            )
        )
    )
    # Output of the results as JSON
    print(json.dumps(create_website.result().as_dict(), sort_keys=True, indent=2))
else:
    print(f'Error: Name {my_webapp_name} is already in use.')