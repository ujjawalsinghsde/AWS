"""
AWS Step Functions Operations using boto3
==========================================

This module provides practical examples for common Step Functions operations:
- State machine lifecycle (create/update/delete)
- Execution management (start/stop/describe)
- Execution history and debugging
- Task token operations (callbacks)
- Monitoring and error handling

Prerequisites:
- pip install boto3
- AWS credentials configured
"""

import json
import time
import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any, List


# ==========================================================================
# CLIENT INITIALIZATION
# ==========================================================================

def get_stepfunctions_client(region_name: str = "us-east-1"):
    """Return a Step Functions client for a given region."""
    return boto3.client("stepfunctions", region_name=region_name)


def get_iam_client(region_name: str = "us-east-1"):
    """Return an IAM client (for creating roles)."""
    return boto3.client("iam")


# ==========================================================================
# STATE MACHINE LIFECYCLE
# ==========================================================================

def create_state_machine(
    name: str,
    definition: dict,
    role_arn: str,
    state_machine_type: str = "STANDARD",
    region: str = "us-east-1",
) -> Dict[str, Any]:
    """
    Create a new state machine.

    Args:
        name: State machine name (must be unique in account/region)
        definition: State machine definition as dict (ASL JSON)
        role_arn: IAM role ARN for Step Functions to assume
        state_machine_type: "STANDARD" or "EXPRESS"
        region: AWS region

    Returns:
        Response with state machine ARN
    """
    client = get_stepfunctions_client(region)

    # Convert definition dict to JSON string
    definition_str = json.dumps(definition)

    try:
        response = client.create_state_machine(
            name=name,
            definition=definition_str,
            roleArn=role_arn,
            type=state_machine_type,
        )
        print(f"Created state machine: {name}")
        print(f"ARN: {response['stateMachineArn']}")
        return response
    except ClientError as e:
        print(f"Error creating state machine: {e}")
        raise


def update_state_machine(
    state_machine_arn: str,
    definition: Optional[dict] = None,
    role_arn: Optional[str] = None,
    region: str = "us-east-1",
) -> Dict[str, Any]:
    """
    Update an existing state machine definition or IAM role.

    Args:
        state_machine_arn: ARN of state machine to update
        definition: New ASL definition (optional)
        role_arn: New IAM role ARN (optional)
        region: AWS region

    Returns:
        Response confirming update
    """
    client = get_stepfunctions_client(region)

    params = {"stateMachineArn": state_machine_arn}

    if definition:
        params["definition"] = json.dumps(definition)

    if role_arn:
        params["roleArn"] = role_arn

    try:
        response = client.update_state_machine(**params)
        print(f"Updated state machine: {state_machine_arn}")
        return response
    except ClientError as e:
        print(f"Error updating state machine: {e}")
        raise


def describe_state_machine(
    state_machine_arn: str,
    region: str = "us-east-1",
) -> Dict[str, Any]:
    """
    Get details about a state machine.

    Args:
        state_machine_arn: ARN of state machine
        region: AWS region

    Returns:
        State machine details (name, definition, role, creation date, etc.)
    """
    client = get_stepfunctions_client(region)

    try:
        response = client.describe_state_machine(stateMachineArn=state_machine_arn)

        print(f"Name: {response['name']}")
        print(f"Type: {response['type']}")
        print(f"Status: {response['status']}")
        print(f"Created: {response['creationDate']}")
        print(f"Definition:\n{response['definition']}")

        return response
    except ClientError as e:
        print(f"Error describing state machine: {e}")
        raise


def list_state_machines(
    region: str = "us-east-1",
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """
    List all state machines in a region.

    Args:
        region: AWS region
        max_results: Max results per request (1-100)

    Returns:
        List of state machine details
    """
    client = get_stepfunctions_client(region)

    try:
        response = client.list_state_machines(maxResults=max_results)

        machines = response.get("stateMachines", [])
        print(f"Found {len(machines)} state machines:")

        for machine in machines:
            print(f"  - {machine['name']} ({machine['stateMachineArn']})")
            print(f"    Type: {machine['type']}, Created: {machine['creationDate']}")

        return machines
    except ClientError as e:
        print(f"Error listing state machines: {e}")
        raise


def delete_state_machine(
    state_machine_arn: str,
    region: str = "us-east-1",
) -> Dict[str, Any]:
    """
    Delete a state machine.

    Args:
        state_machine_arn: ARN of state machine to delete
        region: AWS region

    Returns:
        Response confirming deletion
    """
    client = get_stepfunctions_client(region)

    try:
        response = client.delete_state_machine(stateMachineArn=state_machine_arn)
        print(f"Deleted state machine: {state_machine_arn}")
        return response
    except ClientError as e:
        print(f"Error deleting state machine: {e}")
        raise


# ==========================================================================
# EXECUTION MANAGEMENT
# ==========================================================================

def start_execution(
    state_machine_arn: str,
    input_data: Optional[dict] = None,
    execution_name: Optional[str] = None,
    region: str = "us-east-1",
) -> Dict[str, Any]:
    """
    Start a new execution of a state machine.

    Args:
        state_machine_arn: ARN of state machine
        input_data: Input JSON for execution (dict or None)
        execution_name: Optional unique execution name
        region: AWS region

    Returns:
        Response with execution ARN and start date
    """
    client = get_stepfunctions_client(region)

    params = {"stateMachineArn": state_machine_arn}

    if input_data:
        params["input"] = json.dumps(input_data)

    if execution_name:
        params["name"] = execution_name

    try:
        response = client.start_execution(**params)

        print(f"Started execution: {response['executionArn']}")
        print(f"Start time: {response['startTime']}")

        return response
    except ClientError as e:
        print(f"Error starting execution: {e}")
        raise


def describe_execution(
    execution_arn: str,
    region: str = "us-east-1",
) -> Dict[str, Any]:
    """
    Get details about an execution.

    Args:
        execution_arn: ARN of execution
        region: AWS region

    Returns:
        Execution details (status, input, output, start/stop time, etc.)
    """
    client = get_stepfunctions_client(region)

    try:
        response = client.describe_execution(executionArn=execution_arn)

        print(f"Execution: {response['name']}")
        print(f"Status: {response['status']}")
        print(f"Start time: {response['startDate']}")

        if "stopDate" in response:
            print(f"Stop time: {response['stopDate']}")

        if "output" in response:
            print(f"Output: {response['output']}")

        if "cause" in response:
            print(f"Cause: {response['cause']}")

        return response
    except ClientError as e:
        print(f"Error describing execution: {e}")
        raise


def list_executions(
    state_machine_arn: str,
    status_filter: Optional[str] = None,
    region: str = "us-east-1",
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """
    List executions for a state machine.

    Args:
        state_machine_arn: ARN of state machine
        status_filter: Filter by status (RUNNING, SUCCEEDED, FAILED, TIMED_OUT, ABORTED)
        region: AWS region
        max_results: Max results per request

    Returns:
        List of execution summaries
    """
    client = get_stepfunctions_client(region)

    params = {
        "stateMachineArn": state_machine_arn,
        "maxResults": max_results,
    }

    if status_filter:
        params["statusFilter"] = status_filter

    try:
        response = client.list_executions(**params)

        executions = response.get("executions", [])
        print(f"Found {len(executions)} executions:")

        for exec in executions:
            print(f"  - {exec['name']} | Status: {exec['status']} | Started: {exec['startDate']}")

        return executions
    except ClientError as e:
        print(f"Error listing executions: {e}")
        raise


def stop_execution(
    execution_arn: str,
    region: str = "us-east-1",
) -> Dict[str, Any]:
    """
    Stop a running execution.

    Args:
        execution_arn: ARN of execution to stop
        region: AWS region

    Returns:
        Response confirming stop time
    """
    client = get_stepfunctions_client(region)

    try:
        response = client.stop_execution(executionArn=execution_arn)
        print(f"Stopped execution: {execution_arn}")
        print(f"Stop time: {response['stopDate']}")
        return response
    except ClientError as e:
        print(f"Error stopping execution: {e}")
        raise


# ==========================================================================
# EXECUTION HISTORY & DEBUGGING
# ==========================================================================

def get_execution_history(
    execution_arn: str,
    region: str = "us-east-1",
    max_results: int = 25,
) -> List[Dict[str, Any]]:
    """
    Get full execution history (all state transitions).

    Args:
        execution_arn: ARN of execution
        region: AWS region
        max_results: Max events per request (1-100)

    Returns:
        List of execution history events
    """
    client = get_stepfunctions_client(region)

    try:
        # Collect all events via pagination
        events = []
        paginator = client.get_paginator("get_execution_history")

        pages = paginator.paginate(
            executionArn=execution_arn,
            PaginationConfig={"PageSize": max_results},
        )

        for page in pages:
            events.extend(page.get("events", []))

        print(f"\nExecution history ({len(events)} events):")
        print("-" * 80)

        for event in events:
            timestamp = event.get("timestamp", "")
            event_type = event.get("type", "")

            print(f"\n[{timestamp}] {event_type}")

            # Print relevant details based on event type
            if "stateEnteredEventDetails" in event:
                details = event["stateEnteredEventDetails"]
                print(f"  State: {details.get('name')}")
                print(f"  Type: {details.get('type')}")
                if "input" in details:
                    print(f"  Input: {details['input'][:100]}...")

            elif "stateExitedEventDetails" in event:
                details = event["stateExitedEventDetails"]
                print(f"  State: {details.get('name')}")
                if "output" in details:
                    print(f"  Output: {details['output'][:100]}...")

            elif "executionFailedEventDetails" in event:
                details = event["executionFailedEventDetails"]
                print(f"  Error: {details.get('error')}")
                print(f"  Cause: {details.get('cause')}")

            elif "taskFailedEventDetails" in event:
                details = event["taskFailedEventDetails"]
                print(f"  Error: {details.get('error')}")
                print(f"  Cause: {details.get('cause')}")

        return events
    except ClientError as e:
        print(f"Error getting execution history: {e}")
        raise


def analyze_execution_failure(
    execution_arn: str,
    region: str = "us-east-1",
) -> Dict[str, Any]:
    """
    Analyze a failed execution to identify the error.

    Args:
        execution_arn: ARN of execution
        region: AWS region

    Returns:
        Analysis with error details and failed state
    """
    client = get_stepfunctions_client(region)

    try:
        # Get execution status
        execution = client.describe_execution(executionArn=execution_arn)

        if execution["status"] != "FAILED":
            print(f"Execution is {execution['status']}, not FAILED")
            return execution

        # Get history to find failure point
        history_response = client.get_execution_history(executionArn=execution_arn)
        events = history_response.get("events", [])

        # Find failure event
        failure_info = None
        for event in reversed(events):  # Start from end
            if "failedEventDetails" in str(event):
                if "executionFailedEventDetails" in event:
                    failure_info = event["executionFailedEventDetails"]
                elif "taskFailedEventDetails" in event:
                    failure_info = event["taskFailedEventDetails"]
                break

        analysis = {
            "execution_arn": execution_arn,
            "status": execution["status"],
            "error": failure_info.get("error") if failure_info else "Unknown",
            "cause": failure_info.get("cause") if failure_info else "Unknown",
            "stop_date": execution.get("stopDate"),
            "cause_path": failure_info.get("causePath") if failure_info else None,
        }

        print("\nExecution Failure Analysis:")
        print(f"  Status: {analysis['status']}")
        print(f"  Error: {analysis['error']}")
        print(f"  Cause: {analysis['cause']}")

        return analysis
    except ClientError as e:
        print(f"Error analyzing execution: {e}")
        raise


# ==========================================================================
# TASK TOKEN & CALLBACK OPERATIONS
# ==========================================================================

def send_task_success(
    task_token: str,
    output_data: Optional[dict] = None,
    region: str = "us-east-1",
) -> Dict[str, Any]:
    """
    Send task success callback (for waitForTaskToken states).

    This is called from Lambda or external code when async work completes.

    Args:
        task_token: Task token from step machine (passed to Lambda)
        output_data: Output data to pass to next state
        region: AWS region

    Returns:
        Response confirming success
    """
    client = get_stepfunctions_client(region)

    params = {"taskToken": task_token}

    if output_data:
        params["output"] = json.dumps(output_data)

    try:
        response = client.send_task_success(**params)
        print(f"Task succeeded via callback")
        return response
    except ClientError as e:
        print(f"Error sending task success: {e}")
        raise


def send_task_failure(
    task_token: str,
    error: str = "TaskFailed",
    cause: str = "Task failed without details",
    region: str = "us-east-1",
) -> Dict[str, Any]:
    """
    Send task failure callback (for waitForTaskToken states).

    This is called when async work fails.

    Args:
        task_token: Task token from state machine
        error: Error code
        cause: Human-readable failure reason
        region: AWS region

    Returns:
        Response confirming failure notification
    """
    client = get_stepfunctions_client(region)

    try:
        response = client.send_task_failure(
            taskToken=task_token,
            error=error,
            cause=cause,
        )
        print(f"Task failed via callback: {error} - {cause}")
        return response
    except ClientError as e:
        print(f"Error sending task failure: {e}")
        raise


def send_task_heartbeat(
    task_token: str,
    region: str = "us-east-1",
) -> Dict[str, Any]:
    """
    Send heartbeat for long-running tasks (keeps token alive).

    Use this to extend timeout for tasks taking longer than expected.

    Args:
        task_token: Task token from state machine
        region: AWS region

    Returns:
        Response confirming heartbeat received
    """
    client = get_stepfunctions_client(region)

    try:
        response = client.send_task_heartbeat(taskToken=task_token)
        print(f"Heartbeat sent for long-running task")
        return response
    except ClientError as e:
        print(f"Error sending heartbeat: {e}")
        raise


# ==========================================================================
# EXAMPLE: COMPLETE WORKFLOW
# ==========================================================================

def example_create_and_run_workflow():
    """
    Complete example: Create state machine, run execution, retrieve history.
    """
    region = "us-east-1"

    # 1. Define state machine
    state_machine_definition = {
        "Comment": "Order processing workflow",
        "StartAt": "ValidateOrder",
        "States": {
            "ValidateOrder": {
                "Type": "Task",
                "Resource": "arn:aws:lambda:us-east-1:123456789012:function:ValidateOrder",
                "Next": "CheckInventory",
                "Retry": [
                    {
                        "ErrorEquals": ["States.TaskFailed"],
                        "IntervalSeconds": 1,
                        "MaxAttempts": 2,
                        "BackoffRate": 2.0,
                    }
                ],
                "Catch": [
                    {
                        "ErrorEquals": ["States.ALL"],
                        "Next": "OrderFailed",
                        "ResultPath": "$.validationError",
                    }
                ],
            },
            "CheckInventory": {
                "Type": "Choice",
                "Choices": [
                    {
                        "Variable": "$.inStock",
                        "BooleanEquals": True,
                        "Next": "ProcessPayment",
                    }
                ],
                "Default": "OutOfStock",
            },
            "ProcessPayment": {
                "Type": "Task",
                "Resource": "arn:aws:lambda:us-east-1:123456789012:function:ProcessPayment",
                "TimeoutSeconds": 300,
                "Next": "SendConfirmation",
            },
            "SendConfirmation": {
                "Type": "Task",
                "Resource": "arn:aws:states:::sns:publish",
                "Parameters": {
                    "TopicArn": "arn:aws:sns:us-east-1:123456789012:OrderNotifications",
                    "Message.$": "$",
                },
                "End": True,
            },
            "OutOfStock": {
                "Type": "Fail",
                "Error": "OutOfStock",
                "Cause": "Requested item not available",
            },
            "OrderFailed": {
                "Type": "Fail",
                "Error": "OrderValidationFailed",
                "Cause.$": "$.validationError",
            },
        },
    }

    # 2. Create state machine
    # Note: Replace with actual role ARN
    role_arn = "arn:aws:iam::123456789012:role/StepFunctionsRole"

    response = create_state_machine(
        name="OrderProcessing",
        definition=state_machine_definition,
        role_arn=role_arn,
        state_machine_type="STANDARD",
        region=region,
    )

    state_machine_arn = response["stateMachineArn"]

    # 3. Start execution
    execution_input = {
        "orderId": "12345",
        "customerId": "CUST001",
        "amount": 99.99,
        "inStock": True,
    }

    exec_response = start_execution(
        state_machine_arn=state_machine_arn,
        input_data=execution_input,
        execution_name="order-20240115-001",
        region=region,
    )

    execution_arn = exec_response["executionArn"]

    # 4. Wait for execution to complete
    print("\nWaiting for execution to complete...")
    max_wait = 60  # seconds
    poll_interval = 2
    elapsed = 0

    while elapsed < max_wait:
        exec_status = describe_execution(execution_arn, region=region)

        if exec_status["status"] in ["SUCCEEDED", "FAILED", "TIMED_OUT"]:
            break

        print(f"  Status: {exec_status['status']} (waited {elapsed}s)")
        time.sleep(poll_interval)
        elapsed += poll_interval

    # 5. Get execution history
    get_execution_history(execution_arn, region=region)

    # 6. If failed, analyze
    if exec_status["status"] == "FAILED":
        analyze_execution_failure(execution_arn, region=region)

    # 7. Clean up
    # delete_state_machine(state_machine_arn, region=region)

    return state_machine_arn, execution_arn


# ==========================================================================
# EXAMPLE: TASK TOKEN CALLBACK
# ==========================================================================

def example_lambda_with_callback():
    """
    Example Lambda function that uses task token callback.

    This is NOT directly runnable in this script, but shows the pattern:
    """

    code = '''
import json
import boto3

stepfunctions = boto3.client('stepfunctions')

def lambda_handler(event, context):
    """
    Lambda function called from Step Functions waitForTaskToken state.
    Performs async work, then completes task via callback.
    """

    task_token = event['taskToken']
    order_id = event['orderId']

    print(f"Processing order {order_id} asynchronously...")

    try:
        # Do async work here (e.g., call external API, process in SQS, etc.)
        result = process_order_async(order_id)

        # When done, send task success
        stepfunctions.send_task_success(
            taskToken=task_token,
            output=json.dumps({
                "orderId": order_id,
                "status": "completed",
                "result": result
            })
        )

    except Exception as e:
        # On error, send task failure
        stepfunctions.send_task_failure(
            taskToken=task_token,
            error="ProcessingFailed",
            cause=str(e)
        )

def process_order_async(order_id):
    # Placeholder for actual async work
    return {"processed": True}
    '''

    print("Lambda callback example (see code above):")
    print(code)


if __name__ == "__main__":
    print("AWS Step Functions Operations Examples\n")
    print("="*80)

    # Uncomment to run examples (requires valid AWS credentials and ARNs):
    # example_create_and_run_workflow()
    # example_lambda_with_callback()

    print("\nAvailable functions:")
    print("  - create_state_machine()")
    print("  - update_state_machine()")
    print("  - describe_state_machine()")
    print("  - list_state_machines()")
    print("  - delete_state_machine()")
    print("  - start_execution()")
    print("  - describe_execution()")
    print("  - list_executions()")
    print("  - stop_execution()")
    print("  - get_execution_history()")
    print("  - analyze_execution_failure()")
    print("  - send_task_success()")
    print("  - send_task_failure()")
    print("  - send_task_heartbeat()")
    print("\nSee docstrings for usage examples.")
