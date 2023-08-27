from typing import Any, Self

from aws_cdk import Stack
from constructs import Construct

from cdk.app_construct import AppConstruct
from cdk.infra_construct import InfraConstruct
from cdk.static_construct import StaticConstruct


class DestinyDiceStack(Stack):
    def __init__(
        self: Self,
        scope: Construct,
        construct_id: str,
        web_acl_arn: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.infra = InfraConstruct(self, "infra")
        self.static = StaticConstruct(self, "static", web_acl_arn)
        self.app = AppConstruct(self, "app", self.infra)
