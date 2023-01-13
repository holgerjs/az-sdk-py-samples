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