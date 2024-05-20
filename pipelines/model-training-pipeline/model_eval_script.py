import polars as pl
import numpy as np

from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_percentage_error,
    mean_absolute_error)

import joblib
import json
import tarfile

def calculate_metrics(predictions: list, target: list) -> (float, float, float):
    """
    Calculates regression perfomance metrics based on values predicted and their targets and returns those values in a tuple

    Inputs: 
    predictions: list of predictions made by regression model
    target: targets for the predictions made by the regression model

    Outputs:
    rmse: Root Mean-Square Error of the predictions
    mape: Mean Absolute Percentage Error of the predictions
    mae: Mean Absolute Error of the predictions
    """

    rmse= np.sqrt(mean_squared_error(predictions, target))
    mape= mean_absolute_percentage_error(predictions, target)
    mae = mean_absolute_error(predictions, target)

    return rmse, mape, mae

def load_csv_data(csv_path: str) -> pl.DataFrame:
    """
    Load a csv file into a Polars Dataframe

    Inputs: 
    csv_path: local path to CSV file

    Outputs:
    output_df: Polars DataFrame object containg the CSV data
    """

    return pl.read_csv(csv_path)

if __name__=="__main__":

    #Setting relevant paths
    input_path_data="opt/ml/processing/validation_data"
    input_path_model="opt/ml/processing/model"

    output_path= "/opt/ml/processing/metrics"

    #Loading validation data 
    val_data_df = load_csv_data(f"{input_path_data}/test.csv")

    #Loading model
    file=tarfile.open(f"{input_path_model}/model.tar.gz")
    file.extractall(input_path_model)
    file.close()

    pipeline= joblib.load(f"{input_path_model}/property_value_estimator_pipeline.sav")

    #Performing Inference
    train_cols = [
        col for col in val_data_df.columns if col not in ['id', 'price']
    ]
    target= "price"

    test_predictions = pipeline.predict(val_data_df.to_pandas()[train_cols])
    test_target = val_data_df.to_pandas()[target].values

    #Calculating metrics
    rmse, mape, mae= calculate_metrics(test_predictions, test_target)

    #Saving results in json file
    output_dict={}
    output_dict['metrics']={}

    output_dict['metrics']['rmse']=rmse
    output_dict['metrics']['mape']=mape
    output_dict['metrics']['mae']=mae

    with open(f"{output_path}/evaluation.json", "w") as f:
        json.dump(output_dict, f)