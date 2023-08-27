import aws_cdk as cdk
from aws_cdk import assertions
from syrupy.matchers import path_type

from cdk.waf_cloudfront_stack import WafCloudFrontStack


def test_snapshot(snapshot) -> None:
    app = cdk.Stack()
    stack = WafCloudFrontStack(app, "test")
    template = assertions.Template.from_stack(stack)

    matcher = path_type(
        {
            r".*\.S3Key$": (str,),
            r".*\.Addresses$": (list,),
        },
        regex=True,
    )
    assert template.to_json() == snapshot(matcher=matcher)
