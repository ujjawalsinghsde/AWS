"""
AWS Lambda Operations using boto3
=================================

This module provides practical examples for common Lambda operations:
- Function lifecycle (create/update/delete)
- Invocation (sync/async)
- Configuration management (memory, timeout, env vars)
- Versions and aliases
- Concurrency controls
- Event source mappings (SQS/Kinesis/DynamoDB streams)
- Resource-based policies for invocation permissions

Prerequisites:
- pip install boto3
- AWS credentials configured
"""

import json
import time
import boto3
from botocore.exceptions import ClientError


# ==========================================================================
# CLIENT INITIALIZATION
# ==========================================================================

def get_lambda_client(region_name: str = "us-east-1"):
    """Return a Lambda client for a given region."""
    return boto3.client("lambda", region_name=region_name)


# ==========================================================================
# FUNCTION LIFECYCLE
# ==========================================================================

def create_function(
    function_name: str,
    role_arn: str,
    handler: str,
    zip_file_path: str,
    runtime: str = "python3.12",
    timeout: int = 15,
    memory_size: int = 256,
    environment: dict | None = None,
    region: str = "us-east-1",
) -> dict:
    """Create a Lambda function from a ZIP artifact."""
    client = get_lambda_client(region)

    with open(zip_file_path, "rb") as f:
        zip_bytes = f.read()

    params = {
        "FunctionName": function_name,
        "Runtime": runtime,
        "Role": role_arn,
        "Handler": handler,
        "Code": {"ZipFile": zip_bytes},
        "Timeout": timeout,
        "MemorySize": memory_size,
        "Publish": False,
    }

    if environment:
        params["Environment"] = {"Variables": environment}

    response = client.create_function(**params)
    print(f"Created function: {function_name}")
    return response


def delete_function(function_name: str, qualifier: str | None = None, region: str = "us-east-1") -> dict:
    """Delete a Lambda function or a specific version/alias-qualified function."""
    client = get_lambda_client(region)
    params = {"FunctionName": function_name}
    if qualifier:
        params["Qualifier"] = qualifier

    response = client.delete_function(**params)
    print(f"Deleted function: {function_name} (qualifier={qualifier})")
    return response


def get_function(function_name: str, qualifier: str | None = None, region: str = "us-east-1") -> dict:
    """Get function metadata and configuration."""
    client = get_lambda_client(region)
    params = {"FunctionName": function_name}
    if qualifier:
        params["Qualifier"] = qualifier

    return client.get_function(**params)


def list_functions(region: str = "us-east-1") -> list:
    """List Lambda functions in the region (handles pagination)."""
    client = get_lambda_client(region)
    paginator = client.get_paginator("list_functions")

    functions = []
    for page in paginator.paginate():
        functions.extend(page.get("Functions", []))

    for fn in functions:
        print(
            f"{fn['FunctionName']:40} runtime={fn.get('Runtime', 'n/a'):12} "
            f"memory={fn.get('MemorySize', 'n/a')}MB timeout={fn.get('Timeout', 'n/a')}s"
        )
    return functions


# ==========================================================================
# CODE & CONFIG UPDATES
# ==========================================================================

def update_function_code(
    function_name: str,
    zip_file_path: str,
    publish: bool = False,
    region: str = "us-east-1",
) -> dict:
    """Update Lambda function code with a new ZIP file."""
    client = get_lambda_client(region)

    with open(zip_file_path, "rb") as f:
        zip_bytes = f.read()

    response = client.update_function_code(
        FunctionName=function_name,
        ZipFile=zip_bytes,
        Publish=publish,
    )
    print(f"Updated code for: {function_name}")
    return response


def update_function_configuration(
    function_name: str,
    timeout: int | None = None,
    memory_size: int | None = None,
    environment: dict | None = None,
    ephemeral_storage_mb: int | None = None,
    region: str = "us-east-1",
) -> dict:
    """Update function timeout, memory, env vars, and ephemeral storage."""
    client = get_lambda_client(region)
    params = {"FunctionName": function_name}

    if timeout is not None:
        params["Timeout"] = timeout
    if memory_size is not None:
        params["MemorySize"] = memory_size
    if environment is not None:
        params["Environment"] = {"Variables": environment}
    if ephemeral_storage_mb is not None:
        params["EphemeralStorage"] = {"Size": ephemeral_storage_mb}

    response = client.update_function_configuration(**params)
    print(f"Updated configuration for: {function_name}")
    return response


def wait_until_function_updated(function_name: str, region: str = "us-east-1") -> None:
    """Wait until a function update reaches successful state."""
    client = get_lambda_client(region)
    waiter = client.get_waiter("function_updated")
    waiter.wait(FunctionName=function_name)
    print(f"Function update completed: {function_name}")


# ==========================================================================
# INVOCATION
# ==========================================================================

def invoke_sync(function_name: str, payload: dict, qualifier: str | None = None, region: str = "us-east-1") -> dict:
    """Invoke function synchronously and return parsed response payload."""
    client = get_lambda_client(region)
    params = {
        "FunctionName": function_name,
        "InvocationType": "RequestResponse",
        "Payload": json.dumps(payload).encode("utf-8"),
    }
    if qualifier:
        params["Qualifier"] = qualifier

    response = client.invoke(**params)
    response_payload = response["Payload"].read().decode("utf-8")

    print(f"StatusCode: {response.get('StatusCode')}")
    if "FunctionError" in response:
        print(f"FunctionError: {response['FunctionError']}")
    print(f"Response payload: {response_payload}")

    return {
        "StatusCode": response.get("StatusCode"),
        "ExecutedVersion": response.get("ExecutedVersion"),
        "FunctionError": response.get("FunctionError"),
        "Payload": response_payload,
    }


def invoke_async(function_name: str, payload: dict, qualifier: str | None = None, region: str = "us-east-1") -> dict:
    """Invoke function asynchronously (fire-and-forget from caller perspective)."""
    client = get_lambda_client(region)
    params = {
        "FunctionName": function_name,
        "InvocationType": "Event",
        "Payload": json.dumps(payload).encode("utf-8"),
    }
    if qualifier:
        params["Qualifier"] = qualifier

    response = client.invoke(**params)
    print(f"Async invoke accepted for: {function_name}, status={response.get('StatusCode')}")
    return response


# ==========================================================================
# VERSIONS & ALIASES
# ==========================================================================

def publish_version(function_name: str, description: str = "", region: str = "us-east-1") -> str:
    """Publish a new immutable function version from $LATEST."""
    client = get_lambda_client(region)
    response = client.publish_version(FunctionName=function_name, Description=description)
    version = response["Version"]
    print(f"Published version {version} for {function_name}")
    return version


def create_alias(
    function_name: str,
    alias_name: str,
    function_version: str,
    description: str = "",
    region: str = "us-east-1",
) -> dict:
    """Create an alias pointing to a function version."""
    client = get_lambda_client(region)
    response = client.create_alias(
        FunctionName=function_name,
        Name=alias_name,
        FunctionVersion=function_version,
        Description=description,
    )
    print(f"Created alias {alias_name} -> version {function_version}")
    return response


def update_alias_weighted_routing(
    function_name: str,
    alias_name: str,
    primary_version: str,
    canary_version: str,
    canary_weight: float,
    region: str = "us-east-1",
) -> dict:
    """
    Configure weighted traffic shifting.

    Example: canary_weight=0.1 routes 10% traffic to canary_version.
    """
    client = get_lambda_client(region)
    response = client.update_alias(
        FunctionName=function_name,
        Name=alias_name,
        FunctionVersion=primary_version,
        RoutingConfig={
            "AdditionalVersionWeights": {
                canary_version: canary_weight,
            }
        },
    )
    print(
        f"Updated alias {alias_name}: {primary_version}=main, "
        f"{canary_version}={canary_weight * 100:.1f}%"
    )
    return response


# ==========================================================================
# CONCURRENCY CONTROLS
# ==========================================================================

def put_reserved_concurrency(function_name: str, reserved: int, region: str = "us-east-1") -> dict:
    """Set reserved concurrency for a function."""
    client = get_lambda_client(region)
    response = client.put_function_concurrency(
        FunctionName=function_name,
        ReservedConcurrentExecutions=reserved,
    )
    print(f"Reserved concurrency set to {reserved} for {function_name}")
    return response


def delete_reserved_concurrency(function_name: str, region: str = "us-east-1") -> dict:
    """Remove reserved concurrency limit from a function."""
    client = get_lambda_client(region)
    response = client.delete_function_concurrency(FunctionName=function_name)
    print(f"Reserved concurrency removed for {function_name}")
    return response


def put_provisioned_concurrency(
    function_name: str,
    qualifier: str,
    provisioned: int,
    region: str = "us-east-1",
) -> dict:
    """Enable provisioned concurrency on a version or alias."""
    client = get_lambda_client(region)
    response = client.put_provisioned_concurrency_config(
        FunctionName=function_name,
        Qualifier=qualifier,
        ProvisionedConcurrentExecutions=provisioned,
    )
    print(f"Provisioned concurrency={provisioned} on {function_name}:{qualifier}")
    return response


# ==========================================================================
# EVENT SOURCE MAPPINGS
# ==========================================================================

def create_sqs_event_source_mapping(
    function_name: str,
    queue_arn: str,
    batch_size: int = 10,
    enabled: bool = True,
    region: str = "us-east-1",
) -> dict:
    """Create SQS event source mapping for Lambda."""
    client = get_lambda_client(region)
    response = client.create_event_source_mapping(
        EventSourceArn=queue_arn,
        FunctionName=function_name,
        Enabled=enabled,
        BatchSize=batch_size,
    )
    print(f"Created SQS event source mapping: UUID={response['UUID']}")
    return response


def create_stream_event_source_mapping(
    function_name: str,
    stream_arn: str,
    starting_position: str = "LATEST",
    batch_size: int = 100,
    enabled: bool = True,
    region: str = "us-east-1",
) -> dict:
    """Create event source mapping for Kinesis/DynamoDB streams."""
    client = get_lambda_client(region)
    response = client.create_event_source_mapping(
        EventSourceArn=stream_arn,
        FunctionName=function_name,
        StartingPosition=starting_position,
        BatchSize=batch_size,
        Enabled=enabled,
    )
    print(f"Created stream event source mapping: UUID={response['UUID']}")
    return response


def list_event_source_mappings(function_name: str, region: str = "us-east-1") -> list:
    """List event source mappings for a function."""
    client = get_lambda_client(region)
    response = client.list_event_source_mappings(FunctionName=function_name)
    mappings = response.get("EventSourceMappings", [])

    for m in mappings:
        print(
            f"UUID={m['UUID']} state={m.get('State')} "
            f"source={m.get('EventSourceArn')}"
        )
    return mappings


def update_event_source_mapping(
    uuid: str,
    enabled: bool | None = None,
    batch_size: int | None = None,
    region: str = "us-east-1",
) -> dict:
    """Update event source mapping state or batch size."""
    client = get_lambda_client(region)
    params = {"UUID": uuid}
    if enabled is not None:
        params["Enabled"] = enabled
    if batch_size is not None:
        params["BatchSize"] = batch_size

    response = client.update_event_source_mapping(**params)
    print(f"Updated event source mapping: {uuid}")
    return response


def delete_event_source_mapping(uuid: str, region: str = "us-east-1") -> dict:
    """Delete an event source mapping."""
    client = get_lambda_client(region)
    response = client.delete_event_source_mapping(UUID=uuid)
    print(f"Deleted event source mapping: {uuid}")
    return response


# ==========================================================================
# INVOCATION PERMISSIONS (RESOURCE-BASED POLICY)
# ==========================================================================

def add_invoke_permission(
    function_name: str,
    statement_id: str,
    principal: str,
    source_arn: str,
    action: str = "lambda:InvokeFunction",
    qualifier: str | None = None,
    region: str = "us-east-1",
) -> dict:
    """
    Grant a service principal permission to invoke the function.

    Example principals:
    - apigateway.amazonaws.com
    - events.amazonaws.com
    - s3.amazonaws.com
    """
    client = get_lambda_client(region)
    params = {
        "FunctionName": function_name,
        "StatementId": statement_id,
        "Action": action,
        "Principal": principal,
        "SourceArn": source_arn,
    }
    if qualifier:
        params["Qualifier"] = qualifier

    response = client.add_permission(**params)
    print(f"Added invoke permission: sid={statement_id}")
    return response


def remove_invoke_permission(
    function_name: str,
    statement_id: str,
    qualifier: str | None = None,
    region: str = "us-east-1",
) -> dict:
    """Remove a statement from Lambda resource policy."""
    client = get_lambda_client(region)
    params = {
        "FunctionName": function_name,
        "StatementId": statement_id,
    }
    if qualifier:
        params["Qualifier"] = qualifier

    response = client.remove_permission(**params)
    print(f"Removed invoke permission: sid={statement_id}")
    return response


def get_resource_policy(function_name: str, qualifier: str | None = None, region: str = "us-east-1") -> dict | None:
    """Get Lambda resource-based policy document."""
    client = get_lambda_client(region)
    params = {"FunctionName": function_name}
    if qualifier:
        params["Qualifier"] = qualifier

    try:
        response = client.get_policy(**params)
        policy = json.loads(response["Policy"])
        print(json.dumps(policy, indent=2))
        return policy
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print("No resource policy found.")
            return None
        raise


# ==========================================================================
# ASYNC INVOKE CONFIG (RETRIES / DESTINATIONS)
# ==========================================================================

def put_async_invoke_config(
    function_name: str,
    max_retry_attempts: int = 2,
    max_event_age_seconds: int = 3600,
    on_success_destination: str | None = None,
    on_failure_destination: str | None = None,
    qualifier: str | None = None,
    region: str = "us-east-1",
) -> dict:
    """Configure async invocation retries, event age, and destinations."""
    client = get_lambda_client(region)
    params = {
        "FunctionName": function_name,
        "MaximumRetryAttempts": max_retry_attempts,
        "MaximumEventAgeInSeconds": max_event_age_seconds,
    }
    if qualifier:
        params["Qualifier"] = qualifier

    destination_config = {}
    if on_success_destination:
        destination_config["OnSuccess"] = {"Destination": on_success_destination}
    if on_failure_destination:
        destination_config["OnFailure"] = {"Destination": on_failure_destination}
    if destination_config:
        params["DestinationConfig"] = destination_config

    response = client.put_function_event_invoke_config(**params)
    print(f"Updated async invoke config for {function_name}")
    return response


# ==========================================================================
# SIMPLE USAGE DEMO (SAFE, READ-ONLY OPS BY DEFAULT)
# ==========================================================================

if __name__ == "__main__":
    REGION = "us-east-1"

    # Read-only listing demo.
    print("Listing Lambda functions...")
    all_functions = list_functions(region=REGION)
    print(f"Total functions: {len(all_functions)}")

    # Example invoke (uncomment and configure to run):
    # invoke_sync(
    #     function_name="my-function",
    #     payload={"hello": "world"},
    #     qualifier="prod",
    #     region=REGION,
    # )
