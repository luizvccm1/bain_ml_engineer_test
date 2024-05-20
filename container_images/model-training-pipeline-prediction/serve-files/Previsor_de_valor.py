import pandas as pd
import numpy as np

from category_encoders import TargetEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor

from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_percentage_error,
    mean_absolute_error)

import joblib
import json

import flask
import requests

input_path="/opt/ml/model"
output_path="/opt/ml/processing/output"

model_sklearn= joblib.load()

app = flask.Flask(__name__)
@app.route('/ping', methods=['GET'])
def ping():
    # Check if the classifier was loaded correctly
    print("GET acionado")
    try:
        #regressor
        status = 200
    except requests.exceptions.RequestException as e:
        status = 400
        print(e.args)
    return flask.Response(response= json.dumps(' '), status=status, mimetype='application/json' )

@app.route('/invocations', methods=['POST'])
def transformation():
    try:
        print('Carregando CSV')
        # Get input CSV data and convert it to a DF
        f = flask.request.get_data()
        #store the file contents as a JSON
        input_list= json.loads(f)

        #generate input df
        input_df= pd.DataFrame()
        input_df.loc[input_list]

        #generate_prediction
        prediction= model_sklearn.predict(input_df)

        # Transform predictions to JSON
        result = {
            'value':  prediction,
            }
        
        resultjson = json.dumps(result)

        return flask.Response(response=resultjson, status=200, mimetype='application/json')
    except requests.exceptions.RequestException as e:
        print(e.args)
        return flask.Response(response=json.dumps(' '), status=400, mimetype='application/json')    
    