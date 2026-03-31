"""
AWS API Gateway Operations - boto3 Python Examples
Comprehensive examples for managing API Gateway resources
"""

import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Initialize clients
apigw = boto3.client('apigateway', region_name='us-east-1')
apigw_v2 = boto3.client('apigatewayv2', region_name='us-east-1')  # For HTTP APIs
cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')
iam = boto3.client('iam', region_name='us-east-1')


# ============================================================================
# REST API OPERATIONS
# ============================================================================

class RestAPIOperations:
    """REST API management"""

    @staticmethod
    def create_rest_api(
        name: str,
        description: str = '',
        endpoint_type: str = 'REGIONAL'
    ) -> str:
        """Create a new REST API"""
        response = apigw.create_rest_api(
            name=name,
            description=description,
            endpointConfiguration={'types': [endpoint_type]}
        )
        return response['id']

    @staticmethod
    def list_rest_apis() -> List[Dict[str, Any]]:
        """List all REST APIs"""
        response = apigw.get_rest_apis(limit=500)
        return response['items']

    @staticmethod
    def get_rest_api(api_id: str) -> Dict[str, Any]:
        """Get REST API details"""
        return apigw.get_rest_api(restApiId=api_id)

    @staticmethod
    def delete_rest_api(api_id: str) -> None:
        """Delete a REST API"""
        apigw.delete_rest_api(restApiId=api_id)
        print(f"Deleted API: {api_id}")

    @staticmethod
    def update_rest_api(
        api_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update REST API properties"""
        patches = []
        if name:
            patches.append({'op': 'replace', 'path': '/name', 'value': name})
        if description:
            patches.append({'op': 'replace', 'path': '/description', 'value': description})

        return apigw.update_rest_api(
            restApiId=api_id,
            patchOperations=patches
        )

    @staticmethod
    def set_api_policy(api_id: str, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Set resource-based policy on API"""
        return apigw.update_rest_api(
            restApiId=api_id,
            patchOperations=[
                {
                    'op': 'replace',
                    'path': '/policy',
                    'value': json.dumps(policy)
                }
            ]
        )


# ============================================================================
# RESOURCES & METHODS
# ============================================================================

class ResourceOperations:
    """Resource and method management"""

    @staticmethod
    def get_resources(api_id: str) -> List[Dict[str, Any]]:
        """Get all resources in an API"""
        resources = []
        paginator = apigw.get_paginator('get_resources')
        for page in paginator.paginate(restApiId=api_id):
            resources.extend(page['items'])
        return resources

    @staticmethod
    def get_root_resource(api_id: str) -> str:
        """Get root resource ID"""
        resources = apigw.get_resources(restApiId=api_id)
        root = [r for r in resources['items'] if r['path'] == '/'][0]
        return root['id']

    @staticmethod
    def create_resource(
        api_id: str,
        parent_id: str,
        path_part: str
    ) -> str:
        """Create a new resource"""
        response = apigw.create_resource(
            restApiId=api_id,
            parentId=parent_id,
            pathPart=path_part
        )
        return response['id']

    @staticmethod
    def create_resource_tree(
        api_id: str,
        path: str
    ) -> str:
        """Create nested resource path (e.g., /users/{userId}/posts)"""
        parts = [p for p in path.split('/') if p]
        parent_id = ResourceOperations.get_root_resource(api_id)

        for part in parts:
            resources = apigw.get_resources(restApiId=api_id)
            existing = [
                r for r in resources['items']
                if r.get('parentId') == parent_id and r.get('pathPart') == part
            ]

            if existing:
                parent_id = existing[0]['id']
            else:
                parent_id = ResourceOperations.create_resource(api_id, parent_id, part)

        return parent_id

    @staticmethod
    def delete_resource(api_id: str, resource_id: str) -> None:
        """Delete a resource"""
        apigw.delete_resource(restApiId=api_id, resourceId=resource_id)

    @staticmethod
    def create_method(
        api_id: str,
        resource_id: str,
        http_method: str,
        auth_type: str = 'NONE',
        api_key_required: bool = False,
        request_parameters: Optional[Dict[str, bool]] = None
    ) -> None:
        """Create a method on a resource"""
        params = {
            'restApiId': api_id,
            'resourceId': resource_id,
            'httpMethod': http_method,
            'authorizationType': auth_type,
            'apiKeyRequired': api_key_required
        }

        if request_parameters:
            params['requestParameters'] = request_parameters

        apigw.put_method(**params)
        print(f"Created {http_method} method on resource {resource_id}")

    @staticmethod
    def delete_method(api_id: str, resource_id: str, http_method: str) -> None:
        """Delete a method"""
        apigw.delete_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method
        )


# ============================================================================
# INTEGRATIONS
# ============================================================================

class IntegrationOperations:
    """Integration management"""

    @staticmethod
    def create_lambda_integration(
        api_id: str,
        resource_id: str,
        http_method: str,
        lambda_arn: str,
        use_proxy: bool = True
    ) -> None:
        """Create Lambda integration"""
        integration_type = 'AWS_PROXY' if use_proxy else 'AWS'

        apigw.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            type=integration_type,
            integrationHttpMethod='POST',
            uri=f'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
        )

        # For non-proxy, add method response
        if not use_proxy:
            apigw.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                statusCode='200'
            )
            apigw.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                statusCode='200',
                responseTemplates={'application/json': '$input.json("$")'}
            )

    @staticmethod
    def create_http_integration(
        api_id: str,
        resource_id: str,
        http_method: str,
        backend_url: str,
        backend_method: str = 'GET'
    ) -> None:
        """Create HTTP proxy integration"""
        apigw.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            type='HTTP_PROXY',
            integrationHttpMethod=backend_method,
            uri=backend_url
        )

    @staticmethod
    def create_mock_integration(
        api_id: str,
        resource_id: str,
        http_method: str,
        response_data: Dict[str, Any]
    ) -> None:
        """Create mock integration with static response"""
        apigw.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            type='MOCK',
            requestTemplates={'application/json': '{"statusCode": 200}'}
        )

        apigw.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            statusCode='200'
        )

        apigw.put_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            statusCode='200',
            responseTemplates={'application/json': json.dumps(response_data)}
        )

    @staticmethod
    def create_dynamodb_integration(
        api_id: str,
        resource_id: str,
        http_method: str,
        table_name: str,
        action: str = 'GetItem'
    ) -> None:
        """Create direct DynamoDB integration"""
        # Create IAM role for API Gateway to assume
        role_arn = 'arn:aws:iam::ACCOUNT:role/APIGatewayDynamoDBRole'

        request_template = {
            'GetItem': json.dumps({
                "TableName": table_name,
                "Key": {
                    "id": {"S": "$input.params('id')"}
                }
            }),
            'Query': json.dumps({
                "TableName": table_name,
                "KeyConditionExpression": "id = :id",
                "ExpressionAttributeValues": {":id": {"S": "$input.params('id')"}}
            }),
            'Scan': json.dumps({
                "TableName": table_name
            })
        }

        apigw.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            type='AWS',
            integrationHttpMethod='POST',
            uri=f'arn:aws:apigateway:us-east-1:dynamodb:action/{action}',
            credentials=role_arn,
            requestTemplates={'application/json': request_template.get(action, '')}
        )

        apigw.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            statusCode='200'
        )

        apigw.put_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            statusCode='200',
            responseTemplates={'application/json': '$input.json("$")'}
        )


# ============================================================================
# AUTHORIZATION & AUTHENTICATION
# ============================================================================

class AuthorizationOperations:
    """Authorization and authentication management"""

    @staticmethod
    def create_api_key(
        name: str,
        description: str = '',
        enabled: bool = True
    ) -> str:
        """Create an API key"""
        response = apigw.create_api_key(
            name=name,
            description=description,
            enabled=enabled
        )
        return response['id']

    @staticmethod
    def get_api_key(key_id: str) -> Dict[str, Any]:
        """Get API key details"""
        return apigw.get_api_key(apiKey=key_id)

    @staticmethod
    def list_api_keys() -> List[Dict[str, Any]]:
        """List all API keys"""
        response = apigw.get_api_keys(limit=500)
        return response['items']

    @staticmethod
    def disable_api_key(key_id: str) -> None:
        """Disable an API key"""
        apigw.update_api_key(
            apiKey=key_id,
            patchOperations=[{'op': 'replace', 'path': '/enabled', 'value': 'false'}]
        )

    @staticmethod
    def create_usage_plan(
        name: str,
        api_id: str,
        stage_name: str,
        rate_limit: int = 1000,
        burst_limit: int = 2000,
        quota_limit: Optional[int] = None,
        quota_period: str = 'DAY'
    ) -> str:
        """Create usage plan with throttling and quota"""
        plan_config = {
            'name': name,
            'apiStages': [{'apiId': api_id, 'stage': stage_name}],
            'throttle': {
                'rateLimit': rate_limit,
                'burstLimit': burst_limit
            }
        }

        if quota_limit:
            plan_config['quota'] = {
                'limit': quota_limit,
                'period': quota_period
            }

        response = apigw.create_usage_plan(**plan_config)
        return response['id']

    @staticmethod
    def associate_api_key_to_usage_plan(
        usage_plan_id: str,
        api_key_id: str
    ) -> None:
        """Associate API key with usage plan"""
        apigw.create_usage_plan_key(
            usagePlanId=usage_plan_id,
            keyId=api_key_id,
            keyType='API_KEY'
        )
        print(f"Associated API key {api_key_id} to usage plan {usage_plan_id}")

    @staticmethod
    def create_lambda_authorizer(
        api_id: str,
        name: str,
        lambda_arn: str,
        identity_source: str = 'method.request.header.Authorization',
        auth_type: str = 'TOKEN'
    ) -> str:
        """Create Lambda authorizer"""
        response = apigw.put_authorizer(
            restApiId=api_id,
            name=name,
            type=auth_type,
            authorizerUri=lambda_arn,
            identitySource=identity_source,
            authorizerResultTtlInSeconds=300
        )
        return response['id']

    @staticmethod
    def create_cognito_authorizer(
        api_id: str,
        name: str,
        cognito_user_pool_arn: str,
        identity_source: str = 'method.request.header.Authorization'
    ) -> str:
        """Create Cognito user pool authorizer"""
        response = apigw.put_authorizer(
            restApiId=api_id,
            name=name,
            type='COGNITO_USER_POOLS',
            providerARNs=[cognito_user_pool_arn],
            identitySource=identity_source
        )
        return response['id']

    @staticmethod
    def attach_authorizer_to_method(
        api_id: str,
        resource_id: str,
        http_method: str,
        authorizer_id: str
    ) -> None:
        """Attach authorizer to a method"""
        apigw.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            authorizationType='CUSTOM',
            authorizerId=authorizer_id
        )


# ============================================================================
# REQUEST/RESPONSE TRANSFORMATION
# ============================================================================

class TransformationOperations:
    """Request and response mapping"""

    @staticmethod
    def create_request_model(
        api_id: str,
        model_name: str,
        schema: Dict[str, Any]
    ) -> str:
        """Create request model/schema"""
        response = apigw.create_model(
            restApiId=api_id,
            name=model_name,
            contentType='application/json',
            schema=json.dumps(schema)
        )
        return response['id']

    @staticmethod
    def create_request_validator(
        api_id: str,
        name: str,
        validate_body: bool = True,
        validate_parameters: bool = False
    ) -> str:
        """Create request validator"""
        response = apigw.create_request_validator(
            restApiId=api_id,
            name=name,
            validateRequestBody=validate_body,
            validateRequestParameters=validate_parameters
        )
        return response['id']

    @staticmethod
    def create_user_model_example():
        """Example: User request model schema"""
        return {
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email"},
                "name": {"type": "string", "minLength": 1, "maxLength": 100},
                "age": {"type": "integer", "minimum": 0, "maximum": 150}
            },
            "required": ["email", "name"]
        }

    @staticmethod
    def create_request_mapping_template_example():
        """Example: VTL request mapping template"""
        return '''
{
    "TableName": "Users",
    "Item": {
        "userId": {"S": "$input.params('userId')"},
        "email": {"S": "$input.json('$.email')"},
        "name": {"S": "$input.json('$.name')"},
        "age": {"N": "$input.json('$.age')"},
        "created": {"N": "$context.requestTimeEpoch"}
    }
}
        '''

    @staticmethod
    def create_response_mapping_template_example():
        """Example: VTL response mapping template"""
        return '''
#set($inputRoot = $input.path('$'))
{
    "statusCode": 200,
    "data": {
        #foreach($item in $inputRoot.Items)
            "$item.id.S": {
                "name": "$item.name.S",
                "email": "$item.email.S"
            }#if($foreach.hasNext),#end
        #end
    },
    "requestId": "$context.requestId",
    "timestamp": "$context.requestTimeEpoch"
}
        '''


# ============================================================================
# CORS CONFIGURATION
# ============================================================================

class CORSOperations:
    """CORS management"""

    @staticmethod
    def enable_cors_on_rest_api(
        api_id: str,
        resource_id: str,
        allowed_origins: List[str] = ['*'],
        allowed_methods: List[str] = None,
        allowed_headers: List[str] = None
    ) -> None:
        """Enable CORS on resource (REST API)"""
        if not allowed_methods:
            allowed_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']
        if not allowed_headers:
            allowed_headers = ['Content-Type', 'Authorization', 'X-Amz-Date', 'X-Api-Key']

        # Create OPTIONS method
        apigw.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            authorizationType='NONE'
        )

        # Mock integration
        apigw.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            type='MOCK'
        )

        # Method response
        apigw.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': False,
                'method.response.header.Access-Control-Allow-Methods': False,
                'method.response.header.Access-Control-Allow-Origin': False
            }
        )

        # Integration response
        apigw.put_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': f"'{','.join(allowed_headers)}'",
                'method.response.header.Access-Control-Allow-Methods': f"'{','.join(allowed_methods)}'",
                'method.response.header.Access-Control-Allow-Origin': f"'{','.join(allowed_origins)}'"
            }
        )

        print(f"CORS enabled on resource {resource_id}")


# ============================================================================
# CACHING
# ============================================================================

class CachingOperations:
    """Caching management"""

    @staticmethod
    def enable_cache_on_stage(
        api_id: str,
        stage_name: str,
        cache_size: str = '0.5',
        ttl_seconds: int = 300,
        encrypted: bool = True
    ) -> None:
        """Enable caching on stage"""
        apigw.update_stage(
            restApiId=api_id,
            stageName=stage_name,
            patchOperations=[
                {
                    'op': 'replace',
                    'path': '/cacheClusterEnabled',
                    'value': 'true'
                },
                {
                    'op': 'replace',
                    'path': '/cacheClusterSize',
                    'value': cache_size  # 0.5, 1.6, 6.1, 13.5, 28.4, 58.2, 118
                },
                {
                    'op': 'replace',
                    'path': '/cacheTtlInSeconds',
                    'value': str(ttl_seconds)
                },
                {
                    'op': 'replace',
                    'path': '/cacheDataEncrypted',
                    'value': 'true' if encrypted else 'false'
                }
            ]
        )
        print(f"Cache enabled on stage {stage_name}")

    @staticmethod
    def set_integration_cache_parameters(
        api_id: str,
        resource_id: str,
        http_method: str,
        cache_key_parameters: List[str],
        ttl_seconds: int = 300
    ) -> None:
        """Set cache key parameters for method"""
        apigw.put_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            statusCode='200',
            cacheKeyParameters=cache_key_parameters
        )

    @staticmethod
    def flush_stage_cache(api_id: str, stage_name: str) -> None:
        """Invalidate cache for entire stage"""
        apigw.flush_stage_cache(restApiId=api_id, stageName=stage_name)
        print(f"Cache flushed for stage {stage_name}")


# ============================================================================
# DEPLOYMENTS & STAGES
# ============================================================================

class DeploymentOperations:
    """Deployment and stage management"""

    @staticmethod
    def create_deployment(
        api_id: str,
        stage_name: str,
        description: str = ''
    ) -> str:
        """Create deployment and stage"""
        response = apigw.create_deployment(
            restApiId=api_id,
            stageName=stage_name,
            description=description
        )
        return response['id']

    @staticmethod
    def create_stage(
        api_id: str,
        stage_name: str,
        deployment_id: str,
        description: str = '',
        cache_enabled: bool = False
    ) -> None:
        """Create new stage from deployment"""
        apigw.create_stage(
            restApiId=api_id,
            stageName=stage_name,
            deploymentId=deployment_id,
            description=description,
            cacheClusterEnabled=cache_enabled
        )
        print(f"Stage {stage_name} created")

    @staticmethod
    def set_stage_variables(
        api_id: str,
        stage_name: str,
        variables: Dict[str, str]
    ) -> None:
        """Set stage variables"""
        patches = [
            {'op': 'replace', 'path': f'/variables/{key}', 'value': value}
            for key, value in variables.items()
        ]

        apigw.update_stage(
            restApiId=api_id,
            stageName=stage_name,
            patchOperations=patches
        )

    @staticmethod
    def get_stage(api_id: str, stage_name: str) -> Dict[str, Any]:
        """Get stage details"""
        return apigw.get_stage(restApiId=api_id, stageName=stage_name)

    @staticmethod
    def list_stages(api_id: str) -> List[Dict[str, Any]]:
        """List all stages"""
        response = apigw.get_stages(restApiId=api_id)
        return response['item']

    @staticmethod
    def delete_stage(api_id: str, stage_name: str) -> None:
        """Delete a stage"""
        apigw.delete_stage(restApiId=api_id, stageName=stage_name)
        print(f"Stage {stage_name} deleted")


# ============================================================================
# MONITORING & LOGGING
# ============================================================================

class MonitoringOperations:
    """Monitoring and logging"""

    @staticmethod
    def enable_logging_on_stage(
        api_id: str,
        stage_name: str,
        log_group_arn: str,
        log_level: str = 'INFO'
    ) -> None:
        """Enable CloudWatch logging on stage"""
        apigw.update_stage(
            restApiId=api_id,
            stageName=stage_name,
            patchOperations=[
                {
                    'op': 'replace',
                    'path': '/accessLogSetting/destinationArn',
                    'value': log_group_arn
                },
                {
                    'op': 'replace',
                    'path': '/methodSettings/*/*/*/logging/loglevel',
                    'value': log_level
                }
            ]
        )

    @staticmethod
    def enable_xray_tracing(api_id: str, stage_name: str) -> None:
        """Enable X-Ray tracing on stage"""
        apigw.update_stage(
            restApiId=api_id,
            stageName=stage_name,
            patchOperations=[
                {'op': 'replace', 'path': '/tracingEnabled', 'value': 'true'}
            ]
        )

    @staticmethod
    def get_api_metrics(
        api_name: str,
        stage_name: str,
        metric_name: str = 'Count',
        minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Get CloudWatch metrics for API"""
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/ApiGateway',
            MetricName=metric_name,  # Count, Latency, 4XXError, 5XXError, CacheHitCount
            Dimensions=[
                {'Name': 'ApiName', 'Value': api_name},
                {'Name': 'Stage', 'Value': stage_name}
            ],
            StartTime=datetime.utcnow() - timedelta(minutes=minutes),
            EndTime=datetime.utcnow(),
            Period=300  # 5-minute intervals
        )
        return response['Datapoints']

    @staticmethod
    def create_error_alarm(
        api_name: str,
        stage_name: str,
        error_threshold: int = 10,
        sns_topic_arn: str = None
    ) -> None:
        """Create CloudWatch alarm for 5XX errors"""
        alarm_actions = [sns_topic_arn] if sns_topic_arn else []

        cloudwatch.put_metric_alarm(
            AlarmName=f'{api_name}-5XX-Errors',
            MetricName='5XXError',
            Namespace='AWS/ApiGateway',
            Statistic='Sum',
            Period=300,
            EvaluationPeriods=1,
            Threshold=error_threshold,
            ComparisonOperator='GreaterThanThreshold',
            Dimensions=[
                {'Name': 'ApiName', 'Value': api_name},
                {'Name': 'Stage', 'Value': stage_name}
            ],
            AlarmActions=alarm_actions
        )

    @staticmethod
    def get_usage(
        usage_plan_id: str,
        api_key_id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Get usage metrics for API key"""
        return apigw.get_usage(
            usagePlanId=usage_plan_id,
            keyId=api_key_id,
            startDate=start_date,
            endDate=end_date
        )


# ============================================================================
# CUSTOM DOMAINS
# ============================================================================

class CustomDomainOperations:
    """Custom domain management"""

    @staticmethod
    def create_domain_name(
        domain_name: str,
        certificate_arn: str,
        endpoint_type: str = 'REGIONAL'
    ) -> None:
        """Create custom domain name"""
        apigw.create_domain_name(
            domainName=domain_name,
            certificateArn=certificate_arn,
            endpointConfiguration={'types': [endpoint_type]},
            securityPolicy='TLS_1_2'
        )
        print(f"Domain {domain_name} created")

    @staticmethod
    def map_domain_to_api(
        domain_name: str,
        api_id: str,
        stage_name: str,
        base_path: str = None
    ) -> None:
        """Map custom domain to API stage"""
        apigw.create_base_path_mapping(
            domainName=domain_name,
            restApiId=api_id,
            basePath=base_path,
            stage=stage_name
        )
        print(f"Domain {domain_name} mapped to API {api_id} stage {stage_name}")

    @staticmethod
    def get_domain_name(domain_name: str) -> Dict[str, Any]:
        """Get domain name configuration"""
        return apigw.get_domain_name(domainName=domain_name)


# ============================================================================
# HTTP API OPERATIONS (V2)
# ============================================================================

class HTTPAPIOperations:
    """HTTP API (v2) operations - Newer, faster, cheaper"""

    @staticmethod
    def create_http_api(
        name: str,
        description: str = '',
        cors_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create HTTP API"""
        config = {
            'Name': name,
            'ProtocolType': 'HTTP',
            'Description': description
        }

        if cors_config:
            config['CorsConfiguration'] = cors_config

        response = apigw_v2.create_api(**config)
        return response['ApiId']

    @staticmethod
    def create_http_integration(
        api_id: str,
        integration_type: str,
        integration_uri: str = None,
        payload_format_version: str = '2.0'
    ) -> str:
        """Create HTTP integration (Lambda, HTTP, AWS service)"""
        config = {
            'ApiId': api_id,
            'IntegrationType': integration_type,  # HTTP, AWS_PROXY, HTTP_PROXY
            'PayloadFormatVersion': payload_format_version
        }

        if integration_uri:
            config['IntegrationUri'] = integration_uri

        response = apigw_v2.create_integration(**config)
        return response['IntegrationId']

    @staticmethod
    def create_http_route(
        api_id: str,
        route_key: str,
        integration_id: str,
        authorizer_id: str = None
    ) -> str:
        """Create HTTP route"""
        config = {
            'ApiId': api_id,
            'RouteKey': route_key,  # e.g., 'GET /users' or 'POST /users'
            'Target': f'integrations/{integration_id}'
        }

        if authorizer_id:
            config['AuthorizerId'] = authorizer_id

        response = apigw_v2.create_route(**config)
        return response['RouteId']


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_create_simple_api():
    """Example: Create simple REST API with Lambda integration"""
    # Create API
    api_id = RestAPIOperations.create_rest_api(
        name='UserAPI',
        description='Simple user management API'
    )

    # Get root resource
    root_id = ResourceOperations.get_root_resource(api_id)

    # Create /users resource
    users_id = ResourceOperations.create_resource(api_id, root_id, 'users')

    # Create GET /users method
    ResourceOperations.create_method(
        api_id, users_id, 'GET',
        auth_type='NONE'
    )

    # Create Lambda integration
    lambda_arn = 'arn:aws:lambda:us-east-1:123456789012:function:GetUsers'
    IntegrationOperations.create_lambda_integration(
        api_id, users_id, 'GET', lambda_arn,
        use_proxy=True
    )

    # Deploy to prod
    DeploymentOperations.create_deployment(
        api_id, 'prod',
        description='Initial deployment'
    )

    print(f"API created: {api_id}")
    return api_id


def example_create_api_with_auth():
    """Example: API with API key authentication"""
    # Create API
    api_id = RestAPIOperations.create_rest_api('SecureAPI', 'Secured with API keys')

    # Create usage plan
    usage_plan_id = AuthorizationOperations.create_usage_plan(
        'BasicPlan', api_id, 'prod',
        rate_limit=1000, burst_limit=2000,
        quota_limit=1000000, quota_period='MONTH'
    )

    # Create API key
    api_key_id = AuthorizationOperations.create_api_key(
        'mobile-app-key',
        description='Key for mobile app'
    )

    # Associate key to plan
    AuthorizationOperations.associate_api_key_to_usage_plan(
        usage_plan_id, api_key_id
    )

    print(f"API with auth created: {api_id}, key: {api_key_id}")
    return api_id, api_key_id


def example_create_http_api_with_cors():
    """Example: Modern HTTP API with CORS"""
    cors_config = {
        'AllowCredentials': True,
        'AllowHeaders': ['Content-Type', 'Authorization'],
        'AllowMethods': ['GET', 'POST', 'PUT', 'DELETE'],
        'AllowOrigins': ['https://example.com'],
        'ExposeHeaders': ['x-custom-header'],
        'MaxAge': 300
    }

    api_id = HTTPAPIOperations.create_http_api(
        'ModernAPI',
        description='HTTP API with CORS',
        cors_config=cors_config
    )

    print(f"HTTP API created: {api_id}")
    return api_id


if __name__ == '__main__':
    print("AWS API Gateway boto3 Examples")
    print("=" * 50)
    print("\nThese are generic examples. Update with your resources.")
    print("\nExample usage:")
    print("  - example_create_simple_api()")
    print("  - example_create_api_with_auth()")
    print("  - example_create_http_api_with_cors()")
