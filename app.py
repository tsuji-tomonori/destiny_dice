from pathlib import Path

import aws_cdk as cdk
import tomllib
from aws_cdk import Tags

from cdk.destiny_dice_stack import DestinyDiceStack
from cdk.waf_cloudfront_stack import WafCloudFrontStack


def add_name_tag(scope):  # noqa: ANN001, ANN201
    for child in scope.node.children:
        if cdk.Resource.is_resource(child):
            Tags.of(child).add("Name", child.node.path.replace("/", "-"))
        add_name_tag(child)


with (Path.cwd() / "pyproject.toml").open("rb") as f:
    project = tomllib.load(f)["project"]["name"]

app = cdk.App()

waf_stack = WafCloudFrontStack(
    scope=app,
    construct_id=f"{project.replace('_', '-')}-waf",
    env=cdk.Environment(
        region="us-east-1",
    ),
    cross_region_references=True,
)
DestinyDiceStack(
    scope=app,
    construct_id=f"{project.replace('_', '-')}",
    env=cdk.Environment(
        region="ap-northeast-1",
    ),
    cross_region_references=True,
    web_acl_arn=waf_stack.waf.webacl.attr_arn,
)

Tags.of(app).add("Project", project)
add_name_tag(app)

app.synth()
