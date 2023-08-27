from typing import Any, Self

import aws_cdk as cdk
from aws_cdk import aws_dynamodb as dynamdb
from aws_cdk import aws_sns as sns
from constructs import Construct

from cdk.paramater import build_name
from cdk.waf_construct import WafConstruct


class InfraConstruct(Construct):
    def __init__(
        self: Self,
        scope: Construct,
        construct_id: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB
        self.table_pool = dynamdb.Table(
            scope=self,
            id="pool",
            partition_key=dynamdb.Attribute(
                name="pool_name",
                type=dynamdb.AttributeType.STRING,
            ),
            billing_mode=dynamdb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            table_name=build_name("table", "pool"),
        )

        self.table_item = dynamdb.Table(
            scope=self,
            id="item",
            partition_key=dynamdb.Attribute(
                name="pool_name",
                type=dynamdb.AttributeType.STRING,
            ),
            sort_key=dynamdb.Attribute(
                name="item_id",
                type=dynamdb.AttributeType.NUMBER,
            ),
            billing_mode=dynamdb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            table_name=build_name("table", "item"),
        )

        # AWS SNS
        self.sns_topic = sns.Topic(
            self,
            id="topic",
            topic_name=build_name("topic", "error_notify"),
        )

        self.waf = WafConstruct(self, "apigw")
