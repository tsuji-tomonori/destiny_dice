from pathlib import Path
from typing import Any, Self

import aws_cdk as cdk
import tomllib
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_cloudwatch_actions as cloudwatch_actions
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from constructs import Construct

from cdk.infra_construct import InfraConstruct
from cdk.paramater import build_name, paramater

with (Path.cwd() / "pyproject.toml").open("rb") as f:
    project = tomllib.load(f)["project"]["name"]


class LambdaConstruct(Construct):
    def __init__(
        self: Self,
        scope: Construct,
        construct_id: str,
        infra: InfraConstruct,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        region = cdk.Stack.of(self).region
        powertools_layer = lambda_.LayerVersion.from_layer_version_arn(
            self,
            "powertools",
            layer_version_arn=f"arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV2:40",
        )

        lib_layer = lambda_.LayerVersion(
            self,
            "lib",
            code=lambda_.Code.from_asset(".layers"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
        )

        self.function = lambda_.Function(
            scope=self,
            id="function",
            code=lambda_.Code.from_asset(
                str(Path.cwd() / "src" / "app" / construct_id),
            ),
            handler="lambda_function.lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            environment=paramater["lambda"][construct_id]["env"],
            memory_size=paramater["lambda"][construct_id]["memory_size"],
            layers=[powertools_layer, lib_layer],
            function_name=build_name("function", construct_id),
        )

        self.function.add_environment(
            "POWERTOOLS_SERVICE_NAME",
            construct_id,
        )

        self.lambda_error_metric = self.function.metric_all_errors(
            period=cdk.Duration.minutes(5),
        )
        self.lambda_error_alarm = self.lambda_error_metric.create_alarm(
            scope=self,
            id="lambda_error",
            evaluation_periods=1,
            threshold=1,
            actions_enabled=True,
            alarm_name=build_name("alarm", f"lambda_error_{construct_id}"),
            alarm_description=(
                f"Lambda Function Error from {self.function.function_name}"
            ),
        )
        self.lambda_error_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(infra.sns_topic),
        )

        self.logs = logs.LogGroup(
            scope=self,
            id="logs",
            log_group_name=f"/aws/lambda/{self.function.function_name}",
            retention=logs.RetentionDays.THIRTEEN_MONTHS,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        self.log_error_metric = self.logs.add_metric_filter(
            id="log_error",
            filter_pattern=logs.FilterPattern.string_value(
                json_field="$.level",
                comparison="=",
                value="ERROR",
            ),
            metric_name=f"{construct_id}_error",
            metric_namespace=project,
            metric_value="1",
            unit=cloudwatch.Unit.COUNT,
            filter_name="ERROR",
        )

        self.log_error_alarm = cloudwatch.Alarm(
            scope=self,
            id="alarm",
            metric=cloudwatch.Metric(
                metric_name=f"{construct_id}_error",
                namespace=project,
            ),
            evaluation_periods=1,
            threshold=1,
            actions_enabled=True,
            alarm_name=build_name("alarm", f"log_error_{construct_id}"),
            alarm_description=f"Error level log from {self.function.function_name}",
        )
        self.log_error_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(infra.sns_topic),
        )
