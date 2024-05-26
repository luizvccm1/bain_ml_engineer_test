import flask
import requests
import boto3
import os
import time
import json
import re
import logging
from decimal import Decimal
from api_key_handler import ApiKeyManager

def camel_case_to_snake_case(text):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', text).lower()

def snake_case_to_pascal_case(text):
    words = text.split('_')
    capitalized_words = [word.title() for word in words]
    result = ''.join(capitalized_words)
    return result

region_name = f"{os.environ['REGION']}"

table_name = f"inference-results-logging-table-{os.environ['STAGE']}"
serverless_endpoint_name = f"property-value-regressor-serverless-endpoint-{os.environ['STAGE']}"
training_pipeline_name= f"property-evaluator-training-{os.environ['STAGE']}"
secret_name= f"property-value-predictor-api-keys-{os.environ['STAGE']}"

dynamodb = boto3.resource('dynamodb', region_name=region_name)
table = dynamodb.Table(table_name)

secrets = boto3.client('secretsmanager', region_name=region_name)
sagemaker_runtime = boto3.client('sagemaker-runtime', region_name=region_name)
sagemaker = boto3.client('sagemaker', region_name=region_name)

key_manager= ApiKeyManager(secret_name, secrets)

logging.basicConfig(format='[%(levelname)s]: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Setup complete")

app = flask.Flask(__name__)
@app.route('/ping', methods=['GET'])
def ping():
    # Check if the classifier was loaded correctly
    logger.info("Executing /ping")
    try:
        #regressor
        status = 200
    except requests.exceptions.RequestException as e:
        status = 400
        logger.error(e.args)
    return flask.Response(response= json.dumps(' '), status=status, mimetype='application/json' )

@app.route('/start_training', methods=['GET', 'POST'])
def launch_sagemaker_pipeline():
    """
    Launches the pipeline responsible for training a new version of the model responsible for the property value prediction.

    Inputs:
    Json dict containing:
    TrainingDataS3Path (Optional): Path containing the S3 path of the training csv file to be used in the model training. String.
    ValidationDataS3Path (Optional): Path containing the S3 path of the validation csv file to be used in the model validation. String.

    Outputs:
    result: Result of the launching of the pipeline. SUCCESS or FAILURE.
    execution_arn: Only returned if pipeline is launched successfully. The ARN of the pipeline execution started. String.
    """
    logger.info("Executing /start_training")
    try:
        # Check API Key
        headers= flask.request.headers
        api_key= headers.get("API-key", "")

        logger.info("Checking API key")
        if not key_manager.validate_key_permission(api_key):
            response= {"Body": "Error: Unauthorized API Key"}
            logger.error("Unauthorized API Key")
            return flask.Response(response=json.dumps(response), status=403, mimetype='application/json')

        # Get input JSON data
        if flask.request.method == "POST":
            f = flask.request.get_json()
        else:
            f = {}

        # Set pipeline execution parameters
        input_allowed_keys=[
            "TrainingDataS3Path",
            "ValidationDataS3Path"
        ]

        logger.info("Preparing pipeline params")
        pipeline_hyperparameters=[]

        pipeline_hyperparameters.append({"Name": "TrainingTimestamp", "Value": str(time.time())[:-8]})
        pipeline_hyperparameters.append({"Name": "ValidationLambdaArn", "Value": f"arn:aws:lambda:us-east-1:527069186139:function:update-model-logs-and-endpoints-{os.environ['STAGE']}"})
        
        for key in f:
            if key in input_allowed_keys:
                pipeline_hyperparameters.append({"Name": key, "Value": f[key]})

        # Start pipeline execution
        logger.info("Starting pipeline execution")
        execution= sagemaker.start_pipeline_execution(PipelineName=training_pipeline_name, PipelineParameters=pipeline_hyperparameters)

        response= {
            "result": "SUCCESS",
            "execution_arn": execution['PipelineExecutionArn']
        }

        return flask.Response(response=json.dumps(response), status=200, mimetype='application/json')
    except requests.exceptions.RequestException as e:
        logger.error(e.args)
        response= {"result": "FAILURE", "error": e}
        return flask.Response(response=json.dumps(response), status=400, mimetype='application/json')
    except Exception as e:
        logger.error(e.args)
        response= {"result": "FAILURE", "error": e}
        return flask.Response(response=json.dumps(response), status=400, mimetype='application/json')

@app.route('/get_prediction', methods=['POST'])
def get_value():
    """
    Gets a predictions about a properties values based on data describing it.

    Inputs:
    Json dict containing:
    Type           : The property's type. String.
    Sector         : The property's sector. String.
    NetUsableArea  : The property's net usable area. Float.
    NetArea        : The property's net area. Float.
    NRooms         : The number of rooms of the property. Float.
    NBathroom      : The number of bathrooms of the property. Float.
    Latitude       : The property's latitude. Float.
    Longitude      : The property's longitude. Float.

    Outputs:
    Json dict containing:
    values: Prediction of the property value. Float.
    """
    logger.info("Executing /get_prediction")
    try:
        # Check API Key
        headers= flask.request.headers
        api_key= headers.get("API-key", "")

        if not key_manager.validate_key_permission(api_key):
            response= {"Body": "Error: Unauthorized API Key"}
            logger.error("Unauthorized API Key")
            return flask.Response(response=json.dumps(response), status=403, mimetype='application/json')

        # Get input JSON data
        f = flask.request.get_json()

        logger.info("Preparing input for predition")
        # Check for missing keys
        key_list= [
            "Type",
            "Sector",
            "NetUsableArea",
            "NetArea",
            "NRooms",
            "NBathroom",
            "Latitude",
            "Longitude"
        ]

        missing_key_list=[]
        for key in key_list:
            if key not in f:
                missing_key_list.append(key)

        extra_key_list=[]
        for key in f:
            if key not in key_list:
                extra_key_list.append(key)
        logger.warning(f"Unknown key(s) found: {', '.join(extra_key_list)}. Ignoring them for the prediction generation")

        if missing_key_list:
            error= {"error": f"Error 422 Unprocessable Entity:Request missing fields : [{', '.join(missing_key_list)}]"}
            return flask.Response(response=json.dumps(error), status=422, mimetype='application/json')

        # Convert dict keys to snake case
        snake_case_dict= {}
        for key, value in f.items():
            snake_case_dict[camel_case_to_snake_case(key)]= value
        
        # Stringify dict
        input_data_json= json.dumps(snake_case_dict)

        logger.info("Generating prediction")
        time_counter= time.time()
        # Make request to sagemaker endpoint
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=serverless_endpoint_name,
            ContentType='application/json',  # Specify the content type of the request
            Body=input_data_json
        )
        response_time= time.time()- time_counter

        # Parse the response
        result = json.loads(response['Body'].read().decode())

        # Update the dict with results
        snake_case_dict['predicted_price']= result['value']
        snake_case_dict['endpoint_response_time']= response_time
        snake_case_dict['timestamp']= str(time_counter)

        # Prepare dict for DynamoDB insertion
        for key, value in snake_case_dict.items():
            if type(value) == float:
                snake_case_dict[key]= Decimal(str(value))

        # Insert value on DynamoDB table
        response = table.put_item(Item=snake_case_dict)
        logger.info("Prediction saved to the DynamoDB logging table")

        return flask.Response(response=json.dumps(result), status=200, mimetype='application/json')
    except requests.exceptions.RequestException as e:
        logger.error(e.args)
        return flask.Response(response=json.dumps(''), status=400, mimetype='application/json')    
    except Exception as e:
        logger.error(e.args)
        response= {"error": e}
        return flask.Response(response=json.dumps(response), status=400, mimetype='application/json')
