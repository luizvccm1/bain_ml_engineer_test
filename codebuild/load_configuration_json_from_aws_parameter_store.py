
import json
import boto3
import os

# Load dynamic application configuration from AWS Systems Manager Parameter Store
ssm_client = boto3.client('ssm')
response = ssm_client.get_parameter(Name=os.environ['AppConfigSsmParameterName'])
print(response['Parameter']['Value'])
dynamic_params = json.loads(response['Parameter']['Value'])

# Load static application configuration from JSON file
with open(os.environ['OUTPUT_CONF_JSON'], 'r') as f:
    cf_config = json.load(f)

# Join both application configuration data
cf_config['Parameters'].update(dynamic_params)

# Save final configuration file
with open(os.environ['OUTPUT_CONF_JSON'], 'w') as f:
    json.dump(cf_config, f)