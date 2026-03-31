# AWS Step Functions (Workflow Orchestration)

**Python boto3 code:** [step_functions_operations.py](./step_functions_operations.py)

---

## Table of Contents

1. [What is AWS Step Functions?](#1-what-is-aws-step-functions)
2. [Core Concepts](#2-core-concepts)
3. [State Machine Types](#3-state-machine-types)
4. [State Types & Transitions](#4-state-types--transitions)
5. [Amazon States Language (ASL)](#5-amazon-states-language-asl)
6. [Execution Flow & Behavior](#6-execution-flow--behavior)
7. [Error Handling - Retry & Catch](#7-error-handling---retry--catch)
8. [Integration Patterns](#8-integration-patterns)
9. [Input/Output Processing](#9-inputoutput-processing)
10. [Visual Workflow Editor](#10-visual-workflow-editor)
11. [IAM & Security](#11-iam--security)
12. [Monitoring & Logging](#12-monitoring--logging)
13. [Execution History & Debugging](#13-execution-history--debugging)
14. [Step Functions with Lambda](#14-step-functions-with-lambda)
15. [Step Functions with ECS/Batch](#15-step-functions-with-ecsbatch)
16. [Parallel & Distributed Processing](#16-parallel--distributed-processing)
17. [Map State for Batch Operations](#17-map-state-for-batch-operations)
18. [Cost Optimization](#18-cost-optimization)
19. [CLI Cheat Sheet](#19-cli-cheat-sheet)
20. [Best Practices](#20-best-practices)
21. [Advanced Topics](#21-advanced-topics)

---

## 1. What is AWS Step Functions?

**AWS Step Functions** is a managed workflow orchestration service that lets you coordinate multiple AWS services into serverless workflows using visual state machines.

### Key Characteristics

- **Visual Workflows** - Define workflows using a drag-and-drop editor or code (ASL)
- **Orchestration** - Coordinate Lambda, ECS, Batch, SNS, SQS, and 200+ AWS services
- **Serverless** - No infrastructure to manage; automatic scaling
- **Stateful** - Maintains execution state and history
- **Error Handling** - Built-in retry and catch mechanisms
- **Audit Trail** - Full execution history for debugging and compliance
- **Long-Running** - Supports workflows lasting up to 1 year

### When to Use Step Functions

| Use Case | Why Step Functions Fits |
|----------|-------------------------|
| Multi-step workflows | Coordinate complex business logic across services |
| Data pipelines | Orchestrate ETL with Lambda → Batch → DynamoDB |
| Approval workflows | Human-in-the-loop with task tokens |
| Microservices orchestration | Coordinate independent services reliably |
| Event-driven logic | Chain reactions triggered conditionally |
| Long-running processes | Workflows that span hours or days |
| Error recovery | Automatic retries with exponential backoff |

### Step Functions vs Other Services

| Aspect | Step Functions | EventBridge | SQS | Lambda Alone |
|--------|---|---|---|---|
| Visual workflows | ✓ | - | - | - |
| State management | ✓ | - | - | - |
| Long-running workflows | ✓ | - | ✓ (with polling) | ✗ (15 min max) |
| Error handling | ✓ (Retry/Catch) | - | ✓ (DLQ only) | - |
| Human approval | ✓ (Task tokens) | - | - | - |
| Execution history | ✓ | ✓ | - | - |
| Cost per transition | ~$0.000025 | $1 per 1M events | Varies | Per invocation |

---

## 2. Core Concepts

### 2.1 State Machine
A **state machine** is a JSON file that defines your workflow using Amazon States Language (ASL). It specifies states, transitions, and logic flow.

```json
{
  "Comment": "A simple Hello World example",
  "StartAt": "HelloWorld",
  "States": {
    "HelloWorld": {
      "Type": "Pass",
      "Result": "Hello World!",
      "End": true
    }
  }
}
```

### 2.2 State
A **state** is a step in your workflow. Each state performs an action or makes a decision.

**State types**: Task, Choice, Wait, Pass, Parallel, Map, Try-Catch, etc.

### 2.3 Execution
An **execution** is a single run of a state machine. Each execution receives input, follows the state machine logic, and produces output. Executions run sequentially by default but can be parallelized.

### 2.4 Execution History
Every step in an execution is logged with timestamps and data, creating a complete audit trail.

### 2.5 Transition
A **transition** is the movement from one state to another, determined by the workflow logic and exit conditions.

### 2.6 State Input/Output
Every state receives input (JSON) and may produce output that flows to the next state.

```
Input → State Logic → Output → Next State Input
```

---

## 3. State Machine Types

### 3.1 Standard Workflows

- **Execution duration**: Up to 1 year
- **State transitions**: ~1 million per second
- **Pricing**: Pay per state transition ($0.000025 per transitions)
- **Use case**: Most workflows, business processes, long-running operations
- **Execution model**: Asynchronous, history retained indefinitely

```json
{
  "StartAt": "ProcessOrder",
  "States": {
    "ProcessOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:ProcessOrder",
      "Next": "SendConfirmation"
    },
    "SendConfirmation": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "End": true
    }
  }
}
```

### 3.2 Express Workflows

- **Execution duration**: Up to 5 minutes
- **State transitions**: ~100,000 per second
- **Pricing**: Pay per execution and duration (billed in 100-ms increments)
- **Use case**: High-volume, quick-turnaround requests (API responses, stream processing)
- **Execution model**: Synchronous or asynchronous
- **Lambda timeout**: Best with Express workflows for API-style responses

```json
{
  "StartAt": "ValidateInput",
  "States": {
    "ValidateInput": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:ValidateInput",
      "End": true
    }
  }
}
```

### Standard vs Express Comparison

| Feature | Standard | Express |
|---------|----------|---------|
| Duration | 1 year | 5 minutes |
| Rate | 1M transitions/sec | 100K transitions/sec |
| Pricing | Per transition | Per execution |
| History | Unlimited retention | 5 min retention (async) / Lossy (sync) |
| Synchronous invocation | No | Yes (sync mode) |
| Best for | Long-running, batch | Real-time, API responses |

---

## 4. State Types & Transitions

### 4.1 Task State
Executes work, waits for completion, and handles errors.

```json
{
  "ProcessPayment": {
    "Type": "Task",
    "Resource": "arn:aws:lambda:us-east-1:123456789012:function:ProcessPayment",
    "TimeoutSeconds": 300,
    "Next": "CheckResult"
  }
}
```

**Supported resources**:
- Lambda functions
- AWS services (SQS, SNS, DynamoDB, ECS, Batch, etc.)
- HTTP endpoints (with Step Functions Service Integrations)
- Activity workers (manual code running elsewhere)

### 4.2 Choice State
Branches execution based on conditions (if/else logic).

```json
{
  "CheckPaymentStatus": {
    "Type": "Choice",
    "Choices": [
      {
        "Variable": "$.paymentStatus",
        "StringEquals": "SUCCESS",
        "Next": "SendConfirmation"
      },
      {
        "Variable": "$.paymentStatus",
        "StringEquals": "DECLINED",
        "Next": "HandleFailure"
      }
    ],
    "Default": "HandleUnknown"
  }
}
```

### 4.3 Wait State
Delays execution for a specified period.

```json
{
  "WaitForProcessing": {
    "Type": "Wait",
    "Seconds": 300,
    "Next": "CheckStatus"
  }
}
```

**Wait types**:
- `Seconds`: Fixed seconds
- `SecondsPath`: Seconds from input data (e.g., `$.delaySeconds`)
- `Timestamp`: Until a specific date/time
- `TimestampPath`: Timestamp from input data

### 4.4 Pass State
Transforms data without calling external services (useful for data enrichment).

```json
{
  "EnrichData": {
    "Type": "Pass",
    "Parameters": {
      "orderId.$": "$.id",
      "status": "PROCESSING",
      "timestamp.$": "$$.Execution.StartTime"
    },
    "Next": "ProcessOrder"
  }
}
```

### 4.5 Parallel State
Executes multiple branches simultaneously and waits for all to complete.

```json
{
  "ProcessMultipleTasks": {
    "Type": "Parallel",
    "Branches": [
      {
        "StartAt": "ProcessPayment",
        "States": {
          "ProcessPayment": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:...:ProcessPayment",
            "End": true
          }
        }
      },
      {
        "StartAt": "UpdateInventory",
        "States": {
          "UpdateInventory": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:...:UpdateInventory",
            "End": true
          }
        }
      }
    ],
    "Next": "FinalStep"
  }
}
```

### 4.6 Map State
Iterates over an array and executes the same state machine for each item (like a for-loop).

```json
{
  "ProcessOrders": {
    "Type": "Map",
    "ItemsPath": "$.orders",
    "MaxConcurrency": 5,
    "Iterator": {
      "StartAt": "ProcessSingleOrder",
      "States": {
        "ProcessSingleOrder": {
          "Type": "Task",
          "Resource": "arn:aws:lambda:...:ProcessOrder",
          "End": true
        }
      }
    },
    "Next": "FinalStep"
  }
}
```

### 4.7 Succeed & Fail States
Mark execution as successful or failed.

```json
{
  "SuccessState": {
    "Type": "Succeed"
  },
  "FailState": {
    "Type": "Fail",
    "Error": "PaymentFailed",
    "Cause": "Credit card declined"
  }
}
```

---

## 5. Amazon States Language (ASL)

ASL is a JSON-based language for defining state machines. Key concepts:

### 5.1 State Structure

```json
{
  "StateName": {
    "Type": "StateTpe",
    "Comment": "Optional description",
    "InputPath": "$.specificField",      // Transform input
    "OutputPath": "$.result",              // Select output
    "ResultPath": "$.processResult",      // Where to put result
    "Next": "NextStateName"               // Transition
  }
}
```

### 5.2 Input/Output/Result Paths

- **InputPath**: Select what part of the state input flows to the task
- **OutputPath**: Select what part of the state output flows to the next state
- **ResultPath**: Specify where the task result goes in the output

```json
{
  "ProcessTask": {
    "Type": "Task",
    "Resource": "arn:aws:lambda:...",
    "InputPath": "$.payload.data",        // Pass only this to Lambda
    "ResultPath": "$.lambdaOutput",       // Store result here
    "OutputPath": "$",                    // Pass entire JSON to next state
    "Next": "NextState"
  }
}
```

### 5.3 JSONPath Expressions

Step Functions uses JSONPath to reference data:

```
$           → Entire input
$.field     → Specific field
$[0]        → Array index
$.items[*]  → All array items
$.a.b.c     → Nested field
$$.Execution.Name  → Execution context
```

### 5.4 Context Object

Access execution context with `$$`:

```json
{
  "EnrichData": {
    "Type": "Pass",
    "Parameters": {
      "executionName.$": "$$.Execution.Name",
      "executionArn.$": "$$.Execution.Arn",
      "stateName.$": "$$.State.Name",
      "timestamp.$": "$$.Execution.StartTime"
    },
    "Next": "ProcessOrder"
  }
}
```

---

## 6. Execution Flow & Behavior

### 6.1 Execution Lifecycle

```
Created → Running → Succeeded/Failed/Timed Out
           ↓
      Step-by-step state transitions with full history
```

### 6.2 Execution Status

- **RUNNING** - Actively executing
- **SUCCEEDED** - Completed successfully
- **FAILED** - Failed (Check error/cause)
- **TIMED OUT** - Exceeded timeout
- **ABORTED** - Manually stopped

### 6.3 Input/Output Flow

```json
// Initial input
{
  "orderId": "12345",
  "amount": 99.99
}

// Passes through states, transformed by Each state
// Final output
{
  "orderId": "12345",
  "amount": 99.99,
  "processedAt": "2024-01-15T10:00:00Z",
  "status": "COMPLETED"
}
```

### 6.4 Execution Timeout

Set timeout at state machine or state level:

```json
{
  "TimeoutSeconds": 1800,  // 30 minutes for entire execution
  "States": {
    "Task1": {
      "TimeoutSeconds": 300,  // 5 minutes for this task
      ...
    }
  }
}
```

---

## 7. Error Handling - Retry & Catch

### 7.1 Retry Policy

Automatically retry failed tasks with exponential backoff:

```json
{
  "ProcessPayment": {
    "Type": "Task",
    "Resource": "arn:aws:lambda:...",
    "Retry": [
      {
        "ErrorEquals": ["States.TaskFailed"],
        "IntervalSeconds": 2,
        "MaxAttempts": 3,
        "BackoffRate": 2.0
      }
    ],
    "Catch": [
      {
        "ErrorEquals": ["States.ALL"],
        "Next": "HandleError"
      }
    ],
    "Next": "Success"
  }
}
```

**Retry parameters**:
- `ErrorEquals`: Which errors to retry
- `IntervalSeconds`: Initial delay (2, 4, 8 seconds with BackoffRate)
- `MaxAttempts`: Number of retries (not total attempts)
- `BackoffRate`: Exponential multiplier (usually 2.0)

### 7.2 Catch Block

Handle errors when retries fail:

```json
{
  "UpdateDatabase": {
    "Type": "Task",
    "Resource": "arn:aws:states:::dynamodb:updateItem",
    "Catch": [
      {
        "ErrorEquals": ["States.TaskFailed"],
        "Next": "LogError",
        "ResultPath": "$.error"  // Store error info
      },
      {
        "ErrorEquals": ["States.ALL"],
        "Next": "FallbackHandler"
      }
    ],
    "Next": "Success"
  },
  "LogError": {
    "Type": "Task",
    "Resource": "arn:aws:lambda:...:LogError",
    "End": true
  }
}
```

### 7.3 Error Matching

- `States.ALL` - Matches any error
- `States.TaskFailed` - Task execution error
- `States.Timeout` - Timeout exceeded
- Custom error names from your Lambda functions

---

## 8. Integration Patterns

### 8.1 Call Lambda (Request-Response)

Task runs Lambda and waits for response (default):

```json
{
  "CallLambda": {
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke",
    "Parameters": {
      "FunctionName": "MyFunction",
      "Payload.$": "$"
    },
    "End": true
  }
}
```

### 8.2 Call Lambda (Wait for Callback)

Lambda triggers asynchronous work and returns a task token:

```json
{
  "AsyncLambdaTask": {
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
    "Parameters": {
      "FunctionName": "MyAsyncFunction",
      "Payload": {
        "taskToken.$": "$$.Task.Token"  // Pass token to Lambda
      }
    },
    "Next": "ProcessResult"
  }
}
```

Lambda completes the token when done:

```python
import boto3
import json

stepfunctions = boto3.client('stepfunctions')

def lambda_handler(event, context):
    task_token = event['taskToken']

    # Do async work...

    # Complete the task
    stepfunctions.send_task_success(
        taskToken=task_token,
        output=json.dumps({"status": "completed"})
    )
```

### 8.3 Run ECS Task

```json
{
  "RunECSTask": {
    "Type": "Task",
    "Resource": "arn:aws:states:::ecs:runTask.sync",
    "Parameters": {
      "LaunchType": "FARGATE",
      "Cluster": "my-cluster",
      "TaskDefinition": "my-task",
      "NetworkConfiguration": {
        "AwsvpcConfiguration": {
          "Subnets": ["subnet-123"],
          "SecurityGroups": ["sg-456"]
        }
      }
    },
    "Next": "ProcessResults"
  }
}
```

### 8.4 Submit Batch Job

```json
{
  "SubmitBatchJob": {
    "Type": "Task",
    "Resource": "arn:aws:states:::batch:submitJob.sync",
    "Parameters": {
      "JobDefinition": "my-job-def",
      "JobQueue": "my-queue",
      "JobName": "batch-job-1"
    },
    "Next": "CheckResults"
  }
}
```

### 8.5 Publish to SNS/SQS

```json
{
  "SendNotification": {
    "Type": "Task",
    "Resource": "arn:aws:states:::sns:publish",
    "Parameters": {
      "TopicArn": "arn:aws:sns:us-east-1:123456789012:MyTopic",
      "Message.$": "$"
    },
    "End": true
  }
}
```

### 8.6 DynamoDB Operations

```json
{
  "UpdateOrder": {
    "Type": "Task",
    "Resource": "arn:aws:states:::dynamodb:updateItem",
    "Parameters": {
      "TableName": "Orders",
      "Key": {
        "orderId": {
          "S.$": "$.orderId"
        }
      },
      "AttributeUpdates": {
        "status": {
          "Action": "PUT",
          "Value": {
            "S": "COMPLETED"
          }
        }
      }
    },
    "End": true
  }
}
```

### 8.7 Http Tasks (REST APIs)

```json
{
  "CallExternalAPI": {
    "Type": "Task",
    "Resource": "arn:aws:states:::http:invoke",
    "Parameters": {
      "ApiEndpoint": "https://api.example.com/process",
      "Method": "POST",
      "Headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer token123"
      },
      "Body.$": "$.payload",
      "Authentication": {
        "RoleArn": "arn:aws:iam::123456789012:role/HttpTaskRole"
      }
    },
    "End": true
  }
}
```

---

## 9. Input/Output Processing

### 9.1 Data Transformation
Use Pass state to enrich/transform data without external calls:

```json
{
  "TransformData": {
    "Type": "Pass",
    "Parameters": {
      "orderId.$": "$.id",
      "customerName.$": "$.customer.name",
      "totalAmount.$": "$.items[*].price",
      "timestamp.$": "$$.Execution.StartTime",
      "status": "PROCESSING"
    },
    "Next": "ProcessOrder"
  }
}
```

### 9.2 Filtering Array Elements

```json
{
  "Type": "Task",
  "Resource": "arn:aws:lambda:...",
  "InputPath": "$.orders[0:5]",  // Pass first 5 orders
  "Next": "ProcessOrders"
}
```

### 9.3 Complex JSONPath Transformations

```json
{
  "Type": "Pass",
  "Parameters": {
    "processed.$": "$.items[?(@.price > 100)]",  // Filter by price
    "count.$": "$.items | length(@)",             // Count items
    "names.$": "$.items[*].name"                  // Extract all names
  },
  "Next": "NextState"
}
```

### 9.4 ResultPath Examples

```json
// Include result with original input
"ResultPath": "$"           // Replaces entire input with result

// Append result to a field
"ResultPath": "$.result"    // { original fields, result: {...} }

// Discard result
"ResultPath": null          // Passes original input to next state

// Nested path
"ResultPath": "$.data[0].processed"
```

---

## 10. Visual Workflow Editor

### 10.1 Using the Console Editor

1. Go to AWS Step Functions console
2. Click "Create State Machine"
3. Choose **Design** or **Code** tab
4. **Design**: Drag-and-drop states
5. **Code**: Write ASL JSON
6. Visual editor updates as you type

### 10.2 Previewing Execution

- Click "Start execution" in console
- Provide sample input JSON
- Watch visual progress highlighting current state
- See input/output at each step

### 10.3 Exporting State Machine

Download state machine definition as JSON from console:
- Settings → Download definition

---

## 11. IAM & Security

### 11.1 Step Functions IAM Role

Create an IAM role that Step Functions assumes to call services:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction",
        "states:StartExecution"
      ],
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:UpdateItem",
        "dynamodb:GetItem"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/Orders"
    },
    {
      "Effect": "Allow",
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:us-east-1:123456789012:*"
    }
  ]
}
```

### 11.2 Resource-Based Policy

Control who can invoke your state machine:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "states.amazonaws.com"
      },
      "Action": "states:StartExecution",
      "Resource": "arn:aws:states:us-east-1:123456789012:stateMachine:MyWorkflow"
    },
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111111111111:role/ExternalRole"
      },
      "Action": "states:StartExecution",
      "Resource": "*"
    }
  ]
}
```

### 11.3 Secrets & Credentials

Use Secrets Manager or Systems Manager Parameter Store:

```json
{
  "CallSecureAPI": {
    "Type": "Task",
    "Resource": "arn:aws:states:::http:invoke",
    "Parameters": {
      "ApiEndpoint": "https://api.example.com/process",
      "Method": "POST",
      "Headers": {
        "Authorization.$": "$.credentials.apiKey"
      },
      "Body.$": "$.data"
    },
    "End": true
  }
}
```

Retrieve secrets in Lambda before passing to Step Functions.

---

## 12. Monitoring & Logging

### 12.1 CloudWatch Logs

Enable logging in state machine:

```json
{
  "LoggingConfiguration": {
    "Level": "ALL",
    "IncludeExecutionData": true,
    "Destinations": [
      {
        "CloudWatchLogsLogGroup": {
          "LogGroupName": "/aws/stepfunctions/MyWorkflow"
        }
      }
    ]
  }
}
```

Log levels:
- `ERROR` - Only errors
- `ALL` - All events and data

### 12.2 CloudWatch Metrics

Step Functions publishes metrics:

- `ExecutionsStarted`
- `ExecutionsSucceeded`
- `ExecutionsFailed`
- `ExecutionTime` (duration)
- Dimension: `StateMachineArn`

Create CloudWatch alarms:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name sf-failures \
  --metric-name ExecutionsFailed \
  --namespace AWS/States \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts
```

### 12.3 EventBridge Integration

Capture execution events:

```json
{
  "Name": "capture-state-machine-events",
  "EventBusName": "default",
  "EventPattern": {
    "source": ["aws.states"],
    "detail-type": ["Execution Status Change"],
    "detail": {
      "status": ["FAILED", "TIMED_OUT"]
    }
  },
  "State": "ENABLED",
  "Targets": [
    {
      "Arn": "arn:aws:lambda:us-east-1:123456789012:function:HandleFailure",
      "RoleArn": "arn:aws:iam::123456789012:role/EventBridgeRole"
    }
  ]
}
```

---

## 13. Execution History & Debugging

### 13.1 Viewing Execution History

1. Open state machine → Executions
2. Click on execution ID
3. See full step-by-step history:
   - Timestamp
   - State name
   - Type (Enter/Exit/Task)
   - Input/output data
   - Duration
   - Status

### 13.2 Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `States.TaskFailed` | Task returned error | Check Lambda logs, add Retry/Catch |
| `States.Timeout` | Execution exceeded timeout | Increase TimeoutSeconds or optimize task |
| `States.TaskStateTimeout` | State timeout exceeded | Check TimeoutSeconds at state level |
| `InvalidExecutionInput` | Input schema mismatch | Validate input matches state machine |
| `States.Runtime` | Lambda runtime error | Check Lambda IAM permissions, logs |

### 13.3 Debugging Tips

- Use `Pass` states to inspect data: Add OutputPath or ResultPath to see transformations
- Enable verbose logging: Set LoggingConfiguration to `ALL`
- Monitor CloudWatch Logs: `/aws/stepfunctions/YourStateMachine`
- Test Lambda functions independently before integrating
- Use `$$.Execution.Name` and `$$.State.Name` for tracing
- Check IAM role permissions match resource ARNs

---

## 14. Step Functions with Lambda

### 14.1 Synchronous Lambda Invocation
Step Functions waits for Lambda to complete and returns result.

```json
{
  "InvokeLambda": {
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke",
    "Parameters": {
      "FunctionName": "ProcessOrder:1",
      "Payload.$": "$"
    },
    "Retry": [
      {
        "ErrorEquals": ["States.TaskFailed"],
        "IntervalSeconds": 2,
        "BackoffRate": 2.0,
        "MaxAttempts": 3
      }
    ],
    "Catch": [
      {
        "ErrorEquals": ["States.ALL"],
        "Next": "HandleError",
        "ResultPath": "$.lambdaError"
      }
    ],
    "Next": "ProcessResult"
  }
}
```

### 14.2 Asynchronous Lambda with Task Token
Lambda runs in background, completes task via callback:

```python
import boto3
import json

stepfunctions = boto3.client('stepfunctions')

def async_handler(event, context):
    task_token = event['taskToken']
    order_id = event['orderId']

    # Trigger async work (e.g., start SQS consumer)
    # Handler returns immediately

    # Later, when async work completes...
    stepfunctions.send_task_success(
        taskToken=task_token,
        output=json.dumps({"orderId": order_id, "status": "completed"})
    )
```

Step Functions state:
```json
{
  "AsyncTask": {
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
    "Parameters": {
      "FunctionName": "AsyncProcessor",
      "Payload": {
        "orderId.$": "$.orderId",
        "taskToken.$": "$$.Task.Token"
      }
    },
    "TimeoutSeconds": 3600,
    "Next": "ProcessResult"
  }
}
```

---

## 15. Step Functions with ECS/Batch

### 15.1 Run ECS Task (Fargate)

```json
{
  "RunECSTask": {
    "Type": "Task",
    "Resource": "arn:aws:states:::ecs:runTask.sync",
    "Parameters": {
      "LaunchType": "FARGATE",
      "Cluster": "arn:aws:ecs:us-east-1:123456789012:cluster/my-cluster",
      "TaskDefinition": "my-task:1",
      "NetworkConfiguration": {
        "AwsvpcConfiguration": {
          "Subnets": ["subnet-123", "subnet-456"],
          "SecurityGroups": ["sg-789"],
          "AssignPublicIp": "ENABLED"
        }
      },
      "Overrides": {
        "ContainerOverrides": [
          {
            "Name": "my-container",
            "Environment": [
              {
                "Name": "ORDER_ID",
                "Value.$": "$.orderId"
              }
            ]
          }
        ]
      }
    },
    "Next": "ProcessResults"
  }
}
```

### 15.2 Submit AWS Batch Job

```json
{
  "SubmitBatchJob": {
    "Type": "Task",
    "Resource": "arn:aws:states:::batch:submitJob.sync",
    "Parameters": {
      "JobName": "DataProcessing",
      "JobQueue": "default-queue",
      "JobDefinition": "data-processing-job",
      "ContainerOverrides": {
        "Environment": [
          {
            "Name": "S3_INPUT",
            "Value.$": "$.inputBucket"
          }
        ]
      }
    },
    "TimeoutSeconds": 7200,
    "Next": "AnalyzeResults"
  }
}
```

---

## 16. Parallel & Distributed Processing

### 16.1 Running Tasks in Parallel

```json
{
  "ProcessAllSteps": {
    "Type": "Parallel",
    "Branches": [
      {
        "StartAt": "ProcessPayment",
        "States": {
          "ProcessPayment": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:...:ProcessPayment",
            "End": true
          }
        }
      },
      {
        "StartAt": "UpdateInventory",
        "States": {
          "UpdateInventory": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:...:UpdateInventory",
            "End": true
          }
        }
      },
      {
        "StartAt": "SendNotification",
        "States": {
          "SendNotification": {
            "Type": "Task",
            "Resource": "arn:aws:states:::sns:publish",
            "Parameters": {
              "TopicArn": "arn:aws:sns:us-east-1:123456789012:Orders"
            },
            "End": true
          }
        }
      }
    ],
    "Next": "AggregateResults"
  },
  "AggregateResults": {
    "Type": "Pass",
    "Parameters": {
      "payment.$": "$[0]",
      "inventory.$": "$[1]",
      "notification.$": "$[2]"
    },
    "End": true
  }
}
```

Results from parallel branches combine into an array: `[$[0], $[1], $[2]]`

---

## 17. Map State for Batch Operations

### 17.1 Basic Map (Sequential)

```json
{
  "ProcessOrders": {
    "Type": "Map",
    "ItemsPath": "$.orders",
    "MaxConcurrency": 0,  // 0 = sequential
    "Iterator": {
      "StartAt": "ProcessItem",
      "States": {
        "ProcessItem": {
          "Type": "Task",
          "Resource": "arn:aws:lambda:...:ProcessOrder",
          "End": true
        }
      }
    },
    "Next": "FinalStep"
  }
}
```

### 17.2 Map with Concurrency

Process multiple items in parallel (with limited concurrency):

```json
{
  "ProcessOrders": {
    "Type": "Map",
    "ItemsPath": "$.orders",
    "MaxConcurrency": 5,  // Process 5 items at a time
    "Iterator": {
      "StartAt": "ProcessItem",
      "States": {
        "ProcessItem": {
          "Type": "Task",
          "Resource": "arn:aws:lambda:...:ProcessOrder",
          "End": true
        }
      }
    },
    "ResultPath": "$.processedOrders",  // Store results here
    "Next": "Summarize"
  }
}
```

### 17.3 Map with Try-Catch

Handle failures in Map iterations:

```json
{
  "ProcessOrders": {
    "Type": "Map",
    "ItemsPath": "$.orders",
    "MaxConcurrency": 10,
    "Iterator": {
      "StartAt": "ProcessItem",
      "States": {
        "ProcessItem": {
          "Type": "Task",
          "Resource": "arn:aws:lambda:...:ProcessOrder",
          "Catch": [
            {
              "ErrorEquals": ["States.ALL"],
              "Next": "LogFailure",
              "ResultPath": "$.error"
            }
          ],
          "End": true
        },
        "LogFailure": {
          "Type": "Pass",
          "Parameters": {
            "status": "FAILED",
            "error.$": "$.error"
          },
          "End": true
        }
      }
    },
    "Next": "FinalStep"
  }
}
```

---

## 18. Cost Optimization

### 18.1 Standard vs Express Pricing

| Metric | Standard | Express |
|--------|----------|---------|
| State transitions | $0.000025 per transition | $1.00 per 1M requests |
| Typical 5-state workflow | ~$0.000125 | ~$1.00 |
| 1000 workflows/day | ~$3.75/month | ~$30/month |

**Choose Express for**: High-volume API responses, client-facing APIs
**Choose Standard for**: Batch jobs, long-running tasks

### 18.2 Optimization Tips

1. **Minimize state transitions**: Combine logic in tasks where possible
2. **Use Pass states wisely**: Don't add unnecessary states
3. **Batch items in Map**: Use MaxConcurrency to control resource usage
4. **Monitor execution patterns**: Check console metrics for efficiency
5. **Clean up old state machines**: Archive or delete unused ones
6. **Use task tokens for long-running tasks**: More cost-effective than polling

### 18.3 Example Cost Calculation

Standard workflow: Sales order processing (5 states)
- 10,000 orders/month
- Cost: 10,000 executions × 5 transitions × $0.000025 = **$1.25/month**

Express workflow: API response from client (3 states)
- 1M requests/month
- Cost: $1.00/million × 1M = **$1.00/month**

---

## 19. CLI Cheat Sheet

### Create State Machine

```bash
aws stepfunctions create-state-machine \
  --name MyWorkflow \
  --definition file://state-machine.json \
  --role-arn arn:aws:iam::123456789012:role/StepFunctionsRole \
  --type STANDARD
```

### Start Execution

```bash
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:123456789012:stateMachine:MyWorkflow \
  --name execution-123 \
  --input '{"orderId":"12345"}'
```

### Get Execution Status

```bash
aws stepfunctions describe-execution \
  --execution-arn arn:aws:states:us-east-1:123456789012:execution:MyWorkflow:execution-123
```

### Get Execution History

```bash
aws stepfunctions get-execution-history \
  --execution-arn arn:aws:states:us-east-1:123456789012:execution:MyWorkflow:execution-123
```

### List Executions

```bash
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:123456789012:stateMachine:MyWorkflow
```

### Update State Machine

```bash
aws stepfunctions update-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:123456789012:stateMachine:MyWorkflow \
  --definition file://updated-state-machine.json
```

### Stop Execution

```bash
aws stepfunctions stop-execution \
  --execution-arn arn:aws:states:us-east-1:123456789012:execution:MyWorkflow:execution-123
```

### Delete State Machine

```bash
aws stepfunctions delete-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:123456789012:stateMachine:MyWorkflow
```

### Send Task Success (Callback)

```bash
aws stepfunctions send-task-success \
  --task-token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... \
  --output '{"status":"completed","result":"success"}'
```

### Send Task Failure (Callback)

```bash
aws stepfunctions send-task-failure \
  --task-token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... \
  --error "ProcessingFailed" \
  --cause "Invalid order data"
```

---

## 20. Best Practices

### 20.1 Design Patterns

1. **Use Choice for Branching**: Clear conditional logic → Easy debugging
2. **Retry + Catch Pattern**: Always add retry for transient failures
3. **Data Transformation in Pass**: Don't waste Lambda invocations
4. **Parallel for Independence**: Run parallel branches for truly independent tasks
5. **Map for Collections**: Process arrays with automatic iteration

### 20.2 Error Handling

- Always add `Retry` for transient errors (network, throttling)
- Always add `Catch` for permanent failures (invalid input)
- Use exponential backoff: `BackoffRate: 2.0`
- Store errors in `ResultPath` for auditing
- Monitor CloudWatch logs for error patterns

### 20.3 Performance

- Keep state machines to <250 states for readability
- Use Express workflows for API responses (<5 min)
- Use Standard workflows for batch/long-running (days/months)
- Batch database writes: Use DynamoDB batch operations
- Leverage Parallel/Map for concurrent operations

### 20.4 Security

- Use separate IAM roles per workflow
- Grant least-privilege permissions
- Use Secrets Manager for credentials
- Enable CloudWatch logging with `IncludeExecutionData`
- Audit state machine changes with CloudTrail

### 20.5 Monitoring

- Create CloudWatch alarms for `ExecutionsFailed`
- Monitor execution duration for performance regression
- Log all executions for compliance
- Use EventBridge to trigger actions on failures
- Set up dashboards for state machine health

### 20.6 Cost Management

- Choose `Standard` for batch (1 year, cheap per transition)
- Choose `Express` for APIs (<5 min, fixed per request)
- Minimize unnecessary state transitions
- Cache Lambda results where possible
- Review execution history monthly for optimization opportunities

---

## 21. Advanced Topics

### 21.1 Nested State Machines

Call one state machine from another:

```json
{
  "CallNestedWorkflow": {
    "Type": "Task",
    "Resource": "arn:aws:states:::states:startExecution.sync:2",
    "Parameters": {
      "StateMachineArn": "arn:aws:states:us-east-1:123456789012:stateMachine:NestedWorkflow",
      "Input.$": "$"
    },
    "Next": "ProcessResult"
  }
}
```

### 21.2 Distributed Tracing

Use X-Ray with Step Functions:

```json
{
  "LoggingConfiguration": {
    "Level": "ALL",
    "IncludeExecutionData": true,
    "Destinations": [
      {
        "CloudWatchLogsLogGroup": {
          "LogGroupName": "/aws/stepfunctions/MyWorkflow"
        }
      }
    ]
  },
  "TracingConfiguration": {
    "Enabled": true
  }
}
```

### 21.3 Human-In-The-Loop with Task Tokens

Pause execution, wait for external approval, then resume:

```json
{
  "ApprovalRequired": {
    "Type": "Task",
    "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
    "Parameters": {
      "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/approvals",
      "MessageBody": {
        "orderId.$": "$.orderId",
        "taskToken.$": "$$.Task.Token"
      }
    },
    "TimeoutSeconds": 86400,  // 24 hours
    "Next": "ProcessApproval"
  }
}
```

External process approves via CLI:
```bash
aws stepfunctions send-task-success \
  --task-token <token> \
  --output '{"approved":true}'
```

### 21.4 Dynamic Parallelism

Parallel execution count based on input data:

```json
{
  "CreateDynamicBranches": {
    "Type": "Pass",
    "Parameters": {
      "branches.$": "$.orders | [.[] | {item: ., processInParallel: true}]"
    },
    "Next": "ProcessDynamicParallel"
  }
}
```

This pattern allows creating branches dynamically based on input.

---

## Summary

AWS Step Functions provides sophisticated workflow orchestration for:
- **Multi-step processes** with clear state transitions
- **Error handling** with automatic retries and fallbacks
- **Parallel execution** for independent tasks
- **Batch processing** with Map iterations
- **Integration** with 200+ AWS services
- **Auditability** with complete execution history

Start with simple workflows (Lambda → SNS) and evolve to complex orchestrations (multi-service pipelines, approval workflows, distributed transactions).

**Next**: Read `step_functions_operations.py` for practical boto3 examples!
