import boto3
import subprocess
import sys
import filecmp
import os

build_image=False

#Adicionar: Checar se a imagem já foi construída antes

#Checar se houveram alterações nos arquivos de imagem
s3 = boto3.client('s3')
object_list= s3.list_objects_v2(Bucket=os.environ['S3Bucket'], Prefix='container_images/{Stage}/{folder_name}/'.format(folder_name=str(sys.argv[1]), Stage=os.environ['Stage']))

if 'Contents' in object_list:
    for object in object_list['Contents']:
        key_split= object['Key'].split('/')
        local_key="/".join(key_split[0:1] + key_split[2:])
        s3.download_file(os.environ['S3Bucket'], object['Key'], "temp.txt")
        if os.path.exists(local_key):
            if not filecmp.cmp("temp.txt", local_key, shallow=False):
                build_image=True
                break
        else:
            s3.delete_object(Bucket=os.environ['S3Bucket'], Key=object['Key'])
            print("Arquivo deletado")
else:
    build_image=True

if build_image:
    print("Build da imagem")
    #Atualizar arquivos da imagem no bucket
    for root, dirs, files in os.walk('container_images/{folder_name}/'.format(folder_name=str(sys.argv[1]))):
        for name in files:
            if os.path.isfile((os.path.join(root, name))):
                object= "/".join(os.path.join(root, name).split("/")[2:])
                path_local="container_images/{folder_name}/".format(folder_name=str(sys.argv[1]), stage= os.environ['Stage']) + str(object)
                path_s3="container_images/{stage}/{folder_name}/".format(folder_name=str(sys.argv[1]), stage= os.environ['Stage']) + str(object)
                s3.upload_file(path_local, os.environ['S3Bucket'], path_s3)
        for name in dirs:
            if os.path.isfile((os.path.join(root, name))):
                object= "/".join(os.path.join(root, name).split("/")[2:])
                path_local="container_images/{folder_name}/".format(folder_name=str(sys.argv[1]), stage= os.environ['Stage']) + str(object)
                path_s3="container_images/{stage}/{folder_name}/".format(folder_name=str(sys.argv[1]), stage= os.environ['Stage']) + str(object)
                s3.upload_file(path_local, os.environ['S3Bucket'], path_s3)

    account_id = boto3.client('sts').get_caller_identity().get('Account')
    region = boto3.Session().region_name
    ecr_repository = "sagemaker-" + str(sys.argv[1])
    tag = ':latest'
    processing_repository_uri = '{}.dkr.ecr.{}.amazonaws.com/{}'.format(account_id, region, ecr_repository + "-" + os.environ['Stage'] + tag)
    stage=os.environ['Stage']

    subprocess.check_call(["container_images/build_image.sh", ecr_repository, processing_repository_uri, account_id, region, tag, stage])
