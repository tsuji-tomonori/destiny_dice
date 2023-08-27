from typing import Any, Self

from aws_cdk import Stack
from constructs import Construct

from cdk.waf_construct import WafConstruct


class WafCloudFrontStack(Stack):
    def __init__(
        self: Self,
        scope: Construct | None = None,
        construct_id: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.waf = WafConstruct(self, "cloudfront")
