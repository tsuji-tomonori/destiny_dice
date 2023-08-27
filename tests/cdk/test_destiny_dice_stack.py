import aws_cdk as cdk
from aws_cdk import assertions
from syrupy.matchers import path_type

from cdk.destiny_dice_stack import DestinyDiceStack


def test_snapshot(snapshot) -> None:
    app = cdk.Stack()
    stack = DestinyDiceStack(app, "test", "hoge")
    template = assertions.Template.from_stack(stack)

    matcher = path_type(
        {
            r".*\.S3Key$": (str,),
            r".*\.Addresses$": (list,),
            r".*\.SourceObjectKeys$": (list,),
        },
        regex=True,
    )
    assert template.to_json() == snapshot(matcher=matcher)
