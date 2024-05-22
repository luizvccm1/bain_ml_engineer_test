import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError

def read_json_from_s3(s3_path: str) -> dict:
    """
    Loads a JSON file from S3 into a variable

    Inputs:
    s3_path: S3 path containing the json file

    Outputs:
    json_content: Dict containing the json content
    """

    #Obtain s3 bucket name and file path
    split_path= s3_path.split("/")

    bucket_name = split_path[2]
    object_key = "/".join(split_path[3:])

    # Fetch the object from S3
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket_name, Key=object_key)

    # Read the object's content
    object_content = response['Body'].read().decode('utf-8')

    # Parse the JSON content
    json_content = json.loads(object_content)

    return json_content

def lambda_handler(event, context):
    
    print(event)

    #Construct DynamoDB dict from event
    dynamo_dict= {}

    datetime_timestamp= datetime.fromtimestamp(int(event['timestamp']))
    str_datetime_timestamp= datetime_timestamp.strftime("%Y-%m-%d %H:%M:%S")

    dynamo_dict['Timestamp']            = str_datetime_timestamp
    dynamo_dict['Modelname']            = event['model_name']
    dynamo_dict['TrainingJobName']      = event['training_job_name']
    dynamo_dict['TrainingDataS3Path']   = event['training_data_s3_path']
    dynamo_dict['ValidationDataS3Path'] = event['validation_data_s3_path']
    dynamo_dict['ModelArtifactsS3Path'] = event['model_artifacts_s3_path']

    try:
        metrics_json= read_json_from_s3(f"{event['model_metrics_s3_path']}/evaluation.json")
    except Exception as e:
        print(f"Error in the retrieval of evaluation metrics from S3: {e}")
        print("Metric values will be left indetermined")
        metrics_json={'metrics': {}}

    dynamo_dict['RMSE']          = metrics_json['metrics'].get('rmse', 'Indetermined')
    dynamo_dict['MAPE']          = metrics_json['metrics'].get('mape', 'Indetermined')
    dynamo_dict['MAE']           = metrics_json['metrics'].get('mae', 'Indetermined')
    dynamo_dict['ModelAccepted'] = bool(event['model_accepted'])

    if type(dynamo_dict['RMSE']) == float:
        dynamo_dict['RMSE']= Decimal(str(dynamo_dict['RMSE']))
    if type(dynamo_dict['MAPE']) == float:
        dynamo_dict['MAPE']= Decimal(str(dynamo_dict['MAPE']))
    if type(dynamo_dict['MAE']) == float:
        dynamo_dict['MAE']= Decimal(str(dynamo_dict['MAE']))

    #Saving Dict to DynamoDB
    dynamodb = boto3.resource('dynamodb')
    try:
        table_name = os.environ['PIPELINE_EXECUTION_LOGGING_TABLE']
        table = dynamodb.Table(table_name)

        response = table.put_item(Item=dynamo_dict)
    except Exception as e:
        print(f"Error on the update on the logging DynamoDB table {os.environ['PIPELINE_EXECUTION_LOGGING_TABLE']}: {e}")

    # Check if model was accepted, if yes update the serveless endpoint so it points to it
    if dynamo_dict['ModelAccepted']:
        sagemaker = boto3.client('sagemaker')

        #Checks if endpoint to be updated exists.
        endpoint_name = f'{os.environ["SERVERLESS_ENDPOINT_NAME"]}-{os.environ["STAGE"]}'

        existence_flag=False
        try:
            # Attempt to describe the endpoint
            endpoint_description = sagemaker.describe_endpoint(EndpointName=endpoint_name)
            existence_flag=True
            print("Endpoint already exists")

        except ClientError as e:
            # If the endpoint doesn't exist, handle the exception
            if e.response['Error']['Code'] == 'EndpointNotFound':
                existence_flag= False
                print("Endpoint does not exist")
            else:
                # Handle other exceptions if necessary
                print("An error occurred:", e)

        # Creates endpoint config using new model
        config_name= f'serverless-endpoint-default-config-{os.environ["STAGE"]}-{event["timestamp"]}'
        response = sagemaker.create_endpoint_config(
            EndpointConfigName=config_name,
            ProductionVariants=[
                {
                    "ModelName": event['model_name'],
                    "VariantName": "AllTraffic",
                    "ServerlessConfig": {
                        "MemorySizeInMB": 1024,
                        "MaxConcurrency": 10,
                        "ProvisionedConcurrency": 1,
                    }
                } 
            ]
        )

        #Updates model or creates new one
        if existence_flag:
            response = sagemaker.update_endpoint(
                EndpointName=os.environ["SERVERLESS_ENDPOINT_NAME"],
                EndpointConfigName=config_name
            )

        else:

            response = sagemaker.create_endpoint(
                EndpointName=os.environ["SERVERLESS_ENDPOINT_NAME"],
                EndpointConfigName=config_name
            )

         


