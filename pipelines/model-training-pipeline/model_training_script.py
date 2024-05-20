import polars as pl

from category_encoders import TargetEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor

import os
import argparse
import joblib

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

    parser= argparse.ArgumentParser()

    #Loading hyperparameters
    parser.add_argument('--learning_rate', type=float, default=0.01)
    parser.add_argument('--n_estimators', type=int, default=300)
    parser.add_argument('--max_depth', type=int, default=5)
    parser.add_argument('--loss', type=str, default='absolute_error')

    #Loading Sagemaker specific arguments. Defaults are set in the environment variables
    parser.add_argument('--model-dir', type=str, default=os.environ['SM_MODEL_DIR'])
    parser.add_argument('--train', type=str, default=os.environ['SM_CHANNEL_TRAIN'])

    args= parser.parse_args()

    #Setting relevant paths
    input_path= args.train
    output_path= args.model_dir

    #Loading training data
    train_df= load_csv_data(f"{input_path}/train.csv")

    #Preparing df for training
    train_cols = [
        col for col in train_df.columns if col not in ['id', 'price']
    ]

    categorical_cols = ["type", "sector"]
    numerical_cols   = [col for col in train_cols if col not in categorical_cols]
    target           = "price"

    train_features_df= train_df[train_cols]
    train_target_df= train_df[target]

    #Creating hyperparameter dict
    hyperparams_dict= vars(args)
    hyperparams_dict.pop("train")
    hyperparams_dict.pop("model_dir")

    #Creating model pipeline
    categorical_transformer = TargetEncoder()

    preprocessor = ColumnTransformer(
        transformers=[
            ('categorical',
            categorical_transformer,
            categorical_cols),
            ('numerical',
            'passthrough',
            numerical_cols)
        ])

    steps = [
        ('preprocessor', preprocessor),
        ('model', GradientBoostingRegressor(**hyperparams_dict))
    ]

    pipeline = Pipeline(steps)

    #Training pipeline
    pipeline.fit(train_features_df.to_pandas(), train_target_df.to_pandas())

    #Saving pipeline
    joblib.dump(pipeline, f"{output_path}/property_value_estimator_pipeline.sav")

