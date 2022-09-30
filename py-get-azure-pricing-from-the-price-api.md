## Use the Azure Retail Rates Prices API to retrieve Data

The [Azure Retail Rates Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) provides users with a way to get retail prices for all Azure services without having to use the Azure Pricing Calculator or use the Azure portal. The API endpoint is at `https://prices.azure.com/api/retail/prices` and the [Azure Retail Prices overview](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) provides a few examples on how to use the API.

Below are some steps that I tested to try and query the API and import the results into a Pandas DataFrame.

### Import Libraries

```python
import requests
import pandas as pd
```

### Create the Filter and URL

```python
service_name = "Virtual Machines"
arm_region_name = "westeurope"

filter = f"?$filter=serviceName eq '{service_name}' and armRegionName eq '{arm_region_name}'"
url = f"https://prices.azure.com/api/retail/prices{filter}"
```

Using above example, the `filter` variable should now have the value `"https://prices.azure.com/api/retail/prices?$filter=serviceName eq 'Virtual Machines' and armRegionName eq 'westeurope'"`.

### Run the Query

* Since the API returns 100 values at once, we need to use the `NextPageLink` URL to continue the query. 
* Furthermore, we can see from the example output below that the relevant data  is under `Items`, which is why I only added the `Items` values to the dictionary.

```json
{
    "BillingCurrency": "USD",
    "CustomerEntityId": "Default",
    "CustomerEntityType": "Retail",
    "Items": [
        {
            "currencyCode": "USD",
            "tierMinimumUnits": 0.0,
            "retailPrice": 5.536,
            "unitPrice": 5.536,
            "armRegionName": "westeurope",
            "location": "EU West",
            "effectiveStartDate": "2020-06-01T00:00:00Z",
            "meterId": "ff052bc0-bdca-5b48-b96e-37c82dda2ae8",
            "meterName": "E64-32ds v4",
            "productId": "DZH318Z0CSHB",
            "skuId": "DZH318Z0CSHB/006X",
            "availabilityId": null,
            "productName": "Virtual Machines Edsv4 Series Windows",
            "skuName": "E64-32ds v4",
            "serviceName": "Virtual Machines",
            "serviceId": "DZH313Z7MMC8",
            "serviceFamily": "Compute",
            "unitOfMeasure": "1 Hour",
            "type": "DevTestConsumption",
            "isPrimaryMeterRegion": true,
            "armSkuName": "Standard_E64-32ds_v4"
        }
    ],
    "NextPageLink": "https://prices.azure.com:443/api/retail/prices?$filter=serviceName%20eq%20%27Virtual%20Machines%27%20and%20armRegionName%20eq%20%27westeurope%27&$skip=100",
    "Count": 100
}
```

The relevant while loop is shown below. 

```python
all_records = []
while True:
    if not url:
        break
    response = requests.get(url)
    if response.status_code == 200:
        json_data = response.json()
        url = json_data['NextPageLink'] # Fetch next link
        all_records = all_records + json_data['Items']
```

###  Import into a DataFrame

We now have all the values in a dictionary, which we can import into a Pandas DataFrame for further processing.

```python
df = pd.DataFrame.from_dict(all_records)
```

The `df` variable should now hold the corresponding data.

```python
     currencyCode  tierMinimumUnits  retailPrice  ...         armSkuName reservationTerm effectiveEndDate
0             USD               0.0     4.992000  ...   Standard_L48s_v3             NaN              NaN
1             USD               0.0     7.200000  ...   Standard_L48s_v3             NaN              NaN
2             USD               0.0     0.168710  ...      Standard_F16s             NaN              NaN
3             USD               0.0     0.458132  ...      Standard_F16s             NaN              NaN
4             USD               0.0     0.071264  ...   Standard_D4ds_v5             NaN              NaN
...           ...               ...          ...  ...                ...             ...              ...
7626          USD               0.0     1.411200  ...  Standard_D96as_v5             NaN              NaN
7627          USD               0.0     0.046000  ...     Standard_D4_v5             NaN              NaN
7628          USD               0.0     0.166000  ...     Standard_D4_v5             NaN              NaN
7629          USD               0.0     1.828000  ...      Standard_H16m             NaN              NaN
7630          USD               0.0     0.553000  ...      Standard_H16m             NaN              NaN
```

### Create a Function for re-usability

```python
import requests
import pandas as pd

def fetch_azure_prices(currency_code='EUR', service_name=None, region_name=None):
    '''Function fetches Prices from the Azure Retail Price API. Default currency is EUR. Regions must be lowercase. ServiceNames must be capitalized.'''

    criterias = []

    if service_name:
        criterias.append(f"serviceName eq '{service_name}'")

    if region_name:
        criterias.append(f"armRegionName eq '{region_name}'")


    if criterias:
        filter = f"?currencyCode='{currency_code}'&$filter="
        for criteria in criterias:
            if criteria != criterias[len(criterias)-1]:
                filter += f"{criteria} and "
            else:
                filter += f"{criteria}"
    else:
        filter = f"?currencyCode='{currency_code}'"

    url = f"https://prices.azure.com/api/retail/prices{filter}"

    all_price_records = []
    
    while True:
        if not url:
            break
        response = requests.get(url)
        if response.status_code == 200:
            json_data = response.json()
            url = json_data['NextPageLink'] # Fetch next link
            all_price_records = all_price_records + json_data['Items']
    
    return all_price_records
```

We can then use it like this:

```python
fetch_azure_prices(service_name='Storage', region_name='westeurope')
```

Along the same lines we could also use the API to check for service names in a particular region.

```python
import requests
import pandas as pd

def fetch_azure_services(region_name='westeurope'):
    '''Function fetches Service Names from the Azure Retail Price API based on a given region. Region must be lowercase.'''

    filter = f"?&$filter=armRegionName eq '{region_name}'"
    url = f"https://prices.azure.com/api/retail/prices{filter}"

    all_price_records = []
    
    while True:
        if not url:
            break
        response = requests.get(url)
        if response.status_code == 200:
            json_data = response.json()
            url = json_data['NextPageLink'] # Fetch next link
            all_price_records = all_price_records + json_data['Items']
    
    service_names = pd.DataFrame(all_price_records)['serviceName'].unique()

    return service_names
```