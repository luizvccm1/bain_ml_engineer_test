import json
import os
import re

# Read CloudFormation configuration JSON template
with open(os.environ['OUTPUT_CONF_JSON'], 'r') as f:
    config_data = json.load(f)

# Load missing configuration values from environment variables
for key in config_data['Parameters']:
    if config_data['Parameters'][key] is None:
        config_data['Parameters'][key] = os.environ[key]

# Load configuration values for the lambda layers created
for key in os.environ:
    if re.search('^{prefix}.+$'.format(prefix=os.environ['LAMBDA_LAYER_ENV_VAR_PREFIX']), key):
        config_data['Parameters'][key] = os.environ[key]

for directory in os.scandir("./pipelines"):
    if directory.is_dir():
        config_data['Parameters']["{content_type}Pipeline".format(content_type=directory.path[12:].split('-')[0].capitalize())]= "{pipeline_name}-{content_type}-{stage}".format(pipeline_name=os.environ["SAGEMAKER_PIPELINE_NAME"], content_type=directory.path[12:].split('-')[0], stage=os.environ["Stage"]) 

for key in config_data['Parameters']:
    print("Chave:", key)

# Write updated CloudFormation configuration JSON file
with open(os.environ['OUTPUT_CONF_JSON'], 'w') as f:
    json.dump(config_data, f)
