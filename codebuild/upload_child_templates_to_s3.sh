#!/bin/bash
set -eu

while IFS= read -r -d '' child_template
do
  echo "### Uploading template $child_template"
  aws s3 cp "$child_template" "s3://$S3Bucket/$CloudFormationTemplatesS3Prefix/"
done< <(find ./aws_cloudformation/child_templates -type f -regex ".*\.\(yaml\|yml\)$" -print0)
