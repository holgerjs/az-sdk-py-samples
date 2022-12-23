# How to retrieve a list of available services from the Azure Retail Rates Prices API

## Introduction

You probably know about the [Azure Retail Rates Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) [1] at `https://prices.azure.com/api/retail/prices`. It provides a "programmatic way to retrieve retail prices for all Azure services" [1] and does not require authentication - which makes it easy to query it from any kind of code (which was probably the idea behind creating it this way).
As a test, you can just head over to https://prices.azure.com/api/retail/prices in your browser and the API will provide the first 100 datasets of the price list.

The samples within this article will be based on Python but it could be done in a lot of other languages as well (technically, probably even plain `curl` within a bash script). However, due to the huge amount of pricing data that is returned by the API, Python has some advantages as there are some powerful libraries, such as Pandas, which is really beneficial when working with large datasets. 

## Retrieve a list of Available Services in a given Region

The [API Sample Calls](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices#api-sample-calls) [2] reveal that the API allows for some filter queries to be passed which allows us to narrow the retrieved data sets down by a bit - which certainly makes it easier to work with.

As per the documentation, [potential filters](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices#api-filters) [3] are:

- armRegionName
- Location
- meterId
- meterName
- productid
- skuId
- productName
- skuName
- serviceName
- serviceId
- serviceFamily
- priceType
- armSkuName

To start somewhere, the `armRegionName` could be relatively straightforward. For example, we could check for the [available regions in the documentation](https://azure.microsoft.com/en-us/explore/global-infrastructure/geographies/) [4] or use Az CLI or Azure PowerShell to query them (only when being authenticated though).

However, what about the `serviceName`? It is probably a common use case to retrieve prices for, let's say, Storage Services or Virtual Machine sizes. If we wanted to specify those, then it's necessary that we know what the API is expecting.
One way would be to try and browse through the text but that surely isn't fun.

What we could do though is retrieve price datasets for a given region and then filter out the unique values for the `serviceName` property.

### Create the Python Script

Note that the only library required here is the `requests` [library](https://pypi.org/project/requests/). We could then define the function as outlined below. 

```python
import requests

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
    
    service_names = []

    for record in all_price_records:
        service_names.append(record['serviceName'])

    unique_service_names = list(set(service_names))

    return unique_service_names
```

What above code does is:

- Construct the url including the filter value for a given region
- Send a request
- Add the response to a python dictionary
- Extract the `NextPageLink` and continue sending requests with all subsequent values of `NextPageLink` until it does not contain values any more. `NextPageLink` looks something like `"NextPageLink":"https://prices.azure.com:443/api/retail/prices?$skip=100"`, with the next value using `$skip=200` and so on, until there is nothing to skip any more and all values that match the filter query have been returned.
- The function then iterates through all returned records and extracts all `serviceName` values
- Lastly, it removes all duplicates and returns a list of unique values

### Let's Try

When we execute the function, we can just pass in any region for which we want to retrieve the list of available services. Let's say we wanted to retrieve the service names for the `East US` region. The armRegionName for this region would be `eastus` - basically the region name with all lowercase and no spaces. In this case the function would be executed as below:

```python
eastus_service_names = fetch_azure_services('eastus')
```

This will return a python `list` of 117 services, which you can check by getting the length of the list.

```python
print(len(eastus_service_names))
```

We can then sort the list and just print it out in alphabetical order.

```python
eastus_service_names.sort()
print(eastus_service_names)
```

The output should then be like this:

```bash
['API Management', 'Advanced Data Security', 'Advanced Threat Protection', 'App Configuration', 'Application Gateway', 'Application Insights', 'Automation', 'Azure API for FHIR', 'Azure Active Directory B2C', 'Azure Active Directory Domain Services', 'Azure Active Directory for External Identities', 'Azure Analysis Services', 'Azure App Service', 'Azure Applied AI Services', 'Azure Arc Enabled Databases', 'Azure Bastion', ...]
```

I've shortened it since there is no need to print the whole list here.

## Conclusion

We can query the [Azure Retail Rates Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) [1] through Python to get pricing details. In order to speed up potential requests against the API, it is beneficial to create a specific query. One of the commonly used values to query might be the `serviceName` property. Aforementioned example shows that we can also use the API to get all possible values for the `serviceName` property and we could then use these values in subsequent queries.

The method used in this example certainly has drawbacks - mainly performance, as we are always retrieving the whole price list for a given region, just to filter out the `serviceName`.

The example has only scratched the surface of the possibilities that are available with the API and we may be looking into it a little more in subsequent articles.

## References

| # | Title | URL |
| --- | --- | --- |
| 1 | Azure Retail Rates Prices API | https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices |
| 2 | API Sample Calls | https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices#api-sample-calls |
| 3 | API filters | https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices#api-filters |
| 4 | Azure geographies | https://azure.microsoft.com/en-us/explore/global-infrastructure/geographies/ |
| 5 | Requests Library | https://pypi.org/project/requests/ |
