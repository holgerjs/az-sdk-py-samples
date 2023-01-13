## Azure SDK for Python: Retrieve Virtual Machine Image Details

The [Azure SDK for Python](https://learn.microsoft.com/en-us/azure/developer/python/sdk/azure-sdk-overview) includes capabilities that allow users to retrieve Virtual Machine image details, such as the publisher names, offers, SKUs and the image details itself. [4] I was reading a thread on Stack Overflow and got interested in this functionality - and here is the corresponding write-up.

The corresponding library is the [Azure Management Compute library](https://pypi.org/project/azure-mgmt-compute/) which includes the `ComputeManagementClient` class which in turn has a function called [`virtual_machine_images.list`](https://learn.microsoft.com/en-us/python/api/azure-mgmt-compute/azure.mgmt.compute.v2022_08_01.operations.virtualmachineimagesoperations?view=azure-python#azure-mgmt-compute-v2022-08-01-operations-virtualmachineimagesoperations-list). [1][2] However, this function requires further parameters:

- `location`
- `publisher_name`
- `offer`
- `skus`

Except for location, we may not have all the required details at hand to retrieve the image details. Further relevant functions include:

- [list_publishers](https://learn.microsoft.com/en-us/python/api/azure-mgmt-compute/azure.mgmt.compute.v2022_08_01.operations.virtualmachineimagesoperations?view=azure-python#azure-mgmt-compute-v2022-08-01-operations-virtualmachineimagesoperations-list-publishers) - which has `location` as a required parameter
- [list_offers](https://learn.microsoft.com/en-us/python/api/azure-mgmt-compute/azure.mgmt.compute.v2022_08_01.operations.virtualmachineimagesoperations?view=azure-python#azure-mgmt-compute-v2022-08-01-operations-virtualmachineimagesoperations-list-offers) - which requires `location` and `publisher_name`
- [list_skus](https://learn.microsoft.com/en-us/python/api/azure-mgmt-compute/azure.mgmt.compute.v2022_08_01.operations.virtualmachineimagesoperations?view=azure-python#azure-mgmt-compute-v2022-08-01-operations-virtualmachineimagesoperations-list-skus) - which requires  `location`, `publisher_name` and `offer` parameters

Now that looks like a few for-loops would be helpful until we could finally list all VM images. But would we even want this? Maybe. Given that there are thousands of images available in each region, maybe _rather not_ as it would take a significant amount of time. So, maybe build our own function to be flexible?

Let's try and go through this step by step and take a look at each of those functions.

First, we would need the appropriate Azure SDK for Python libraries for authentication and compute management:

- [azure-identity](https://pypi.org/project/azure-identity/) [3]
- [azure-mgmt-compute](https://pypi.org/project/azure-mgmt-compute/) [1]

```python
from azure.identity import AzureCliCredential
from azure.mgmt.compute import ComputeManagementClient
```

We'd need to define our Credentials, Subscription ID and Azure Location.

```python
my_credential = AzureCliCredential()
my_subscription_id = "{subscription-id}"
my_location = "{azure-location}"
```

Now we could create the client and collect the list of Publishers.

```python
compute_client = ComputeManagementClient(credential=my_credential, subscription_id=my_subscription_id)
img_publishers = compute_client.virtual_machine_images.list_publishers(location=my_location)
```

At this point, if we were to display the content of the `img_publishers` variable, it would show loads of objects:

```
[...<azure.mgmt.compute.v2022_08_01.models._models_py3.VirtualMachineImageResource object at 0x7fb8d85c0790>, <azure.mgmt.compute.v2022_08_01.models._models_py3.VirtualMachineImageResource object at 0x7fb8d85c07c0>, <azure.mgmt.compute.v2022_08_01.models._models_py3.VirtualMachineImageResource object at 0x7fb8d85c07f0>, <azure.mgmt.compute.v2022_08_01.models._models_py3.VirtualMachineImageResource object at 0x7fb8d85c0820>, <azure.mgmt.compute.v2022_08_01.models._models_py3.VirtualMachineImageResource object at 0x7fb8d85c0850>, <azure.mgmt.compute.v2022_08_01.models._models_py3.VirtualMachineImageResource object at 0x7fb8d85c0880>...]
```

Just to get an idea of how many publishers there are (I used `northeurope` as Azure location):

```
>>> len(img_publishers)
1871
```

Let's just pick one randomly, to see what details are contained within these objects:

```python
>>> print(img_publishers[1200])
{'additional_properties': {}, 'id': '/Subscriptions/{subscription-id}/Providers/Microsoft.Compute/Locations/northeurope/Publishers/MicrosoftSQLServer', 'name': 'MicrosoftSQLServer', 'location': 'northeurope', 'tags': None, 'extended_location': None}
```

The item of interest seems to be the name. We can now use that to go further and query the corresponding offers that belong to this publisher. Let's stick to above example in order to keep it simple for the moment.

```python
offers = compute_client.virtual_machine_images.list_offers(location=my_location, publisher_name=img_publishers[1200].name)
```

Let's see how many offers are there from `MicrosoftSQLServer`:

```
>>> len(offers)
37
```

We'll again pick one of them to see what properties might be important - and it's, again, `name`. 

```python
>>> print(offers[36])
{'additional_properties': {}, 'id': '/Subscriptions/{subscription-id}/Providers/Microsoft.Compute/Locations/northeurope/Publishers/MicrosoftSQLServer/ArtifactTypes/VMImage/Offers/sql2022-ws2022', 'name': 'sql2022-ws2022', 'location': 'northeurope', 'tags': None, 'extended_location': None}
```

Next stop: SKUs

```python
skus = compute_client.virtual_machine_images.list_skus(location=my_location,publisher_name=img_publishers[1200].name, offer=offers[36].name)
```

Telling by the length of the list, there are only four SKUs for this particular offer:

```python
>>> len(skus)
4
```

And picking one of them reveals that, again, the `name` property is what we need.

```python
>>> print(skus[0])
{'additional_properties': {'properties': {'automaticOSUpgradeProperties': {'automaticOSUpgradeSupported': False}}}, 'id': '/Subscriptions/{subscription-id}/Providers/Microsoft.Compute/Locations/northeurope/Publishers/MicrosoftSQLServer/ArtifactTypes/VMImage/Offers/sql2022-ws2022/Skus/enterprise-gen2', 'name': 'enterprise-gen2', 'location': 'northeurope', 'tags': None, 'extended_location': None}
```

Since we now have everything together we can finally call the `list()` function.

```python
images = compute_client.virtual_machine_images.list(location=my_location, publisher_name=img_publishers[1200].name, offer=offers[36].name, skus=skus[0].name)
```

We now have identified 2 images:

```python
>>> len(images)
2
```

And from that we can get an idea about what the outcome will be:

```python
>>> print(images[0])
{'additional_properties': {}, 'id': '/Subscriptions/{subscription-id}/Providers/Microsoft.Compute/Locations/northeurope/Publishers/MicrosoftSQLServer/ArtifactTypes/VMImage/Offers/sql2022-ws2022/Skus/enterprise-gen2/Versions/16.0.221025', 'name': '16.0.221025', 'location': 'northeurope', 'tags': None, 'extended_location': None}
```

Picking items from the individual lists is a) not much fun and b) does not scale very well. As next step we might want to wrap some for-loops around these.
So, let's take a step back and assume we were back at a point where we imported our libraries and defined `my_credential`, `my_subscription_id` and `my_location` variables. We would also have created the `ComputeManagementClient` and dumped the list of publishers into the `img_publishers` variable.

```python
from azure.identity import AzureCliCredential
from azure.mgmt.compute import ComputeManagementClient

my_credential = AzureCliCredential()
my_subscription_id = "{subscription-id}"
my_location = "{azure-location}"

compute_client = ComputeManagementClient(credential=my_credential, subscription_id=my_subscription_id)
img_publishers = compute_client.virtual_machine_images.list_publishers(location=my_location)
```

From here on we could iterate through the Publishers, Offers, SKUs and finally Images.

```python
for publisher in img_publishers:
    offers = compute_client.virtual_machine_images.list_offers(location=my_location, publisher_name=publisher.name)
    for offer in offers:
        skus = compute_client.virtual_machine_images.list_skus(location=my_location,publisher_name=publisher.name, offer=offer.name)
        for sku in skus:
            images = compute_client.virtual_machine_images.list(location=my_location, publisher_name=publisher.name, offer=offer.name, skus=sku.name)
            for image in images:
                print(image)
```

It shouldn't take long for us to see some results on screen (cancelled the processing using CTRL-C, otherwise this would take ages to get all the images):

```python
...
{'additional_properties': {}, 'id': '/Subscriptions/{subscription-id}/Providers/Microsoft.Compute/Locations/northeurope/Publishers/aod/ArtifactTypes/VMImage/Offers/win2019azpolicy/Skus/win2019azpolicy/Versions/0.0.1', 'name': '0.0.1', 'location': 'northeurope', 'tags': None, 'extended_location': None}
{'additional_properties': {}, 'id': '/Subscriptions/{subscription-id}/Providers/Microsoft.Compute/Locations/northeurope/Publishers/aod/ArtifactTypes/VMImage/Offers/win2019azpolicy/Skus/win2019azpolicy/Versions/0.0.3', 'name': '0.0.3', 'location': 'northeurope', 'tags': None, 'extended_location': None}
{'additional_properties': {}, 'id': '/Subscriptions/{subscription-id}/Providers/Microsoft.Compute/Locations/northeurope/Publishers/apigee/ArtifactTypes/VMImage/Offers/apigee-edge/Skus/apigee-edge-4-15-07/Versions/1.0.0', 'name': '1.0.0', 'location': 'northeurope', 'tags': None, 'extended_location': None}
{'additional_properties': {}, 'id': '/Subscriptions/{subscription-id}/Providers/Microsoft.Compute/Locations/northeurope/Publishers/apigee/ArtifactTypes/VMImage/Offers/apigee-edge/Skus/apigee-edge-private-cloud/Versions/4.16.05', 'name': '4.16.05', 'location': 'northeurope', 'tags': None, 'extended_location': None}
...
```

While this works, it might not be very helpful for further processing. We might want to add the details to a custom dictionary? If so, the loops could be put out like this:

```python
for publisher in img_publishers:
    offers = compute_client.virtual_machine_images.list_offers(location=my_location, publisher_name=publisher.name)
    for offer in offers:
        skus = compute_client.virtual_machine_images.list_skus(location=my_location,publisher_name=publisher.name, offer=offer.name)
        for sku in skus:
            images = compute_client.virtual_machine_images.list(location=my_location, publisher_name=publisher.name, offer=offer.name, skus=sku.name)
            for image in images:
                image_dict = dict({
                    'publisherName' : publisher.name,
                    'offerName' : offer.name,
                    'skuName': sku.name,
                    'imageName': image.name
                })
                print(image_dict)
```

The dictionary would look something like this (again CTRL-C'd after a few seconds to stop the processing as it would take too long):

```python
...
{'publisherName': 'aod', 'offerName': 'win2019azpolicy', 'skuName': 'win2019azpolicy', 'imageName': '0.0.1'}
{'publisherName': 'aod', 'offerName': 'win2019azpolicy', 'skuName': 'win2019azpolicy', 'imageName': '0.0.3'}
{'publisherName': 'apigee', 'offerName': 'apigee-edge', 'skuName': 'apigee-edge-4-15-07', 'imageName': '1.0.0'}
{'publisherName': 'apigee', 'offerName': 'apigee-edge', 'skuName': 'apigee-edge-private-cloud', 'imageName': '4.16.05'}
...
```

If we wanted to add those individual dictionary to a large one to process in the end, we could append the image details rather then printing them out on screen.

```python
results = []

for publisher in img_publishers:
    offers = compute_client.virtual_machine_images.list_offers(location=my_location, publisher_name=publisher.name)
    for offer in offers:
        skus = compute_client.virtual_machine_images.list_skus(location=my_location,publisher_name=publisher.name, offer=offer.name)
        for sku in skus:
            images = compute_client.virtual_machine_images.list(location=my_location, publisher_name=publisher.name, offer=offer.name, skus=sku.name)
            for image in images:
                image_dict = dict({
                    'publisherName' : publisher.name,
                    'offerName' : offer.name,
                    'skuName': sku.name,
                    'imageName': image.name
                })
                results.append(image_dict)
```

This would still run a _very_ long time though. So maybe we would want to add some query functionality? Let's create a function.

```python
def get_vm_images(credential, subscription_id, location, image_publisher):
    results = []

    compute_client = ComputeManagementClient(credential=credential, subscription_id=subscription_id)
    img_publishers = compute_client.virtual_machine_images.list_publishers(location=location)
    
    for publisher in img_publishers:
        if image_publisher in publisher.name:
            offers = compute_client.virtual_machine_images.list_offers(location=location, publisher_name=publisher.name)
            for offer in offers:
                skus = compute_client.virtual_machine_images.list_skus(location=location,publisher_name=publisher.name, offer=offer.name)
                for sku in skus:
                    images = compute_client.virtual_machine_images.list(location=location, publisher_name=publisher.name, offer=offer.name, skus=sku.name)
                    for image in images:
                        image_dict = dict({
                            'publisherName' : publisher.name,
                            'offerName' : offer.name,
                            'skuName': sku.name,
                            'imageName': image.name
                        })
                        results.append(image_dict)
        else:
            pass
    return results
```

By checking whether the value of `image_publisher` (which we pass to the function) is part of the `publisher.name` value, we could make sure that only if there is a match, Images would be queried and added to the results dictionary: `if image_publisher in publisher.name`.

We could try this:

```python
>>> get_vm_images(credential=my_credential, subscription_id=my_subscription_id, location=my_location, image_publisher="canonical")
```

Hm, we get nothing:

```python
[]
```

So, maybe capitalization matters.

```python
>>> get_vm_images(credential=my_credential, subscription_id=my_subscription_id, location=my_location, image_publisher="Canonical")
```

And indeed, this seems to work better:

```python
[...{'publisherName': 'Canonical', 'offerName': 'UbuntuServer', 'skuName': '19_10-daily-gen2', 'imageName': '19.10.202006110'}, {'publisherName': 'Canonical', 'offerName': 'UbuntuServer', 'skuName': '19_10-daily-gen2', 'imageName': '19.10.202007020'}, {'publisherName': 'Canonical', 'offerName': 'UbuntuServer', 'skuName': '19_10-daily-gen2', 'imageName': '19.10.202007030'}, {'publisherName': 'Canonical', 'offerName': 'UbuntuServer', 'skuName': '19_10-daily-gen2', 'imageName': '19.10.202007070'}, {'publisherName': 'Canonical', 'offerName': 'UbuntuServer', 'skuName': '19_10-daily-gen2', 'imageName': '19.10.202007080'}, {'publisherName': 'Canonical', 'offerName': 'UbuntuServer', 'skuName': '19_10-daily-gen2', 'imageName': '19.10.202007090'}, {'publisherName': 'Canonical', 'offerName': 'UbuntuServer', 'skuName': '19_10-daily-gen2', 'imageName': '19.10.202007100'}]
```

So, something else to account for I presume... since there might be multiple variations. Maybe some publishers are typed all lowercase, others require capitalization - we could replace above if-clause (I'm sure there are more elegant ways though) by: `if image_publisher.lower() in publisher.name or image_publisher.capitalize() in publisher.name:`

The function code would now look like this

```python
def get_vm_images(credential, subscription_id, location, image_publisher):
    results = []

    compute_client = ComputeManagementClient(credential=credential, subscription_id=subscription_id)
    img_publishers = compute_client.virtual_machine_images.list_publishers(location=location)
    
    for publisher in img_publishers:
        if image_publisher.lower() in publisher.name or image_publisher.capitalize() in publisher.name:
            offers = compute_client.virtual_machine_images.list_offers(location=location, publisher_name=publisher.name)
            for offer in offers:
                skus = compute_client.virtual_machine_images.list_skus(location=location,publisher_name=publisher.name, offer=offer.name)
                for sku in skus:
                    images = compute_client.virtual_machine_images.list(location=location, publisher_name=publisher.name, offer=offer.name, skus=sku.name)
                    for image in images:
                        image_dict = dict({
                            'publisherName' : publisher.name,
                            'offerName' : offer.name,
                            'skuName': sku.name,
                            'imageName': image.name
                        })
                        results.append(image_dict)
        else:
            pass

    return results
```

With this in place, we should be able to get results even when passing something like `canonical` instead of `Canonical`.

Now we have this very basic function in place. This could be used in various ways. I.E. to produce json output...

```python
import json

canonical_images = get_vm_images(credential=my_credential, subscription_id=my_subscription_id, location=my_location, image_publisher="canonical")
print(json.dumps(canonical_images))
```

```python
[ ... {"publisherName": "Canonical", "offerName": "UbuntuServer", "skuName": "19_10-daily-gen2", "imageName": "19.10.202006110"}, {"publisherName": "Canonical", "offerName": "UbuntuServer", "skuName": "19_10-daily-gen2", "imageName": "19.10.202007020"}, {"publisherName": "Canonical", "offerName": "UbuntuServer", "skuName": "19_10-daily-gen2", "imageName": "19.10.202007030"}, {"publisherName": "Canonical", "offerName": "UbuntuServer", "skuName": "19_10-daily-gen2", "imageName": "19.10.202007070"}, {"publisherName": "Canonical", "offerName": "UbuntuServer", "skuName": "19_10-daily-gen2", "imageName": "19.10.202007080"}, {"publisherName": "Canonical", "offerName": "UbuntuServer", "skuName": "19_10-daily-gen2", "imageName": "19.10.202007090"}, {"publisherName": "Canonical", "offerName": "UbuntuServer", "skuName": "19_10-daily-gen2", "imageName": "19.10.202007100"}]
```

...or to load into a Pandas DataFrame:

```python
import pandas as pd

canonical_images = get_vm_images(credential=my_credential, subscription_id=my_subscription_id, location=my_location, image_publisher="canonical")
df = pd.DataFrame(canonical_images)

print(df)
```

```python
>>> print(df)
     publisherName                                     offerName           skuName        imageName
0        Canonical  0001-com-ubuntu-confidential-vm-experimental             18_04   18.04.20210309
1        Canonical  0001-com-ubuntu-confidential-vm-experimental        18_04-gen2   18.04.20210309
2        Canonical  0001-com-ubuntu-confidential-vm-experimental             20_04   20.04.20210309
3        Canonical  0001-com-ubuntu-confidential-vm-experimental        20_04-gen2   20.04.20210309
4        Canonical         0001-com-ubuntu-confidential-vm-focal     20_04-lts-cvm  20.04.202111100
...            ...                                           ...               ...              ...
4546     Canonical                                  UbuntuServer  19_10-daily-gen2  19.10.202007030
4547     Canonical                                  UbuntuServer  19_10-daily-gen2  19.10.202007070
4548     Canonical                                  UbuntuServer  19_10-daily-gen2  19.10.202007080
4549     Canonical                                  UbuntuServer  19_10-daily-gen2  19.10.202007090
4550     Canonical                                  UbuntuServer  19_10-daily-gen2  19.10.202007100

[4551 rows x 4 columns]
```

Finally, here is the full script (which can also be found [here](scripts/get-vm-images.py)). I've added an additional if-clause so that the function would also accept `None` as image publisher - however, this is not recommended really as it takes _a lot_ of time.

```python
from azure.identity import AzureCliCredential
from azure.mgmt.compute import ComputeManagementClient

def get_vm_images(credential, subscription_id, location, image_publisher=None):
    results = []

    compute_client = ComputeManagementClient(credential=credential, subscription_id=subscription_id)
    img_publishers = compute_client.virtual_machine_images.list_publishers(location=location)
    
    if image_publisher:
        for publisher in img_publishers:
            if image_publisher.lower() in publisher.name or image_publisher.capitalize() in publisher.name:
                offers = compute_client.virtual_machine_images.list_offers(location=location, publisher_name=publisher.name)
                for offer in offers:
                    skus = compute_client.virtual_machine_images.list_skus(location=location,publisher_name=publisher.name, offer=offer.name)
                    for sku in skus:
                        images = compute_client.virtual_machine_images.list(location=location, publisher_name=publisher.name, offer=offer.name, skus=sku.name)
                        for image in images:
                            image_dict = dict({
                                'publisherName' : publisher.name,
                                'offerName' : offer.name,
                                'skuName': sku.name,
                                'imageName': image.name
                            })

                            results.append(image_dict)
            else:
                pass
    else:
        for publisher in img_publishers:
            offers = compute_client.virtual_machine_images.list_offers(location=location, publisher_name=publisher.name)
            for offer in offers:
                skus = compute_client.virtual_machine_images.list_skus(location=location,publisher_name=publisher.name, offer=offer.name)
                for sku in skus:
                    images = compute_client.virtual_machine_images.list(location=location, publisher_name=publisher.name, offer=offer.name, skus=sku.name)
                    for image in images:
                        image_dict = dict({
                            'publisherName' : publisher.name,
                            'offerName' : offer.name,
                            'skuName': sku.name,
                            'imageName': image.name
                        })

                        results.append(image_dict)
    
    return results


my_credential = AzureCliCredential()
my_subscription_id = "{subscription-id}"

get_vm_images(credential=my_credential, subscription_id=my_subscription_id, location="eastus", image_publisher="Canonical")
```

I hope this might be helpful for someone who wants to test and try the Azure SDK for Python - I certainly enjoyed looking into it. Let me just add a few bullet points:

- Above code samples are just for fun and learning and should not be used in production since there are a lot of important things missing such as error-handling and logging.
- There are surely more elegant ways of doing the same with Python.
- The Azure CLI is capable of listing all images _out of the box_: `az vm image list --all`

That's it for the moment - thanks for reading.

## References

|#|Title|URL|Accessed-On|
|---|---|---|---|
| 1 | azure-mgmt-compute 29.0.0 | https://pypi.org/project/azure-mgmt-compute/ | 2023-01-12 |
| 2 | VirtualMachineImagesOperations Class - list | https://learn.microsoft.com/en-us/python/api/azure-mgmt-compute/azure.mgmt.compute.v2022_08_01.operations.virtualmachineimagesoperations?view=azure-python#azure-mgmt-compute-v2022-08-01-operations-virtualmachineimagesoperations-list | 2023-01-12 |
| 3 | azure-identity 1.12.0 | https://pypi.org/project/azure-identity/ | 2023-01-13 |
| 4 | Use the Azure libraries (SDK) for Python | https://learn.microsoft.com/en-us/azure/developer/python/sdk/azure-sdk-overview | 2023-01-12 |
| 5 | VirtualMachineImagesOperations Class - list_publishers | https://learn.microsoft.com/en-us/python/api/azure-mgmt-compute/azure.mgmt.compute.v2022_08_01.operations.virtualmachineimagesoperations?view=azure-python#azure-mgmt-compute-v2022-08-01-operations-virtualmachineimagesoperations-list-publishers | 2023-01-12 |
| 6 | VirtualMachineImagesOperations Class - list_offers | https://learn.microsoft.com/en-us/python/api/azure-mgmt-compute/azure.mgmt.compute.v2022_08_01.operations.virtualmachineimagesoperations?view=azure-python#azure-mgmt-compute-v2022-08-01-operations-virtualmachineimagesoperations-list-offers | 2023-01-12 |
| 7 | VirtualMachineImagesOperations Class - list_skus | https://learn.microsoft.com/en-us/python/api/azure-mgmt-compute/azure.mgmt.compute.v2022_08_01.operations.virtualmachineimagesoperations?view=azure-python#azure-mgmt-compute-v2022-08-01-operations-virtualmachineimagesoperations-list-skus | 2023-01-12 |
