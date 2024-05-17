#!/bin/bash
set -eu

# Function to create a new python package based on a requirements file
function create_lambda_layer_package {
  # Get Lambda Layer name and version from requirement file name
  req_file=$(basename "$1")
  read -r layer_name layer_ver <<<"$(echo "$req_file" | sed 's/^\(.\+\)-\(\([0-9]\+\)\(\.[0-9]\+\)*\)\.txt$/\1 \2/')"

  # Convert layer_name to Pascal Case
  read -r layer_name_pascal <<<"$(echo "$layer_name" | sed -r 's/(^|_|\s|-)(([_ -]|\s)+)/\1/g' | sed -r 's/.*/\L&/g' | sed -r 's/(^|_|\s|-)([a-z])/\U\2/g')"

  # IMPORTANT:  To create a new lambda layer version, you shall modify the layer requirement .txt file with the new
  #             requirements specifications and also update its file name in ´lambda_layers/´ folder.
  pkg_file_name="$layer_name-$layer_ver.zip"
  pkg_s3_key="$LAMBDA_LAYER_PACKAGE_S3_PREFIX$pkg_file_name"

  # Create proper environment variable to use in configuration.json
  var="$LAMBDA_LAYER_ENV_VAR_PREFIX$layer_name_pascal"
  export "$var"="$pkg_s3_key"

  # Check if lambda layer package file already exists
  totalFoundObjects="0"
  totalFoundObjects=$(aws s3 ls "s3://$S3Bucket/$pkg_s3_key" --recursive --summarize |
    grep "Total Objects: " |
    sed 's/[^0-9]*//g')

  # Create lambda layer package if it doesn't exist
  if [ "$totalFoundObjects" -eq "0" ]; then
    echo "##### Building project lambda layer package $pkg_file_name"
    python3 -m pip install -t "./lambda_layer_$layer_name/python" -r "$LAMBDA_LAYER_REQUIREMENTS_PATH/$req_file"

    echo "##### Compressing lambda layer package $pkg_file_name"
    cd "lambda_layer_$layer_name/"
    zip -r -9 "$pkg_file_name" ./python

    echo "Uploading lambda layer package $pkg_file_name to S3"
    aws s3 cp "./$pkg_file_name" "s3://$S3Bucket/$pkg_s3_key"

    echo "Deleting $layer_name layer package temp files"
    cd ..
    rm -r "lambda_layer_$layer_name/"
  else
    echo "Package file ´$pkg_file_name´ already found in ´$pkg_s3_key´. Skipping $layer_name layer creation"
  fi
}

# Iterate over all requirement files in ./lambda_layers path
while IFS= read -r -d '' req_path
do
  echo "##### Building project lambda layer package from $req_path"
  create_lambda_layer_package "$req_path"
done < <(find "$LAMBDA_LAYER_REQUIREMENTS_PATH" -type f -regex "^.+-[0-9]+\(\.[0-9]+\)*\.txt$" -print0)