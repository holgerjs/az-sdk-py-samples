###############################################
# Example Script: Create Deployment from GitHub
###############################################


from azure.identity import AzureCliCredential
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.web.models import SiteSourceControl

# Provide Subscription / Resource Group / Web App details
my_subscription_id = '{subscription-id}'
my_resource_group_name = '{resource-group-name}'
my_webapp_name = '{webapp-name}'

# Authenticate to Azure and create client
my_credential = AzureCliCredential()


webapp_client = WebSiteManagementClient(credential=my_credential, subscription_id=my_subscription_id)
source_control = webapp_client.web_apps.begin_create_or_update_source_control(
    resource_group_name = my_resource_group_name,
    name = my_webapp_name,
    site_source_control = SiteSourceControl(
        is_manual_integration = True,
        repo_url = 'https://github.com/{repository-url}',
        branch = 'master'
    )
)