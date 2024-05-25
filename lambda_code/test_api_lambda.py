import requests
import json
import os

def lambda_handler(event, context):

    # Define the API endpoint URL
    alb_url = f"http://{os.environ['DNS_NAME']}:80/{event['endpoint']}"
    
    #Define the request params
    headers = event['headers']
    method_type= event['method_type']
    payload= event['payload']
    

    try:
        # Make a POST request to the API endpoint with the payload
        if method_type.lower()== "get":
            response = requests.get(alb_url, headers=headers)
        elif method_type.lower()== "post":
            response = requests.post(alb_url, json=payload, headers=headers)
        else:
            print("Method type not recognised: Request aborted")
    
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Print the response content (assuming it's JSON)
            print(response.json())
        else:
            # Print an error message if the request was not successful
            print(f'Error: {response.status_code}')
    except Exception as e:
        print(e)