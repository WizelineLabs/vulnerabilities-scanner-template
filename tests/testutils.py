import json
import os
from zipfile import ZipFile

import boto3
import botocore

LAMBDA_ZIP = "./lambda.zip"


def get_lambda_client():
    return boto3.client(
        "lambda",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1",
        endpoint_url="http://localstack:4566",
    )


def create_lambda_zip(function_name):
    os.chdir("lambda/")
    with ZipFile(LAMBDA_ZIP, "w") as z:
        z.write(function_name + ".py")


def create_lambda(function_name):
    lambda_client = get_lambda_client()
    create_lambda_zip(function_name)
    with open(LAMBDA_ZIP, "rb") as f:
        zipped_code = f.read()
    lambda_client.create_function(
        FunctionName=function_name,
        Runtime="python3.8",
        Role="role",
        Handler=function_name + ".lambda_handler",
        Code=dict(ZipFile=zipped_code),
        Environment={"Variables": {"ENVIRONMENT": "TESTING"}},
        Timeout=20,
    )


def delete_lambda(function_name):
    lambda_client = get_lambda_client()
    lambda_client.delete_function(FunctionName=function_name)
    os.remove(LAMBDA_ZIP)


def invoke_function(function_name):
    lambda_client = get_lambda_client()
    response = lambda_client.invoke(
        FunctionName=function_name, InvocationType="RequestResponse"
    )
    return json.loads(response["Payload"].read().decode("utf-8"))
