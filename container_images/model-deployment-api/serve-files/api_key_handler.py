import boto3
import json
import time

class ApiKeyManager():
    """
    Class responsible for handling the API key management

    Attributes:
    client: boto3.client('secret') used to interact with the AWS Secret Server
    secret_name: Name of the secret containing the api_keys of the application
    api_keys: Set of accepted api_keys
    last_update: Timestamp containing the time where the last update to the api keys ocurred
    refresh_time: Number of seconds that must pass before the client forces a refresh
    """

    def __init__(self, secret_name: str, boto_secret_client: boto3.client, refresh_time=300):

        self.client=  boto_secret_client
        self.secret_name= secret_name
        self.api_keys= set()
        self.last_update= None
        self.refresh_time= refresh_time

        self.update_keys()

    def get_secret(self):
        """
        Gets the values from the secret associated with the object

        Output:
        secret: Dict containing the secret extracted. Dict.
        """

        try: 
            get_secret_value_response= self.client.get_secret_value(
                SecretId= self.secret_name
            )
        except ClientError as e:
            raise e
        
        secret = get_secret_value_response['SecretString']

        return secret
    
    def update_keys(self):
        """
        Refreshes the set of accepted api keys
        """

        secret= json.loads(self.get_secret())

        secret_set= set()
        for value in secret.values():
            secret_set.update((value,))

        self.api_keys= secret_set
        self.last_update= time.time()
    
    def validate_key_permission(self, api_key):
        """
        Checks if an api key is valid or not. Returns True if yes and False otherwise
        """

        #Check if enough time has passed to force a refresh on the keys
        if time.time()- self.last_update > self.refresh_time:
            self.update_keys()

        #Check if key is in local keys
        if api_key in self.api_keys:
            return True
        
        #Check if key is not in local keys, update keys and try again
        self.update_keys()

        if api_key in self.api_keys:
            return True
        
        #If key still is not in, we assume its invalid
        return False