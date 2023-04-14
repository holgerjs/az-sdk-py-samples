## Transport Sharing | Azure SDK for Python

The code below is based on the blog post ['Transport sharing in the Azure SDK for Python'](https://devblogs.microsoft.com/azure-sdk/transport-sharing-in-azure-sdk-for-python/), which was published on [Microsoft Developer Blogs](https://devblogs.microsoft.com/).

Further details were gathered from the code samples in the [azure-sdk-for-python](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/core/azure-core/samples) GitHub repository.

The blog post states:
> Sharing a transport refers to creating a single instance of a transport object, such as an HttpTransport, and using it across multiple clients or requests. When you create a new transport object for each client or request, it can lead to increased resource usage and reduced performance.
> 
> -- [Understanding Transport Sharing](https://devblogs.microsoft.com/azure-sdk/transport-sharing-in-azure-sdk-for-python/#understanding-transport-sharing)

The idea of transport sharing is to re-use existing HTTPTransport objects in order to keep the amount of concurrent connections to an Azure resource at a low level. For example, when performing activities on a particular storage account, the connection to this storage account could be shared.

Below are the steps I performed to test this. I will read containers from a storage account using individual HTTPTransport objects first and then use transport sharing to see the difference between both approaches.

1. Import the corresponding libraries.

   ```python
   from azure.storage.blob import BlobServiceClient
   from azure.identity import AzureCliCredential
   from azure.core.pipeline.transport import RequestsTransport
   ```

2. Import constant variables. This is just so that I don't use the name of the storage account in the main code. One could also read the value from an environment variable or put it into the code directly. The content of the `Constants.py` file simply looks like this:

   ```python
   STORAGE_ACCOUNT_BLOB_ENDPOINT = 'https://{my_storage_account_name}.blob.core.windows.net/'
   ```

   The import is then done as usual.

   ```python
   import Constants as CONST
   ```

3. Retrieve credentials from the Azure CLI. This is just for testing purposes and should not be used in a production environment.

   ```python
   credential = AzureCliCredential()
   ```


4. Individual transports. Below code can be used to create two clients for the same storage accounts and then list the corresponding containers using both clients individually.

   ```python
   blob_client1 = BlobServiceClient(
       account_url = CONST.STORAGE_ACCOUNT_BLOB_ENDPOINT,
       credential = credential
   )

   blob_client2 = BlobServiceClient(
       account_url = CONST.STORAGE_ACCOUNT_BLOB_ENDPOINT,
       credential = credential
   )

   containers_list1 = blob_client1.list_containers()
   containers_list2 = blob_client2.list_containers()

   for container in containers_list1:
       print(container)

   for container in containers_list2:
       print(container)
   ```

   Depending on the amount of containers in the storage account, the output would be along these lines:

   ```bash
   {'name': 'con1', 'last_modified': datetime.datetime(2022, 10, 28, 14, 45, 11, tzinfo=datetime.timezone.utc), 'etag': '"0x1DAF35011161C06"', 'lease': {'status': 'unlocked', 'state': 'available', 'duration': None}, 'public_access': None, 'has_immutability_policy': False, 'deleted': None, 'version': None, 'has_legal_hold': False, 'metadata': None, 'encryption_scope': <azure.storage.blob._models.ContainerEncryptionScope object at 0x7f9bb10632e0>, 'immutable_storage_with_versioning_enabled': False}
   {'name': 'con1', 'last_modified': datetime.datetime(2022, 10, 28, 14, 45, 11, tzinfo=datetime.timezone.utc), 'etag': '"0x1DAF35011161C06"', 'lease': {'status': 'unlocked', 'state': 'available', 'duration': None}, 'public_access': None, 'has_immutability_policy': False, 'deleted': None, 'version': None, 'has_legal_hold': False, 'metadata': None, 'encryption_scope': <azure.storage.blob._models.ContainerEncryptionScope object at 0x7f9bb0fa9430>, 'immutable_storage_with_versioning_enabled': False}
   ```

   When running `netstat` now, we can see that two TCP connections were established against the storage account in question. One for each blob client. (For figuring out which IP address the storage account has, one can use `nslookup`, i.E. : `nslookup {my_storage_account_name}.blob.core.windows.net`)

   ```
   $ netstat -tnov | grep 20.41.119.17
   tcp        0      0 10.0.0.6:50434          20.41.119.17:443        ESTABLISHED off (0.00/0/0)
   tcp        0      0 10.0.0.6:50450          20.41.119.17:443        ESTABLISHED off (0.00/0/0)
   ```

   Afterwards, the connections need to be closed again.

   ```python
   blob_client1.close()
   blob_client2.close()
   ```
   
5. Shared Transport. 
   
   Then, I tried the same using a shared HTTPTransport object. Note that the additional `transport` and `session_owner` parameters are passed into `BlobServiceClient` now.
   
   ```python
   shared_transport = RequestsTransport()

   blob_svc_client1 = BlobServiceClient(
       account_url = CONST.STORAGE_ACCOUNT_BLOB_ENDPOINT,
       credential = credential,
       transport = shared_transport, 
       session_owner = False
   )

   blob_svc_client2 = BlobServiceClient(
       account_url = CONST.STORAGE_ACCOUNT_BLOB_ENDPOINT,
       credential = credential,
       transport = shared_transport, 
       session_owner = False
   )

   containers_list_from_shared_transport1 = blob_svc_client1.list_containers()
   containers_list_from_shared_transport2 = blob_svc_client2.list_containers()

   for cont in containers_list_from_shared_transport1:
       print(container)

   for cont in containers_list_from_shared_transport2:
       print(container)
   ```

   The console output should be similar to the one before, i.E.:

   ```bash
   {'name': 'con1', 'last_modified': datetime.datetime(2022, 10, 28, 14, 45, 11, tzinfo=datetime.timezone.utc), 'etag': '"0x1DAF35011161C06"', 'lease': {'status': 'unlocked', 'state': 'available', 'duration': None}, 'public_access': None, 'has_immutability_policy': False, 'deleted': None, 'version': None, 'has_legal_hold': False, 'metadata': None, 'encryption_scope': <azure.storage.blob._models.ContainerEncryptionScope object at 0x7f9bb10632e0>, 'immutable_storage_with_versioning_enabled': False}
   {'name': 'con1', 'last_modified': datetime.datetime(2022, 10, 28, 14, 45, 11, tzinfo=datetime.timezone.utc), 'etag': '"0x1DAF35011161C06"', 'lease': {'status': 'unlocked', 'state': 'available', 'duration': None}, 'public_access': None, 'has_immutability_policy': False, 'deleted': None, 'version': None, 'has_legal_hold': False, 'metadata': None, 'encryption_scope': <azure.storage.blob._models.ContainerEncryptionScope object at 0x7f9bb0fa9430>, 'immutable_storage_with_versioning_enabled': False}
   ```

   However, using `netstat` again, we can now see that only one TCP connection was opened this time, so the connection was shared with both blob service clients.

   ```
   $ netstat -tnov | grep 20.41.119.17
   tcp        0      0 10.0.0.6:44812          20.41.119.17:443        ESTABLISHED off (0.00/0/0)
   ```

   As with the previous example, we would finally need to close the connection (this is not required when using the `with` statment like in the samples in the Azure SDK repository).

   ```python
   shared_transport.close()
   ```
   