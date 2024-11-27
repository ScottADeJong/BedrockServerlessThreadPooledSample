from aws_cdk import (
    # Duration,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    RemovalPolicy,
    Duration,
    CfnOutput,
)
from constructs import Construct

class BedrockSampleStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        my_lambda = _lambda.Function(
                self, 'BedrockSamplePromptHandler',
                runtime=_lambda.Runtime.PYTHON_3_12,
                code=_lambda.Code.from_asset('lambda'),
                handler="BedrockSample-lambda.lambda_handler",
                timeout=Duration.seconds(60),
                architecture=_lambda.Architecture.ARM_64,
        )

        my_lambda.add_to_role_policy(iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    'bedrock:InvokeModel',
                ],
                resources=[
                    'arn:aws:bedrock:us-east-1::foundation-model/*',
                ],
        ))

        my_lambda.add_to_role_policy(iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    's3:ListAllMyBuckets',
                ],
                resources=[
                    'arn:aws:s3:::*',
                ],
        ))

        my_api = apigw.LambdaRestApi(
            self, 'BedrockSample-api',
            handler=my_lambda,
            rest_api_name="bedrock-sample",
            deploy_options=apigw.StageOptions(
                logging_level=apigw.MethodLoggingLevel.INFO),
        )

        ingress = s3.Bucket(
            self, "ingress",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY
        )

        egress = s3.Bucket(
            self, "egress",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY
        )

        egress.grant_write(my_lambda)
        ingress.grant_read(my_lambda)
        ingress.add_event_notification(
            s3.EventType.OBJECT_CREATED, s3n.LambdaDestination(my_lambda))

        CfnOutput(self, "API Gateway URL", value=my_api.url)
