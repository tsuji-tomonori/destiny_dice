from typing import Any, Self

from aws_cdk import aws_wafv2 as wafv2
from constructs import Construct

from cdk.paramater import build_name, paramater


class WafConstruct(Construct):
    def __init__(
        self: Self,
        scope: Construct,
        construct_id: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.ipset = wafv2.CfnIPSet(
            scope_=self,
            id="ipset",
            addresses=paramater["waf"]["common"]["addresses"],
            ip_address_version=paramater["waf"]["common"]["ip_address_version"],
            scope=paramater["waf"][construct_id]["scope"],
            name=build_name("ipset", construct_id),
        )

        self.webacl = wafv2.CfnWebACL(
            scope_=self,
            id="webacl",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(
                block=wafv2.CfnWebACL.BlockActionProperty(),
            ),
            scope=paramater["waf"][construct_id]["scope"],
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name=paramater["waf"]["common"]["metric_name"],
                sampled_requests_enabled=True,
            ),
            name=build_name("webacl", construct_id),
            rules=[
                wafv2.CfnWebACL.RuleProperty(
                    name=build_name("rule", construct_id),
                    priority=paramater["waf"]["common"]["priority"],
                    statement=wafv2.CfnWebACL.StatementProperty(
                        ip_set_reference_statement=wafv2.CfnWebACL.IPSetReferenceStatementProperty(
                            arn=self.ipset.attr_arn,
                        ),
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name=paramater["waf"]["common"]["metric_name"],
                        sampled_requests_enabled=True,
                    ),
                    action=wafv2.CfnWebACL.RuleActionProperty(
                        allow=wafv2.CfnWebACL.AllowActionProperty(),
                    ),
                ),
            ],
        )
