import os

from sagemaker.workflow.pipeline_context import PipelineSession

import sagemaker
import sagemaker.session

from sagemaker.workflow.parameters import (
        ParameterInteger,
        ParameterString,
)


from sagemaker.processing import ScriptProcessor, ProcessingInput, ProcessingOutput

from sagemaker.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.inputs import TrainingInput

from sagemaker.workflow.pipeline import Pipeline

from sagemaker.workflow.model_step import ModelStep
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.functions import JsonGet
from sagemaker.workflow.conditions import ConditionLessThanOrEqualTo
from sagemaker.model import Model

from sagemaker.workflow.lambda_step import LambdaStep
from sagemaker.lambda_helper import Lambda

from sagemaker.workflow.functions import Join

from sagemaker.sklearn.estimator import SKLearn

from sagemaker.workflow.properties import PropertyFile

import sys

import time

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

def get_pipeline(
   region="us-east-1",
   role=None,
   default_bucket=None,
   pipeline_name="property-evaluator-training",  # You can find your pipeline name in the Studio UI (project -> Pipelines -> name)
   image_name='',
   stage='test'
):

    sagemaker_session = sagemaker.session.Session()

    # Defining Pipeline Parameters

    processing_instance_count = ParameterInteger(
        name="ProcessingInstanceCount",
        default_value=1
    )
    training_instance_type_sklearn = ParameterString(
        name="TrainingInstanceTypeSKLearn",
        default_value="ml.m5.large"
    )
    processing_instance_type_model_eval = ParameterString(
        name="ProcessingInstanceTypeModelEval",
        default_value="ml.m5.large"
    )
    training_data_s3_path = ParameterString(
        name="TrainingDataS3Path",
        default_value= "s3://bain-ml-test-cicd-bucket-prd/data/training_data/train.csv"
    )
    validation_data_s3_path = ParameterString(
        name="ValidationDataS3Path",
        default_value= "s3://bain-ml-test-cicd-bucket-prd/data/validation_data/test.csv"
    )
    training_timestamp= ParameterString(
        name="TrainingTimestamp",
        default_value= "00000000"
    )
    validation_lambda_arn = ParameterString(
        name="ValidationLambdaArn",
        default_value= ""
    )

    output_folder_key= "model_pipeline/training_jobs/output"


    timestamp=Join(on="", values=[training_timestamp, ])


    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            print(os.path.join(root, file))

    #Defining pipeline processors

    training_processor_sklearn= SKLearn(
        entry_point= "model_training_script.py",
        framework_version= "1.2-1",
        instance_count= 1, 
        instance_type= training_instance_type_sklearn,
        volume_size=30,
        max_run= 60 * 60 * 24,
        output_path= "s3://{output_bucket}/{output_folder_path}/gbr".format(output_bucket=default_bucket, output_folder_path= output_folder_key),
        role=role,
        sagemaker_session= sagemaker_session,
        hyperparameters= {"learning_rate":0.01,
                          "n_estimators":300,
                          "max_depth":5,
                          "loss":"absolute_error"},
        source_dir = BASE_DIR
    )

    script_processor_model_eval = ScriptProcessor(command=['python3'],
        image_uri=f"527069186139.dkr.ecr.{region}.amazonaws.com/{image_name}:latest",
        role=role,
        instance_count=processing_instance_count,
        instance_type=processing_instance_type_model_eval,
        volume_size_in_gb= 5,
        max_runtime_in_seconds= 2 * 86400
    )

    #Step where the training of the SKLearn model pipeline occurs
    step_sklearn = TrainingStep(
        name="SKLearnPipelineTraining",
        estimator=training_processor_sklearn,
        inputs={
            "train": TrainingInput(
                s3_data=training_data_s3_path,
                content_type="text/csv",
            )
        }
    )

    evaluation_report = PropertyFile(
        name="EvaluationReport",
        output_name="model_metrics",
        path="evaluation.json"
    )

    #Step where the trains of the SKLearn model pipeline occurs
    step_model_eval = ProcessingStep(
        name="SKLearnPipelineEval",
        processor=script_processor_model_eval,
        inputs=[
            ProcessingInput(
                source=validation_data_s3_path,
                destination="/opt/ml/processing/validation_data"
            ),
            ProcessingInput(
                source=step_sklearn.properties.ModelArtifacts.S3ModelArtifacts,
                destination="/opt/ml/processing/model"
            ),
        ],
        outputs=[
            ProcessingOutput(
                output_name="model_metrics", 
                destination=f"s3://{default_bucket}/{output_folder_key}/eval_metrics", 
                source="/opt/ml/processing/metrics"
            ),
        ],
        code=os.path.join(BASE_DIR,"model_eval_script.py"),
        property_files=[evaluation_report],
        depends_on=[step_sklearn]
    )

    #Model to be created from the training step
    model_sklearn = Model(
        image_uri=f"527069186139.dkr.ecr.{region}.amazonaws.com/{image_name[:-4]}-prediction-{stage}:latest",
        model_data=step_sklearn.properties.ModelArtifacts.S3ModelArtifacts,
        sagemaker_session=PipelineSession(),
        role=role,
    )

    #Serverless endpoint config
    serverless_inference_config = {
        "MemorySizeInMB": 2048,  # Memory size for the serverless endpoint
        "MaxConcurrency": 10     # Maximum number of concurrent invocations
    }

    register_model_step_args = model_sklearn.create(
        instance_type=None,
        serverless_inference_config= serverless_inference_config
    )

    step_model_registration = ModelStep(
        name="ServerlessEndpointUpdate",
        step_args=register_model_step_args
    )

    step_update_pipeline_logs_accepted = LambdaStep(
        name="PipelineResultsLoggerAccepted",
        lambda_func=Lambda(function_arn=validation_lambda_arn),
        inputs={
            "timestamp": timestamp,
            "training_job_name": step_sklearn.properties.TrainingJobName,
            "training_data_s3_path": training_data_s3_path,
            "validation_data_s3_path": validation_data_s3_path,
            "model_name": step_model_registration.properties.ModelName,
            "model_metrics_s3_path": step_model_eval.properties.ProcessingOutputConfig.Outputs["model_metrics"].S3Output.S3Uri,
            "model_accepted": True
        },
        depends_on=[step_model_registration]
    )

    step_update_pipeline_logs_failed = LambdaStep(
        name="PipelineResultsLoggerRejected",
        lambda_func=Lambda(function_arn=validation_lambda_arn),
        inputs={
            "timestamp": timestamp,
            "training_job_name": step_sklearn.properties.TrainingJobName,
            "training_data_s3_path": training_data_s3_path,
            "validation_data_s3_path": validation_data_s3_path,
            "model_name": None,
            "model_metrics_s3_path": step_model_eval.properties.ProcessingOutputConfig.Outputs["model_metrics"].S3Output.S3Uri,
            "model_accepted": False
        }
    )

    #Step where we check if the obtained RMSE is above the minimum performance threshold
    step_condition = ConditionStep(
        name="CheckModelQuality",
        conditions=[
            ConditionLessThanOrEqualTo(
                left=JsonGet(
                    step_name=step_model_eval.name,
                    property_file=evaluation_report,
                    json_path="metrics.rmse"
                ),
                right=6000.0 
            )
        ],
        if_steps= [step_model_registration, step_update_pipeline_logs_accepted],
        else_steps= [step_update_pipeline_logs_failed],
        depends_on=[step_model_eval]
    )

    # Pipeline definition

    pipeline_name=pipeline_name + "-" +str(stage) 

    pipeline = Pipeline(
        name=pipeline_name,
        parameters=[
            processing_instance_count,
            training_instance_type_sklearn,
            processing_instance_type_model_eval,
            training_data_s3_path,
            validation_data_s3_path,
            training_timestamp
        ],
        steps=[step_sklearn,
               step_model_eval, 
               step_condition]
    )
    return pipeline