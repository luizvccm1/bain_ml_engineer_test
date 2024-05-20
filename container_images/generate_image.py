import boto3
import subprocess
import sys
import filecmp
import os
import botocore

s3 = boto3.client('s3')
ecr= boto3.client('ecr')

build_image=False
#Checar se existe imagem no repositório
print("Checando existência de imagem prévia no ECR")
repository_name= f"sagemaker-{str(sys.argv[1])}-{os.environ['Stage']}"
try:
    repositories= ecr.describe_repositories(repositoryNames=[repository_name])  
    if len(repositories['repositories']) > 1:
        rep_name= repository_name
    else:
        rep_name= repositories['repositories'][0]['repositoryName']

    response= ecr.list_images(
        repositoryName=rep_name
    )

    if len(response['imageIds']) == 0:
        print("Não encontradas imagens no repositório. Realizando o Build")
        build_image=True

except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] == 'RepositoryNotFoundException':
        print(f" Repositório {repository_name} não encontrado. Realizando o Build do mesmo")
        build_image=True
    else:
        print(f"Erro inexperado encontrado: {e}")
        print("Realizando o Build")
        build_image=True

else:
    print(f"Erro inexperado encontrado: {e}")
    print("Realizando o Build")
    build_image=True


#Checar se houveram alterações nos arquivos de imagem
try:
    object_list= s3.list_objects_v2(Bucket=os.environ['S3Bucket'], Prefix='container_images/{Stage}/{folder_name}/'.format(folder_name=str(sys.argv[1]), Stage=os.environ['Stage']))
except Exception as e:
    print("Erro na leitura do S3: {e}")
    print("Realizando o Build")
    object_list={}

if not object_list:
    build_image =True

if build_image == False:
    for object in object_list['Contents']:
        key_split= object['Key'].split('/')
        local_key="/".join(key_split[0:1] + key_split[2:])
        s3.download_file(os.environ['S3Bucket'], object['Key'], "temp.txt")
        if os.path.exists(local_key):
            print("Comparando arquivo local {local_key} com sua versão do S3")
            if not filecmp.cmp("temp.txt", local_key, shallow=False):
                build_image=True
                break
        else:
            s3.delete_object(Bucket=os.environ['S3Bucket'], Key=object['Key'])
            build_image=True
            print("Arquivo deletado")
    
    #To do: Implementar lógica que checa aruivos adicionais localmente

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
