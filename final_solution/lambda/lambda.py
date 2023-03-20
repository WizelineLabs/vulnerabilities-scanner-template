"""Set retention configuration for log groups with missing retention configuration"""
import os
import boto3

IS_DEPLOYMENT = os.environ["ENVIRONMENT"] in ["prd", "stg", "sandbox"]
region_name = os.environ.get("REGION", "us-east-1")

def get_logs_client():
    """Get AWS logs client either local or real"""
    if IS_DEPLOYMENT:
        return boto3.client("logs", region_name=region_name)
    else:
        return boto3.client(
            "logs",
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name=region_name,
            endpoint_url="http://localhost:4566",
        )


def lambda_handler(event,context):
    """Lambda handler or main"""

    retention_days = int(os.environ.get("RETENTION_DAYS", "545"))
    valid_retention_values = [
        1,
        3,
        5,
        7,
        14,
        30,
        60,
        90,
        120,  # 4 months
        150,  # 5 months
        180,  # 6 months
        365,  # 1 year
        400,  # 13.3 months
        545,  # 18.1 months
        731,  # 24.3 months (2 years)
        1827,  # 5 years
        3653,  # 10 years
    ]
    assert (
        retention_days in valid_retention_values
    ), f"invalid retention_days value {retention_days}, valid values are {valid_retention_values}"

    logs_client = get_logs_client()
    log_groups = all_log_groups(logs_client)

    log_groups_without_retention = get_log_groups_without_retention(
        log_groups=log_groups, retention_days=retention_days
    )

    update_log_groups_without_retention(logs_client, log_groups_without_retention)

    return {"response": "success"}


def update_log_groups_without_retention(logs_client, log_groups_tuples):
    """Update retention setting"""
    print(f"tuples: {log_groups_tuples}")
    for log_group_tuple in log_groups_tuples:
        update_log_group_retention_setting(
            logs_client,
            log_group_tuple[0],
            log_group_tuple[1],
        )


def get_log_groups_without_retention(log_groups, retention_days):
    """Update retention configuration for log groups with missing retention configuration"""
    print(f"Processing log groups in region {region_name} ...")

    log_groups_without_retention = []
    print(f"log_groups: {log_groups}")
    for log_group in log_groups:
        if "retentionInDays" not in log_group:
            log_groups_without_retention.append(
                tuple((log_group["logGroupName"], retention_days))
            )
    print(f"log_groups_without_retention: {log_groups_without_retention}")

    return log_groups_without_retention

def update_log_group_retention_setting(logs_client, log_group_name, retention_days):
    """Update log group retention configuration for a specific log group"""

    logs_client.put_retention_policy(
        logGroupName=log_group_name, retentionInDays=retention_days
    )
    print(
        f" - Updated retention setting for log group {log_group_name} to {retention_days} days."
    )


def all_log_groups(logs_client):
    """Get a list of the logs groups"""
    log_groups = []
    paginator = logs_client.get_paginator("describe_log_groups")
    for page in paginator.paginate():
        log_groups.extend(page["logGroups"])

    return log_groups


if __name__ == "__main__":
    lambda_handler(None, None)
