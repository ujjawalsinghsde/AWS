# Step Functions Interview Questions

## 1. Fundamental Questions

### Basic Concepts
1. **What is AWS Step Functions and its primary use cases?**
   - Serverless workflow orchestration service
   - Coordinates multiple AWS services (Lambda, EC2, RDS, SQS, SNS, etc)
   - Manages flow: sequential, parallel, conditional, retry logic
   - Use case: Multi-step processing (order → payment → fulfillment)

2. **Explain Step Functions states and state types.**
   - **Task**: Execute work (Lambda, EC2, DynamoDB)
   - **Choice**: Conditional branching
   - **Wait**: Delay execution
   - **Parallel**: Run multiple tasks simultaneously
   - **Map**: Iterate over arrays
   - **Pass**: Data transformation without work
   - **Succeed/Fail**: Terminal states

3. **Explain ASL (Amazon States Language).**
   - JSON-based state machine definition language
   - Defines states, transitions, and logic
   - `Next`: Move to next state
   - `Choices`: Conditional logic
   - `Catch`/`Retry`: Error handling
   - `ResultPath`: Data flow between states

4. **What are the two execution modes?**
   - **Standard**: Default, up to 1-year execution, at-least-once semantics
   - **Express**: Synchronous, up to 5-minute execution, exactly-once
   - Choose: Standard for long-running, Express for rapid/synchronous

5. **Explain error handling in Step Functions.**
   - `Retry`: Automatic retries with exponential backoff
   - `Catch`: Handle errors, transition to error handler state
   - Example:
   ```json
   {
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
         "Next": "ErrorHandler"
       }
     ]
   }
   ```

---

## 2. Intermediate Scenarios

### Workflow Design

6. **Scenario: Process order through multiple steps (payment → fulfillment → notification).**
   - Step 1 (Lambda): Validate order
   - Step 2 (Lambda): Process payment
   - Catch: If payment fails, notify customer
   - Step 3 (Parallel):
     - Simultaneously: Pack order (Step Function)
     - Simultaneously: Send confirmation email (SNS)
   - Step 4 (Wait): Wait 7 days
   - Step 5 (Lambda): Send follow-up email
   - Term: Succeed

7. **Scenario: Fan-out to multiple parallel processors.**
   - Order received
   - Map state: Process 100 items in parallel
   - Each item: Validate → Inventory check → Price lookup
   - Aggregate: Combine results
   - Pay special attention to concurrency limits

### Data Flow & Transformation

8. **How do you handle data between states?**
   - `ResultPath`: Where to put output
     - `$.result`: Put in result field
     - `null`: Discard output
   - `InputPath`: Select input data
   - `OutputPath`: Select output data
   - Example:
   ```json
   {
     "Type": "Task",
     "Resource": "arn:aws:lambda:region:account:function:process",
     "InputPath": "$.order",
     "ResultPath": "$.processedOrder",
     "OutputPath": "$",
     "Next": "NextState"
   }
   ```

---

## 3. Advanced Scenarios

### Long-Running Workflows & Callbacks

9. **Scenario: Human approval needed in workflow (order > $1000).**
   - Task: Send approval request
   - Wait: Use callback with task token
   - Human approves via email link
   - Resume: Execution continues
   - Code: Use `heartbeatSeconds` to avoid timeout
   ```json
   {
     "Type": "Task",
     "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
     "Parameters": {
       "QueueUrl": "approval-queue",
       "MessageBody": {
         "token.$": "$$.Task.Token",
         "orderId.$": "$.orderId"
       }
     },
     "TimeoutSeconds": 86400
   }
   ```

10. **Design long-running ETL workflow (12-hour data processing).**
    - Trigger: S3 file upload
    - Step 1: Notify start (SNS)
    - Step 2: AsyncInvoke Glue job
    - Step 3: Wait for completion
    - Step 4: Validate results
    - Step 5: Load to Redshift
    - Step 6: Notify completion
    - Monitoring: CloudWatch logs, execution history

### Error Handling Patterns

11. **Implement robust error handling with exponential backoff.**
    - Retry: Network timeouts (transient)
    - Catch: Business logic errors (permanent)
    - DLQ: Send failed orders to manual review
    - Alerting: SNS notification on failure
    ```json
    {
      "Catch": [
        {"ErrorEquals": ["PaymentFailed"], "Next": "NotifyPaymentFailure"},
        {"ErrorEquals": ["InventoryUnavailable"], "Next": "RetryTomorrow"},
        {"ErrorEquals": ["States.ALL"], "Next": "UnexpectedError"}
      ]
    }
    ```

---

## 4. Real-World Scenarios

12. **Scenario: Order workflow fails 10% of the time. Improve reliability.**
    - Analysis:
      1. CloudWatch Logs: Find failure reasons
      2. Execution History: Trace where failures occur
    - Improvements:
      - Add retry with exponential backoff
      - Implement DLQ for failed orders
      - Add manual intervention for specific errors
      - Monitoring: Alert on failure rate > 5%
      - Circuit breaker: Disable downstream service if failing

13. **Design payment processing with idempotency and rollback.**
    - Challenge: Payment service has duplicate issue
    - Solution:
      1. Payment task: Use `ChargeIdempotencyKey`
      2. If charge service fails: Retry attempts
      3. If ultimately fails: Rollback previous steps
      4. Manual intervention: Alert human for review
    - DynamoDB: Store idempotency keys to prevent duplicates

14. **Implement data transformation pipeline with validation.**
    - Step 1: Read from S3
    - Step 2: Validate data
    - Choice: Valid?
      - Yes: Transform (Step 3)
      - No: Move to InvalidData folder (Step 2b)
    - Step 3: Load to target
    - Step 4: Notify success

---

## 5. Monitoring & Debugging

15. **Monitor Step Functions workflows in production.**
    - CloudWatch Logs: All execution logs
    - CloudWatch Metrics: Duration, failures, throttles
    - Execution History: Trace execution path
    - Alarms:
      - Execution failures > 1% → Alert
      - Execution duration > SLA → Alert
    - Dashboard: Overall state machine health

16. **Troubleshoot failed executions.**
    - Steps:
      1. View execution history
      2. Identify failed state
      3. Check input/output data
      4. Review Lambda CloudWatch logs
      5. Check IAM permissions
      6. Validate downstream service (RDS, SQS, etc)

---

## 6. Cost Optimization

17. **Optimize Step Functions costs.**
    - Express vs Standard: Express cheaper for short workflows
    - Parallel execution: Pay per state transition (optimize parallelism)
    - Timeout: Set reasonable timeout (avoid long hangs)
    - Monitoring: Don't over-log
    - Avoid: Unnecessary retries, loops, waiting

---

## 7. Hands-On Examples

18. **Write Step Functions definition for order processing:**
    ```json
    {
      "Comment": "Order processing workflow",
      "StartAt": "ValidateOrder",
      "States": {
        "ValidateOrder": {
          "Type": "Task",
          "Resource": "arn:aws:lambda:region:account:function:validate-order",
          "Catch": [
            {
              "ErrorEquals": ["InvalidOrder"],
              "Next": "RejectOrder"
            }
          ],
          "Next": "ProcessPayment"
        },
        "ProcessPayment": {
          "Type": "Task",
          "Resource": "arn:aws:lambda:region:account:function:process-payment",
          "Retry": [
            {
              "ErrorEquals": ["PaymentTimeout"],
              "IntervalSeconds": 2,
              "MaxAttempts": 3,
              "BackoffRate": 2.0
            }
          ],
          "Catch": [
            {"ErrorEquals": ["PaymentFailed"], "Next": "NotifyFailure"}
          ],
          "Next": "FulfillOrder"
        },
        "FulfillOrder": {
          "Type": "Parallel",
          "Branches": [
            {
              "StartAt": "PackOrder",
              "States": {
                "PackOrder": {
                  "Type": "Task",
                  "Resource": "arn:aws:lambda:region:account:function:pack",
                  "End": true
                }
              }
            },
            {
              "StartAt": "SendConfirmation",
              "States": {
                "SendConfirmation": {
                  "Type": "Task",
                  "Resource": "arn:aws:sns:publish",
                  "End": true
                }
              }
            }
          ],
          "Next": "OrderComplete"
        },
        "OrderComplete": {
          "Type": "Succeed"
        },
        "NotifyFailure": {
          "Type": "Task",
          "Resource": "arn:aws:sns:publish",
          "Next": "RejectOrder"
        },
        "RejectOrder": {
          "Type": "Fail",
          "Error": "OrderRejected"
        }
      }
    }
    ```

19. **Lambda with Step Functions callback:**
    ```python
    import boto3
    import json

    stepfunctions = boto3.client('stepfunctions')

    def lambda_handler(event, context):
        task_token = event['task_token']
        order_id = event['order_id']

        try:
            # Process order
            result = process_order(order_id)

            # Notify Step Functions
            stepfunctions.send_task_success(
                taskToken=task_token,
                output=json.dumps({'orderId': order_id, 'status': 'success'})
            )

        except Exception as e:
            stepfunctions.send_task_failure(
                taskToken=task_token,
                error=str(type(e)),
                cause=str(e)
            )

    def process_order(order_id):
        # Business logic
        return True
    ```

---

## Tips for Interview Success

- **State machines design**: Practice complex workflows
- **Error handling**: Retry and Catch patterns
- **Data flow**: Understand ResultPath, InputPath, OutputPath
- **Long-running workflows**: Callbacks and timeouts
- **Parallel execution**: Map state and branching
- **Monitoring**: CloudWatch, execution history
- **Cost**: Choose right mode (Standard vs Express)
- **Integration**: Know which AWS services Step Functions integrates with

