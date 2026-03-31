# AWS API Gateway

**Table of Contents**
- [Fundamentals](#fundamentals)
- [API Types](#api-types)
- [Creating & Managing APIs](#creating--managing-apis)
- [Resources & Methods](#resources--methods)
- [Integration Types](#integration-types)
- [Request/Response Transformation](#requestresponse-transformation)
- [Authorization & Authentication](#authorization--authentication)
- [CORS Configuration](#cors-configuration)
- [Caching](#caching)
- [Throttling & Quotas](#throttling--quotas)
- [Monitoring & Logging](#monitoring--logging)
- [Stages & Versioning](#stages--versioning)
- [Custom Domains](#custom-domains)
- [Advanced Patterns](#advanced-patterns)
- [Best Practices & Security](#best-practices--security)

---

## Fundamentals

### What is API Gateway?

AWS API Gateway is a fully managed service that enables developers to create, publish, and manage APIs at any scale. It acts as a "front door" for applications to access backend services, data, and functionality.

**Key Value Propositions:**
- **Managed Service**: No servers to manage — AWS handles scaling, patching, and availability
- **Multiple API Types**: REST APIs, HTTP APIs, and WebSocket APIs
- **Integration Hub**: Connect to Lambda, HTTP endpoints, AWS services (DynamoDB, SNS, SQS, etc.)
- **Security**: Built-in authorization, throttling, request validation, and encryption
- **Developer Experience**: Mock responses, request transformation, caching, API versioning

### When to Use API Gateway

✅ **Use API Gateway when:**
- Building REST/HTTP APIs for microservices
- Creating event-driven architectures with Lambda
- Exposing AWS services as APIs (e.g., DynamoDB directly)
- Building WebSocket applications (real-time chat, notifications)
- Need multi-stage deployments (dev, staging, prod)
- Require API versioning and traffic throttling

❌ **Avoid if:**
- Very simple internal services (consider direct Lambda URLs)
- Extremely latency-sensitive (though API Gateway latency is ~100ms)
- Only need basic HTTP routing (ALB might be simpler)

### Core Components

```
Client Requests
    ↓
[API Gateway]
    ├── Request Validation
    ├── Authorization
    ├── Transformation
    ├── Caching
    ├── Throttling
    ↓
[Integration]
    ├── Lambda
    ├── HTTP Endpoints
    ├── AWS Services
    └── Mock Responses
    ↓
Response (Transformed)
    ↓
Client
```

---

## API Types

### 1. REST APIs

**Traditional RESTful architecture** with full feature set.

**When to use:**
- Complex APIs with many features and configurations
- Require request/response models and schemas
- Need all authorization types (OAuth, Cognito, custom authorizers)
- Legacy applications expecting full REST API features

**Characteristics:**
```
Endpoint: https://api-id.execute-api.region.amazonaws.com/stage/resource
Cost: Higher per request ($3.50 per million requests)
Latency: ~100ms additional
Features: Full request mapping, response mapping, models, validators
```

**Example:**
```bash
GET /users/{userId}           # Get user
POST /users                   # Create user
PUT /users/{userId}           # Update user
DELETE /users/{userId}        # Delete user
```

### 2. HTTP APIs

**Newer, lightweight alternative** with ~70% cost savings and faster performance.

**When to use:**
- Building modern APIs without legacy requirements
- Cost optimization is important
- Need simple authorization (API Key, JWT, basic)
- Performance is critical

**Characteristics:**
```
Endpoint: https://api-id.execute-api.region.amazonaws.com/stage/resource
Cost: Lower per request ($0.90 per million requests)
Latency: ~50ms additional (faster than REST)
Features: Simplified structure, JWT native support, subset of REST features
```

**Comparison: REST vs HTTP APIs**
| Feature | REST API | HTTP API |
|---------|----------|----------|
| Cost per 1M requests | $3.50 | $0.90 |
| Caching | ✓ | ✗ |
| Request Mapping Templates | ✓ | Limited (not full VTL) |
| Response Mapping | ✓ | Limited |
| API Keys | ✓ | ✓ |
| Legacy OAuth | ✓ | ✗ |
| Lambda Authorizers | ✓ | ✓ |
| CORS | ✓ | ✓ (simpler) |
| Request Validators | ✓ | ✗ |
| X-Ray Tracing | ✓ | ✓ |

### 3. WebSocket APIs

**Real-time, bidirectional communication** for applications needing persistent connections.

**When to use:**
- Chat applications
- Real-time notifications
- Live dashboards
- Collaborative editing tools

**Characteristics:**
```
Connection Management: $0.25/million connection minutes
Message Routing: $1.00 per million messages
Persistent bidirectional connection
```

---

## Creating & Managing APIs

### Creating a REST API

```python
import boto3

apigw = boto3.client('apigateway', region_name='us-east-1')

# Create API
response = apigw.create_rest_api(
    name='MyUserAPI',
    description='User management API',
    endpointConfiguration={'types': ['REGIONAL']},  # REGIONAL or EDGE
    policy={  # Optional: Resource policy
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": "*",
                "Action": "execute-api:Invoke",
                "Resource": "execute-api:/*"
            }
        ]
    }
)

api_id = response['id']
print(f"API Created: {api_id}")
```

### Creating an HTTP API

```python
# HTTP APIs are simpler
response = apigw.create_api(
    Name='MyUserAPI',
    ProtocolType='HTTP',
    Description='User management HTTP API',
    CorsConfiguration={
        'AllowCredentials': True,
        'AllowHeaders': ['Content-Type', 'Authorization'],
        'AllowMethods': ['GET', 'POST', 'PUT', 'DELETE'],
        'AllowOrigins': ['https://example.com'],
        'ExposeHeaders': ['x-custom-header'],
        'MaxAge': 300
    }
)
```

### Endpoint Configuration Types

```python
# REGIONAL: Low latency within a region (recommended)
{'types': ['REGIONAL']}

# EDGE: CloudFront distribution for global latency optimization
{'types': ['EDGE']}

# PRIVATE: Only accessible from VPC
{'types': ['PRIVATE']}
```

---

## Resources & Methods

### Creating Resources & Methods

```python
# Get root resource
resources = apigw.get_resources(restApiId=api_id)
root_id = [r for r in resources['items'] if r['path'] == '/'][0]['id']

# Create /users resource
users_resource = apigw.create_resource(
    restApiId=api_id,
    parentId=root_id,
    pathPart='users'
)
users_id = users_resource['id']

# Create /users/{userId} resource
user_resource = apigw.create_resource(
    restApiId=api_id,
    parentId=users_id,
    pathPart='{userId}'
)
user_id = user_resource['id']

# Create GET method on /users/{userId}
apigw.put_method(
    restApiId=api_id,
    resourceId=user_id,
    httpMethod='GET',
    authorizationType='AWS_IAM',  # Authorization type
    requestParameters={
        'method.request.path.userId': True,  # Path parameter is required
        'method.request.querystring.includeDetails': False  # Optional query param
    }
)
```

### Method Request Parameters

```python
apigw.put_method(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='POST',
    authorizationType='NONE',
    requestParameters={
        'method.request.path.userId': True,           # Path parameter
        'method.request.querystring.limit': False,    # Query string (optional)
        'method.request.header.X-API-Key': True       # Header (required)
    }
)
```

---

## Integration Types

### 1. Lambda Integration

**Most common pattern** — invoke Lambda functions from API Gateway.

```python
# Create Lambda integration
apigw.put_integration(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='GET',
    type='AWS_PROXY',  # Lambda proxy (recommended)
    integrationHttpMethod='POST',  # Always POST for Lambda
    uri=f'arn:aws:apigateway:region:lambda:path/2015-03-31/functions/arn:aws:lambda:region:account:function:function-name/invocations',
    passthroughBehavior='WHEN_NO_MATCH'  # Pass request if no mapping template
)

# Lambda Proxy Response Format (recommended)
{
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json"
    },
    "body": json.dumps({"message": "Hello"})
}
```

**Lambda Proxy vs Non-Proxy:**

| Aspect | Proxy | Non-Proxy |
|--------|-------|-----------|
| Lambda Response | Must return statusCode, headers, body | Returns custom format |
| Transformation | Automatic | Requires mapping templates |
| Request Format | Full request object | Must map in VTL |
| Learning Curve | Simpler | Steeper |
| Flexibility | Less flexible | Most flexible |

### 2. HTTP Integration

**Invoke external HTTP services.**

```python
apigw.put_integration(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='GET',
    type='HTTP',  # or HTTP_PROXY
    integrationHttpMethod='GET',
    uri='https://api.example.com/users',
    requestParameters={
        'integration.request.querystring.user_id': 'method.request.querystring.userId'
    }
)
```

### 3. AWS Service Integration

**Direct integration with AWS services** (no Lambda needed).

```python
# Direct DynamoDB query through API Gateway
apigw.put_integration(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='GET',
    type='AWS',
    integrationHttpMethod='POST',
    uri='arn:aws:apigateway:region:dynamodb:action/GetItem',
    requestTemplates={
        'application/json': json.dumps({
            "TableName": "Users",
            "Key": {
                "userId": {
                    "S": "$input.params('userId')"
                }
            }
        })
    }
)
```

### 4. Mock Integration

**Return static responses** for testing without backend.

```python
apigw.put_integration(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='GET',
    type='MOCK',
    requestTemplates={
        'application/json': '{"statusCode": 200}'
    }
)

# Add method response
apigw.put_method_response(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='GET',
    statusCode='200'
)

# Add integration response with static data
apigw.put_integration_response(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='GET',
    statusCode='200',
    responseTemplates={
        'application/json': json.dumps({
            "statusCode": 200,
            "body": {"message": "Mock response"}
        })
    }
)
```

---

## Request/Response Transformation

### Velocity Template Language (VTL)

API Gateway uses **VTL** (Velocity Template Language) to transform requests and responses.

### Request Mapping

```python
# Transform incoming request
apigw.put_integration(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='POST',
    type='AWS',
    uri='arn:aws:apigateway:region:dynamodb:action/PutItem',
    requestTemplates={
        'application/json': '''
{
    "TableName": "Users",
    "Item": {
        "userId": {"S": "$input.params('userId')"},
        "email": {"S": "$input.json('$.email')"},
        "name": {"S": "$input.json('$.name')"},
        "created": {"N": "$input.path('$.timestamp')"}
    }
}
        '''
    }
)
```

### Response Mapping

```python
apigw.put_integration_response(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='GET',
    statusCode='200',
    responseTemplates={
        'application/json': '''
{
    "statusCode": 200,
    "data": $input.json('$.Item'),
    "timestamp": "$context.requestTimeEpoch"
}
        '''
    }
)
```

### Common VTL Functions

```velocity
# Variables and context
$input.params('paramName')          # Get query/path parameters
$input.json('$.fieldName')          # Get JSON body field
$input.path('$.nested.field')       # Get nested JSON path
$context.requestId                  # Get request ID
$context.requestTimeEpoch           # Timestamp
$context.identity.sourceIp          # Client IP
$context.authorizer.principalId     # Authorized user ID

# Conditional logic
#if($input.params('limit'))
    "limit": $input.params('limit')
#else
    "limit": 10
#end

# Loops
#foreach($item in $input.json('$.items'))
    "$item.id": "$item.name"#if($foreach.hasNext),#end
#end

# String formatting
"message": "$input.params('name') - received"
```

---

## Authorization & Authentication

### 1. API Key Authorization

**Simple key-based access** (not for production auth).

```python
# Create API key
api_key = apigw.create_api_key(
    name='mobile-app-key',
    description='Key for mobile app',
    stageKeys=[
        {
            'stageName': 'prod',
            'restApiId': api_id
        }
    ]
)

# Create usage plan
usage_plan = apigw.create_usage_plan(
    name='Basic Plan',
    description='Basic usage plan',
    apiStages=[
        {
            'apiId': api_id,
            'stage': 'prod'
        }
    ],
    throttle={
        'rateLimit': 1000,      # Requests per second
        'burstLimit': 2000      # Max burst
    },
    quota={
        'limit': 1000000,       # Requests per day
        'period': 'DAY'
    }
)

# Associate key with plan
apigw.create_usage_plan_key(
    usagePlanId=usage_plan['id'],
    keyId=api_key['id'],
    keyType='API_KEY'
)

# Require API key on method
apigw.put_method(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='GET',
    authorizationType='API_KEY',
    apiKeyRequired=True
)
```

**Client Usage:**
```bash
curl -i https://api.example.com/users \
  -H "X-API-Key: YOUR_API_KEY"
```

### 2. AWS IAM Authorization

**Use AWS credentials** for internal service-to-service communication.

```python
# Configure IAM auth on method
apigw.put_method(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='GET',
    authorizationType='AWS_IAM'
)

# Client must sign request with AWS Signature Version 4
from botocore.auth import SigV4Auth
from requests import Request

# Client-side example
request = Request('GET', 'https://api.execute-api.region.amazonaws.com/users')
SigV4Auth(session.get_credentials(), 'execute-api', region).add_auth(request)
```

**Resource Policy for IAM:**
```python
# Allow specific IAM role
resource_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::ACCOUNT:role/LambdaRole"
            },
            "Action": "execute-api:Invoke",
            "Resource": "execute-api:/*"
        }
    ]
}

apigw.update_rest_api(
    restApiId=api_id,
    patchOperations=[
        {
            'op': 'replace',
            'path': '/policy',
            'value': json.dumps(resource_policy)
        }
    ]
)
```

### 3. Lambda Authorizer (Custom Authorizer)

**Custom authorization logic** using Lambda.

```python
# Lambda function that authorizes requests
def lambda_handler(event, context):
    token = event['authorizationToken']  # Extract token from header
    method_arn = event['methodArn']

    # Validate token (JWT, database lookup, etc.)
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        principal_id = decoded['sub']
        is_valid = True
    except:
        is_valid = False

    # Generate policy
    policy = {
        'principalId': principal_id if is_valid else 'user',
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': 'Allow' if is_valid else 'Deny',
                    'Resource': method_arn
                }
            ]
        },
        'context': {
            'userId': decoded.get('sub'),
            'email': decoded.get('email')
        }
    }

    return policy


# Configure Lambda Authorizer on method
apigw.put_authorizer(
    restApiId=api_id,
    name='CustomAuthorizer',
    type='TOKEN',  # or REQUEST
    authorizerUri=f'arn:aws:apigateway:region:lambda:path/2015-03-31/functions/arn:aws:lambda:region:account:function:authorizer-function/invocations',
    authorizerCredentialsArn=f'arn:aws:iam::account:role/APIGatewayLambdaInvokeRole',
    identitySource='method.request.header.Authorization',  # Where to find token
    authorizerResultTtlInSeconds=300  # Cache authorization result
)

# Use authorizer on method
apigw.put_method(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='GET',
    authorizationType='CUSTOM',
    authorizerId=authorizer_id
)
```

### 4. Cognito User Pools

**User management and JWT tokens** via Cognito.

```python
# Create Cognito authorizer
apigw.put_authorizer(
    restApiId=api_id,
    name='CognitoAuthorizer',
    type='COGNITO_USER_POOLS',
    providerARNs=[
        f'arn:aws:cognito-idp:region:account:userpool/region_PoolId'
    ],
    identitySource='method.request.header.Authorization'
)

# Use on method
apigw.put_method(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='GET',
    authorizationType='COGNITO_USER_POOLS',
    authorizerId=authorizer_id
)
```

### 5. OAuth 2.0 / OpenID Connect

**External OAuth providers** (REST APIs only).

```python
apigw.put_authorizer(
    restApiId=api_id,
    name='OAuthAuthorizer',
    type='TOKEN',
    authorizerUri='function_uri',
    identitySource='method.request.header.Authorization'
)
```

---

## CORS Configuration

### Enable CORS on REST API

```python
# On preflight request (OPTIONS)
apigw.put_method(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='OPTIONS',
    authorizationType='NONE'
)

# Mock integration for OPTIONS
apigw.put_integration(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='OPTIONS',
    type='MOCK'
)

# Set CORS headers in response
apigw.put_integration_response(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='OPTIONS',
    statusCode='200',
    responseParameters={
        'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
        'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'",
        'method.response.header.Access-Control-Allow-Origin': "'*'"
    }
)
```

### CORS on HTTP API (Simpler)

```python
apigw.create_api(
    Name='MyAPI',
    ProtocolType='HTTP',
    CorsConfiguration={
        'AllowCredentials': True,
        'AllowHeaders': ['Content-Type', 'Authorization'],
        'AllowMethods': ['GET', 'POST', 'PUT', 'DELETE'],
        'AllowOrigins': ['https://example.com', 'https://app.example.com'],
        'ExposeHeaders': ['x-custom-header', 'x-amzn-RequestId'],
        'MaxAge': 86400
    }
)
```

---

## Caching

### Enable Caching (REST API Only)

```python
# Create cache cluster
apigw.update_stage(
    restApiId=api_id,
    stageName='prod',
    patchOperations=[
        {
            'op': 'replace',
            'path': '/cacheClusterEnabled',
            'value': 'true'
        },
        {
            'op': 'replace',
            'path': '/cacheClusterSize',
            'value': '0.5'  # 0.5, 1.6, 6.1, 13.5, 28.4, 58.2, 118 GB
        }
    ]
)

# Cache settings per method
apigw.put_method_response(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='GET',
    statusCode='200'
)

apigw.put_method_response(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='GET',
    statusCode='200'
)

# Configure cache key
apigw.put_integration_response(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='GET',
    statusCode='200',
    cacheKeyParameters=[
        'method.request.querystring.userId',  # Include userId in cache key
        'method.request.header.Authorization'  # Include auth header
    ],
    responseTemplates={
        'application/json': '$input.json("$")'
    }
)

# Set default cache TTL
apigw.update_stage(
    restApiId=api_id,
    stageName='prod',
    patchOperations=[
        {
            'op': 'replace',
            'path': '/cacheDataEncrypted',
            'value': 'true'
        },
        {
            'op': 'replace',
            'path': '/cacheTtlInSeconds',
            'value': '300'  # 5 minutes
        }
    ]
)

# Method-level cache TTL (override stage default)
apigw.update_integration_response(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='GET',
    statusCode='200',
    patchOperations=[
        {
            'op': 'replace',
            'path': '/cacheDataEncrypted',
            'value': 'true'
        },
        {
            'op': 'replace',
            'path': '/cacheTtlInSeconds',
            'value': '600'  # 10 minutes
        }
    ]
)
```

### Cache Invalidation

```python
# Invalidate cache for specific request
apigw.flush_stage_cache(
    restApiId=api_id,
    stageName='prod'
)
```

### Caching Best Practices

```
GET /users?limit=10              → Cache for 300 seconds
GET /users/123                   → Cache for 3600 seconds (static)
POST /users                      → Do NOT cache (mutations)
DELETE /users/123                → Do NOT cache (mutations)
```

---

## Throttling & Quotas

### Account-Level Throttling

**AWS enforces by default:**
- Rate limit: 10,000 requests/second
- Burst limit: 5,000 concurrent requests

### Usage Plans & Quotas

```python
# Create usage plan with limits
usage_plan = apigw.create_usage_plan(
    name='Premium Plan',
    description='Premium tier',
    throttle={
        'rateLimit': 2000,      # 2000 req/sec per user
        'burstLimit': 5000      # 5000 concurrent
    },
    quota={
        'limit': 10000000,      # 10 million requests
        'period': 'MONTH'       # Reset monthly
    }
)

# Create API key
api_key = apigw.create_api_key(name='premium-key-1')

# Associate key with plan
apigw.create_usage_plan_key(
    usagePlanId=usage_plan['id'],
    keyId=api_key['id'],
    keyType='API_KEY'
)

# Track usage
metrics = apigw.get_usage(
    usagePlanId=usage_plan['id'],
    keyId=api_key['id'],
    startDate='2024-01-01',
    endDate='2024-01-31'
)

print(f"Requests used: {metrics['items']['2024-01-01'][0]}")
```

### Per-Stage Throttling

```python
apigw.update_stage(
    restApiId=api_id,
    stageName='prod',
    patchOperations=[
        {
            'op': 'replace',
            'path': '/*/*/throttle/rateLimit',
            'value': '500'  # Override per method
        },
        {
            'op': 'replace',
            'path': '/*/*/throttle/burstLimit',
            'value': '1000'
        }
    ]
)
```

---

## Monitoring & Logging

### CloudWatch Metrics

```python
import boto3
from datetime import datetime, timedelta

cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')

# Get API metrics
metrics = cloudwatch.get_metric_statistics(
    Namespace='AWS/ApiGateway',
    MetricName='Count',  # or Latency, 4XXError, 5XXError, CacheHitCount, CacheMissCount
    Dimensions=[
        {'Name': 'ApiName', 'Value': 'MyUserAPI'},
        {'Name': 'Stage', 'Value': 'prod'}
    ],
    StartTime=datetime.utcnow() - timedelta(hours=1),
    EndTime=datetime.utcnow(),
    Period=300  # 5-minute intervals
)

for point in metrics['Datapoints']:
    print(f"{point['Timestamp']}: {point['Sum']} requests")
```

### Full Request/Response Logging

```python
# Enable detailed logging (requires IAM role)
apigw.update_stage(
    restApiId=api_id,
    stageName='prod',
    patchOperations=[
        {
            'op': 'replace',
            'path': '/*/*/*/logging/full-request-response-logging',
            'value': 'true'
        },
        {
            'op': 'replace',
            'path': '/accessLogSetting/destinationArn',
            'value': 'arn:aws:logs:region:account:log-group:api-logs'
        },
        {
            'op': 'replace',
            'path': '/methodSettings/~1{proxy+}/*/logging/loglevel',
            'value': 'INFO'  # or ERROR
        }
    ]
)
```

### X-Ray Tracing

```python
# Enable X-Ray
apigw.update_stage(
    restApiId=api_id,
    stageName='prod',
    patchOperations=[
        {
            'op': 'replace',
            'path': '/tracingEnabled',
            'value': 'true'
        }
    ]
)

# View traces
xray = boto3.client('xray', region_name='us-east-1')
traces = xray.get_trace_summaries(
    StartTime=datetime.utcnow() - timedelta(minutes=10),
    EndTime=datetime.utcnow()
)
```

### Access Logs Format

```json
{
  "$context.requestId"
  "$context.identity.sourceIp"
  "$context.requestTime"
  "$context.routeKey"
  "$context.status"
  "$context.error.messageString"
  "$context.integration.latency"
  "$context.identity.userAgent"
  "$context.requestTimeEpoch"
}
```

---

## Stages & Versioning

### Understanding Stages

Stages are **independent deployments** of the same API with different configurations, backend endpoints, and settings.

```
API Gateway API
    ├── dev stage
    │   ├── Backend: dev-lambda-function
    │   ├── Endpoint: https://api.example.com/dev/users
    │   └── Cache: Disabled
    ├── staging stage
    │   ├── Backend: staging-lambda-function
    │   ├── Endpoint: https://api.example.com/staging/users
    │   └── Cache: 5 min TTL
    └── prod stage
        ├── Backend: prod-lambda-function
        ├── Endpoint: https://api.example.com/prod/users
        └── Cache: 1 hour TTL
```

### Create & Deploy to Stages

```python
# Create deployment (snapshot of API)
deployment = apigw.create_deployment(
    restApiId=api_id,
    stageName='dev',
    description='Initial dev deployment',
    cacheClusterEnabled=False
)

# Create prod stage
prod_stage = apigw.create_stage(
    restApiId=api_id,
    stageName='prod',
    deploymentId=deployment['id'],
    description='Production stage',
    cacheClusterEnabled=True,
    cacheClusterSize='0.5',
    loggingLevel='INFO'
)

# Update stage variables
apigw.update_stage(
    restApiId=api_id,
    stageName='prod',
    patchOperations=[
        {
            'op': 'replace',
            'path': '/variables/lambda_function_name',
            'value': 'user-api-prod'
        },
        {
            'op': 'replace',
            'path': '/variables/db_host',
            'value': 'prod-db.example.com'
        }
    ]
)

# Access stage variables in Lambda
def lambda_handler(event, context):
    stage_variables = event.get('stageVariables', {})
    function_name = stage_variables.get('lambda_function_name')
    db_host = stage_variables.get('db_host')
```

### API Versioning Strategies

**Strategy 1: URL Path Versioning**
```
GET /v1/users
GET /v2/users
GET /v3/users
```

**Strategy 2: Stage-Based Versioning**
```
GET https://api.example.com/v1/users
GET https://api.example.com/v2/users
```

**Strategy 3: Request Header Versioning**
```
GET /users
  Header: API-Version: 2
```

---

## Custom Domains

### Set Up Custom Domain

```python
# Create certificate in ACM first (or import existing)
acm = boto3.client('acm', region_name='us-east-1')

# Create domain name mapping
domain_name = apigw.create_domain_name(
    domainName='api.example.com',
    certificateArn='arn:aws:acm:region:account:certificate/id',
    endpointConfiguration={'types': ['REGIONAL']},  # or EDGE
    securityPolicy='TLS_1_2'  # or TLS_1_0
)

# Map domain to stage
apigw.create_base_path_mapping(
    domainName='api.example.com',
    restApiId=api_id,
    basePath='myapp',  # Optional: https://api.example.com/myapp/users
    stage='prod'
)

# Update DNS CNAME record:
# CNAME api.example.com -> d1234.execute-api.region.amazonaws.com
```

---

## Advanced Patterns

### 1. Canary Deployments

```python
# Route percentage of traffic to canary stage
apigw.update_stage(
    restApiId=api_id,
    stageName='prod',
    patchOperations=[
        {
            'op': 'replace',
            'path': '/canarySettings/traceEnabled',
            'value': 'true'
        },
        {
            'op': 'replace',
            'path': '/canarySettings/useStageCache',
            'value': 'false'  # Use canary cache, not stage cache
        },
        {
            'op': 'replace',
            'path': '/canarySettings/percentTraffic',
            'value': '5'  # Send 5% to canary
        }
    ]
)
```

### 2. Request Validation

```python
# Create request model
apigw.create_model(
    restApiId=api_id,
    name='UserModel',
    contentType='application/json',
    schema=json.dumps({
        "type": "object",
        "properties": {
            "email": {"type": "string", "format": "email"},
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0}
        },
        "required": ["email", "name"]
    })
)

# Create validator
validator = apigw.create_request_validator(
    restApiId=api_id,
    name='BodyValidator',
    validateRequestBody=True,
    validateRequestParameters=False
)

# Apply to method
apigw.put_method(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='POST',
    authorizationType='NONE',
    requestValidatorId=validator['id'],
    requestModels={'application/json': 'UserModel'}
)
```

### 3. Request Throttling by User

```python
# In Lambda authorizer, return user context
def lambda_handler(event, context):
    token = event['authorizationToken']
    decoded = jwt.decode(token, SECRET_KEY)

    return {
        'principalId': decoded['sub'],
        'policyDocument': {...},
        'context': {
            'userId': decoded['sub'],
            'tier': decoded.get('tier', 'free')  # free, premium, enterprise
        }
    }

# Usage plan for each tier
free_plan = apigw.create_usage_plan(
    name='Free Tier',
    throttle={'rateLimit': 100, 'burstLimit': 500},
    quota={'limit': 10000, 'period': 'MONTH'}
)

premium_plan = apigw.create_usage_plan(
    name='Premium Tier',
    throttle={'rateLimit': 5000, 'burstLimit': 10000},
    quota={'limit': 1000000, 'period': 'MONTH'}
)
```

### 4. Request/Response Caching by User

```velocity
## Cache key includes user ID
#set($userId = $context.authorizer.userId)
cache-${userId}-${method.request.querystring.filter}
```

### 5. API Documentation (OpenAPI/Swagger)

```python
# Export API as OpenAPI specification
spec = apigw.get_export(
    restApiId=api_id,
    stageName='prod',
    exportType='oas30',  # or swagger2
    accepts='application/json'
)

# Import and update from OpenAPI spec
apigw.import_rest_api(
    name='ImportedAPI',
    body=open('openapi.yaml').read(),
    mode='overwrite'
)
```

---

## Best Practices & Security

### 1. API Security Checklist

```python
# ✓ Enable CloudTrail for audit
cloudtrail = boto3.client('cloudtrail')
cloudtrail.create_trail(
    Name='api-gateway-trail',
    S3BucketName='audit-logs-bucket',
    IncludeGlobalServiceEvents=True,
    IsMultiRegionTrail=True
)

# ✓ Use AWS WAF to block malicious traffic
waf = boto3.client('wafv2')
web_acl = waf.create_web_acl(
    Name='api-gateway-waf',
    Scope='REGIONAL',  # for regional APIs
    DefaultAction={'Allow': {}},
    Rules=[
        {
            'Name': 'RateLimitRule',
            'Priority': 0,
            'Action': {'Block': {}},
            'Statement': {
                'RateBasedStatement': {
                    'Limit': 2000,
                    'AggregateKeyType': 'IP'
                }
            },
            'VisibilityConfig': {
                'SampledRequestsEnabled': True,
                'CloudWatchMetricsEnabled': True,
                'MetricName': 'RateLimitRule'
            }
        }
    ],
    VisibilityConfig={
        'SampledRequestsEnabled': True,
        'CloudWatchMetricsEnabled': True,
        'MetricName': 'api-gateway-waf'
    }
)

# ✓ Enforce encryption
apigw.update_stage(
    restApiId=api_id,
    stageName='prod',
    patchOperations=[
        {
            'op': 'replace',
            'path': '/methodSettings/~1{proxy+}/*/dataTraceEnabled',
            'value': 'false'  # Don't log request/response data
        },
        {
            'op': 'replace',
            'path': '/cacheDataEncrypted',
            'value': 'true'
        }
    ]
)

# ✓ Enable VPC endpoint for private access
ec2 = boto3.client('ec2')
vpc_endpoint = ec2.create_vpc_endpoint(
    VpcEndpointType='Interface',
    ServiceName=f'com.amazonaws.region.execute-api',
    VpcId='vpc-xxxxx',
    SubnetIds=['subnet-xxxxx'],
    SecurityGroupIds=['sg-xxxxx']
)
```

### 2. Error Handling

```python
# Create error response in Lambda
def lambda_handler(event, context):
    try:
        # Process request
        user_id = event['pathParameters']['userId']
        user = get_user(user_id)

        return {
            'statusCode': 200,
            'body': json.dumps(user)
        }

    except ValueError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'InvalidRequest',
                'message': str(e),
                'requestId': context.request_id
            })
        }

    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'InternalServerError',
                'requestId': context.request_id
            })
        }
```

### 3. Request Validation

```python
# Validate input before processing
def lambda_handler(event, context):
    body = json.loads(event['body'])

    # Validate required fields
    required = ['email', 'name']
    if not all(field in body for field in required):
        return error_response(400, "Missing required fields")

    # Validate email format
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', body['email']):
        return error_response(400, "Invalid email format")

    # Validate string length
    if len(body['name']) > 100:
        return error_response(400, "Name too long")

    # Proceed with processing
    return success_response(create_user(body))
```

### 4. Performance Optimization

```python
# ✓ Use HTTP APIs (not REST) for better performance
# ✓ Enable caching for read-heavy operations
# ✓ Use Lambda Layers for shared code
# ✓ Configure appropriate memory/concurrency
# ✓ Use Lambda provisioned concurrency for predictable latency
# ✓ Batch DynamoDB operations
# ✓ Use CloudFront in front of API for static responses
```

### 5. Cost Optimization

```
| Component | Cost Strategy |
|-----------|---------------|
| API Calls | Use HTTP API (~$0.90 vs $3.50 per 1M REST calls) |
| Caching | Enable for frequently accessed data |
| Stages | Use fewer stages (dev/staging/prod only) |
| Custom Domain | One domain per API (reuse across stages) |
| Logs | Use sampling, not full logging |
| Data Transfer | CloudFront + S3 for large payloads |
| DynamoDB | Use direct integrations instead of Lambda + calls |
```

### 6. Monitoring & Alerting

```python
# Create CloudWatch alarm for errors
cloudwatch = boto3.client('cloudwatch')
cloudwatch.put_metric_alarm(
    AlarmName='API-5XX-Errors',
    MetricName='5XXError',
    Namespace='AWS/ApiGateway',
    Statistic='Sum',
    Period=300,
    EvaluationPeriods=1,
    Threshold=5,
    ComparisonOperator='GreaterThanThreshold',
    Dimensions=[
        {'Name': 'ApiName', 'Value': 'MyUserAPI'},
        {'Name': 'Stage', 'Value': 'prod'}
    ],
    AlarmActions=['arn:aws:sns:region:account:topic/alerts']
)
```

---

## Key Takeaways for Developers

| Concept | Remember |
|---------|----------|
| **API Type** | Use HTTP API for new builds (faster, cheaper). REST API for complex features. |
| **Integration** | Lambda Proxy is simpler; use for most cases. Non-proxy for complex transformations. |
| **Authorization** | Use IAM internally. Lambda Authorizer for custom logic. Cognito for user sign-ups. API Key for simple quotas. |
| **Caching** | Cache GET requests only. Include user ID in cache key for multi-user APIs. |
| **Throttling** | Control costs with usage plans. Monitor with CloudWatch. Educate users about limits. |
| **Stages** | dev, staging, prod. Stage variables > stage switching. |
| **Logging** | Enable X-Ray for tracing. CloudWatch for metrics. CloudTrail for compliance. |
| **Security** | Use WAF. Enable encryption. Validate input. Least privilege IAM roles. |

