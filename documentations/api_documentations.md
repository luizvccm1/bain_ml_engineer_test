# Introduction

This is the documentation for the API implemented inside the ECS cluster. It is responsible for accessing AWS Services to generate property value predictions using ML models and train new model versions to use in inference.

Some points regarding this API are:
- It is implemented through Docker and ran using the image built based on the files inside the repository path `container_images/model-deployment-api`.
- All payloads are expected to be in JSON format and the application type to be "application/json".
- Most methods need an API-key to be accessed, which must be present in the headers in the `API-key` field.

# Authentication

Some of the routes of this API need an API key to be accessed. These API keys are retrieved from inside the `property-value-predictor-api-keys-prd` secret inside AWS Secrets Manager. A key is automatically stored inside it when the secret is created, and to add more keys you have only to access the secret and add a new `key:value` pair, with the value being the new key.

The API also has a local cache where it stores keys so it does not have to access AWS Secrets Manager multiple times. These keys are updated whenever the API receives a key it cannot find in the cache or every 5 minutes since the secret was last accessed.

# Endpoint URL

To access the API, the requests must be made to an Application Load Balancer (ALB) that is used to control the traffic to the ECS Cluster, which listens to port 80. There are 2 ways to find out the DNS of the Load Balancer:

1. **Checking Elastic Container Services (ECS)**:
    1. Access the ECS Service using the search bar on the top of AWS.
    2. Select the `property-value-predictor-api-prd` cluster.
    3. Select the `property-value-predictor-api-prd` service.
    4. Select the "Configurations and networking" tab.
    5. Copy "DNS names" on the "Network configuration" tab.

2. **Check the Testing Lambda Function**:
    1. Access the Lambda service using the search bar on the top of AWS.
    2. Click the `test-api-lambda-prd` function.
    3. Click the "Configuration" tab.
    4. On the left column, select "Environment variables".
    5. The DNS name should be there under the key `DNS_NAME`.

# Methods

## /ping

- **Method types**: "GET"
- **API key**: UNNECESSARY
- **Description**: Method used to check if the API is online. If it is, it returns a code 200 response.
- **Output**: None

## /start_training

- **Method types**: "GET", "POST"
- **API key**: NECESSARY
- **Description**: Method used to launch the pipeline responsible for training a new version of the model used for the property price prediction.
- **Input**:
    ```json
    {
        "TrainingDataS3Path": "Path containing the S3 path of the training csv file to be used in the model training. The file's name must be train.csv. If value not informed, defaults to 's3://bain-ml-test-cicd-bucket-{Stage}/data/training_data/train.csv'. String.",
        "ValidationDataS3Path": "Path containing the S3 path of the validation csv file to be used in the model validation. The file's name must be test.csv. If value not informed, defaults to 's3://bain-ml-test-cicd-bucket-{Stage}/data/validation_data/test.csv'. String."
    }
    ```
- **Output**:
    ```json
    {
        "result": "Value indicating whether the model training pipeline was started successfully. Can be either SUCCESS or FAILURE. String.",
        "execution_arn": "Only returned if pipeline launch was successful. The ARN of the pipeline execution started. String.",
        "error": "Only returned if pipeline launch wasn't successful. Error message indicating why pipeline wasn't launched. String."
    }
    ```

## /get_prediction

- **Method types**: "POST"
- **API key**: NECESSARY
- **Description**: Method used to generate a prediction of the price of a property based on some of its characteristics.
- **Input**:
    ```json
    {
        "Type": "The property's type. String.",
        "Sector": "The property's sector. String.",
        "NetUsableArea": "The property's net usable area. Float.",
        "NetArea": "The property's net area. Float.",
        "NRooms": "The number of rooms of the property. Float.",
        "NBathroom": "The number of bathrooms of the property. Float.",
        "Latitude": "The property's latitude. Float.",
        "Longitude": "The property's longitude. Float."
    }
    ```
- **Output**:
    ```json
    {
        "values": "Prediction of the property value. Float.",
        "error": "Only returned if prediction wasn't successful. Error message indicating why the prediction was not generated. String."
    }
    ```
