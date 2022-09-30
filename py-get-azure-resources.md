## Use the Azure SDK for Python to retrieve Azure Resources

The Azure SDK for Python is one of many ways to connect to Azure REST API's and extract information. Here is how to retrieve all resources from an Azure subscription, put the data into a Pandas DataFrame and plot a simple pie chart.

### Import Libraries

We need to import the following libraries.

```python
# Import libraries
from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
import pandas as pd
import matplotlib
```

### Acquire Credentials and obtain the Management Object

```python
# Acquire credential
credential = AzureCliCredential()

# Define Scope
subscription_id = "subscription_id"

# Obtain the management object for resources.
resource_client = ResourceManagementClient(credential, subscription_id)
```

### Create and Populate a Dictionary

```python
resources = resource_client.resources.list()
dict = []
for resource in resources:
    dict.append(resource.as_dict())
```

### Create a DataFrame from the Dictionary

```python
df = pd.DataFrame.from_dict(dict)
```

### Select only the Top 10 rows based on the Resource Type Count

```python
type_df = df['type'].value_counts()
type_df_top = type_df.head(10)
```

### Finally plot the Pie Chart

```python
plot = type_df_top.plot.pie(figsize=(10, 10), autopct= lambda x: '{:.0f}'.format(x*type_df_top.sum()/100))
```

... which might look like something along these lines.
![Pie Chart](images/pie-chart.png)
