#!/bin/sh

echo "Building images"

ecr_repository="$1"
processing_repository_uri="$2"
account_id="$3"
region="$4"
tag="$5"
stage="$6"

echo "Declared variables"

echo $ecr_repository
echo $processing_repository_uri
echo $account_id
echo $region
echo $tag
echo $stage

chmod +x container_images/"${ecr_repository:10}"/serve-files/serve
docker build --platform linux/amd64 -t "$ecr_repository-$stage" container_images/"${ecr_repository:10}"
aws ecr get-login-password --region "$region" | docker login --username AWS --password-stdin "$account_id".dkr.ecr."$region".amazonaws.com

output=$(aws ecr describe-repositories --repository-names "$ecr_repository-$stage" 2>&1)
if [ $? -ne 0 ]; then
  if echo ${output} | grep -q RepositoryNotFoundException; then
    aws ecr create-repository --repository-name "${ecr_repository}-${stage}"
  else
    >&2 echo ${output}
  fi
fi

docker tag "${ecr_repository}-${stage}${tag}" "$processing_repository_uri"
docker push "$processing_repository_uri"