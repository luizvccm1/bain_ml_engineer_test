#!/bin/bash
set -eu

echo "##### CREATE DEFINED LAMBDA LAYERS"
. codebuild/create_lambda_layers.sh

echo "##### PACKAGING LAMBDA SAM TEMPLATE"
sam --version
sam package --s3-bucket "$S3Bucket" -t "$LAMBDA_SAM_TEMPLATE_1" --output-template-file "$LAMBDA_SAM_TEMPLATE_1" --s3-prefix "deploy_packages"
sam package --s3-bucket "$S3Bucket" -t "$LAMBDA_SAM_TEMPLATE_2" --output-template-file "$LAMBDA_SAM_TEMPLATE_2" --s3-prefix "deploy_packages"

echo "##### LOAD CLOUDFORMATION CONFIGURATIONS JSON DYNAMIC VALUES FROM LOCAL ENVIRONMENT VARIABLES"
python codebuild/update_cloudformation_config_json.py

echo "##### LOAD CLOUDFORMATION CONFIGURATIONS JSON DYNAMIC VALUES FROM AWS SYSTEMS MANAGER PARAMETER STORE"
python codebuild/load_configuration_json_from_aws_parameter_store.py

echo "##### UPLOADING CHILD TEMPLATES TO S3"
bash codebuild/upload_child_templates_to_s3.sh

