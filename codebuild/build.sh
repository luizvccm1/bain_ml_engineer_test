#!/bin/bash
set -eu

echo "##### LOAD CLOUDFORMATION CONFIGURATIONS JSON DYNAMIC VALUES FROM LOCAL ENVIRONMENT VARIABLES"
python codebuild/update_cloudformation_config_json.py

echo "##### LOAD CLOUDFORMATION CONFIGURATIONS JSON DYNAMIC VALUES FROM AWS SYSTEMS MANAGER PARAMETER STORE"
python codebuild/load_configuration_json_from_aws_parameter_store.py

echo "##### UPLOADING CHILD TEMPLATES TO S3"
bash codebuild/upload_child_templates_to_s3.sh

