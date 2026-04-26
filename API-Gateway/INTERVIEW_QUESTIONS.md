# API Gateway Interview Questions

## 1. Fundamental Questions

### Basic Concepts
1. **What is API Gateway and its main features?**
   - Fully managed service for creating REST/HTTP/WebSocket APIs
   - Handles authentication, rate limiting, caching, request/response transformation
   - Integrates with Lambda, EC2, DynamoDB, other AWS services
   - Automatically scales
   - Pay per API call (cheap)

2. **Explain API Gateway API types.**
   - **REST API**: Resource-based, traditional HTTP methods
   - **HTTP API**: Simpler, cheaper, less features than REST
   - **WebSocket API**: Bidirectional communication
   - Choose: REST for complex APIs, HTTP for simple/microservices

3. **What are API stages and deployments?**
   - Stage: Environment (dev, staging, prod)
   - Deployment: Snapshot of API at a point in time
   - Each stage has own settings: throttling, caching, variables
   - Test stage without affecting users

4. **Explain request/response transformation in API Gateway.**
   - Mapping templates: Transform JSON/XML
   - Request: Modify incoming request to backend
   - Response: Modify backend response before client
   - Use case: Convert REST to SOAP, add headers, filter data

5. **What are API keys and usage plans?**
   - API Key: Identifier for tracking API usage per client
   - Usage Plan: Rate limits and quotas (e.g., 100 req/sec, 1M req/month)
   - Throttling: API-level and stage-level
   - Use case: Monitor client usage, enforce fair usage

---

## 2. Intermediate Scenarios

### Security & Authorization

6. **Scenario: Secure API accessible only to authenticated users. Design.**
   - Answer options:
     1. **API Key**: Simple, not for sensitive (passed in header)
     2. **IAM**: AWS services, cross-account access
     3. **Cognito User Pools**: User authentication, easiest for web apps
     4. **Lambda Authorizer**: Custom logic (LDAP, database lookup)
     5. **OAuth 2.0 / OpenID Connect**: Third-party federation
   - Best practice: Cognito for web apps, IAM for AWS services, Lambda for custom

7. **Scenario: API needs to call another service with rate limiting. Solution?**
   - Implementation:
     1. API Gateway throttle: 1000 requests/second
     2. Backend Lambda: Handles actual requests
     3. SQS queue: Buffer requests if backend slow
     4. DynamoDB: Rate limiter table (token bucket algorithm)
   - Prevent overwhelming downstream service while handling spikes

### Caching & Performance

8. **How do you cache API responses to reduce backend load?**
   - Enable caching per method (GET with no params is cacheable)
   - Cache key: Query parameters, headers, path
   - TTL: Default 300 seconds
   - Size: 0.5 GB - 237 GB depending on stage
   - Invalid cache: Method, stage variable changes
   - Use case: Status, pricing, reference data (infrequently changed)

9. **Scenario: API response time is 500ms, target is 50ms. Optimize.**
   - Caching:
     - Add CloudFront in front of API Gateway
     - Cache GET requests (3600 seconds)
     - Invalidate on data change
   - API optimization:
     - Reduce mapping templates complexity
     - Use Lambda Provisioned Concurrency
     - Add DynamoDB caching (ElastiCache)
     - Optimize database queries
   - Monitoring: API Gateway metrics for latency

---

## 3. Advanced Scenarios

### Integration Patterns

10. **Design API for heavy computation (image processing).**
    - Pattern:
      1. POST /process-image: API returns 202 Accepted
      2. Request ID returned to client
      3. Lambda: Async processing with SQS
      4. GET /status/{request-id}: Check processing status
      5. Notification: SNS email when complete
    - Benefits: API returns quickly, user polls for result

11. **Implement API versioning strategy.**
    - Approaches:
      1. **URL path**: /v1/users, /v2/users
      2. **Query parameter**: /users?version=2
      3. **Header**: Accept-Version: v2
      4. **Subdomain**: v2.api.example.com
    - Best practice: URL path (easiest to test, clear in logs)
    - Migration: Keep old version running, guide to new

12. **Design API with multiple backends (canary deployment).**
    - 90% traffic → Primary backend
    - 10% traffic → New version
    - Monitor: Error rate, latency
    - If acceptable: Gradually shift traffic
    - Rollback: If issues detected
    - Implementation: ALB weight, Lambda aliases, API Gateway integration

---

## 4. Real-World Scenarios

13. **Scenario: API suddenly returns 500 errors. Troubleshoot.**
    - Check:
      1. API Gateway logs (CloudWatch)
      2. Backend integration (Lambda CloudWatch logs)
      3. Database connectivity
      4. Downstream service issues
      5. Rate limiting (if hitting quota)
    - Monitoring: CloudWatch dashboard for errors/latency
    - Alarms: Alert on error rate > 1%

14. **Implement API rate limiting per user (not just API-level).**
    - CloudWatch Insights query to identify heavy users
    - Lambda Authorizer: Check user rate limit (DynamoDB counter)
    - Return 429 Too Many Requests if exceeded
    - Reset counter periodically (per minute/hour)
    - Alternative: API Usage Plans (AWS-managed)

15. **Design GraphQL API with API Gateway.**
    - Challenge: GraphQL is POST-only, complex query patterns
    - Solution:
      1. API Gateway: Single POST /graphql endpoint
      2. Lambda: GraphQL resolver (Apollo Server, Strawberry)
      3. DataLoader: Batch database queries (N+1 prevention)
      4. Caching: Per-field caching or query result caching
    - Benefits: Precise data fetching, reduce over-fetching

---

## 5. Best Practices

16. **API Gateway best practices:**
    - Use HTTP API for simple endpoints (cheaper)
    - REST API for complex transformations
    - Enable logging (CloudWatch)
    - Set appropriate throttling limits
    - Use CloudFront for caching
    - Implement comprehensive error handling
    - API versioning strategy
    - Monitoring: Metrics, alarms, dashboards
    - Documentation: OpenAPI/Swagger specification
    - Security: Never log sensitive data

---

## 6. Hands-On Examples

17. **Create REST API with Lambda integration:**
    ```python
    # Lambda function
    def lambda_handler(event, context):
        http_method = event['httpMethod']
        path = event['path']
        body = json.loads(event.get('body', '{}'))

        if http_method == 'GET' and path == '/users':
            return {
                'statusCode': 200,
                'body': json.dumps([{'id': 1, 'name': 'Alice'}])
            }
        elif http_method == 'POST' and path == '/users':
            # Create user
            return {
                'statusCode': 201,
                'body': json.dumps({'id': 2, 'name': body.get('name')})
            }
        else:
            return {'statusCode': 404}
    ```

18. **API Gateway request mapping template:**
    ```vtl
    {
      "userid": "$input.params('user-id')",
      "name": "$input.path('$.name')",
      "timestamp": "$context.requestTime"
    }
    ```

19. **Response mapping template (filter response):**
    ```vtl
    {
      "id": $input.path('$.user_id'),
      "name": $input.path('$.username'),
      #if($input.path('$.email') != "")
      "email": $input.path('$.email')
      #end
    }
    ```

---

## Tips for Interview Success

- **Understand integration types**: Lambda, HTTP, AWS service
- **Security**: Know all authorization options
- **Performance**: Caching, CloudFront, Lambda optimization
- **API versioning**: Important for long-lived APIs
- **Monitoring**: CloudWatch is essential
- **Error handling**: Proper HTTP status codes
- **Rate limiting**: Prevent abuse, fair usage

