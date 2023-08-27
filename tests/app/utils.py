import json
from pathlib import Path
from typing import Any, NamedTuple

from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource


def put_items(
    db_resource: DynamoDBServiceResource,
    table_name: str,
    items: list[dict],
) -> None:
    table = db_resource.Table(table_name)
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)


def delete_items(
    db_resource: DynamoDBServiceResource,
    table_name: str,
    keys: list[dict],
) -> None:
    table = db_resource.Table(table_name)
    with table.batch_writer() as batch:
        for key in keys:
            batch.delete_item(Key=key)


def scan_items(client: DynamoDBClient, db_name: str, query: str) -> list[str]:
    paginator = client.get_paginator("scan")
    response_iterator = paginator.paginate(
        TableName=db_name,
    )
    return list(response_iterator.search(query))


def query_items(
    client: DynamoDBClient,
    db_name: str,
    key: str,
    value: str,
    query: str,
) -> list[str]:
    paginator = client.get_paginator("query")
    response_iterator = paginator.paginate(
        TableName=db_name,
        KeyConditions={
            key: {"ComparisonOperator": "EQ", "AttributeValueList": [{"S": value}]},
        },
    )
    return list(response_iterator.search(query))


def get_item(
    db_resource: DynamoDBServiceResource,
    table_name: str,
    key: dict,
) -> dict | None:
    table = db_resource.Table(table_name)
    return table.get_item(Key=key).get("Item")


def create_pool_table(
    client: DynamoDBClient,
) -> str:
    table_name = "pool"
    client.create_table(
        AttributeDefinitions=[
            {
                "AttributeName": "pool_name",
                "AttributeType": "S",
            },
        ],
        TableName=table_name,
        KeySchema=[
            {
                "AttributeName": "pool_name",
                "KeyType": "HASH",
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    return table_name


def create_item_table(
    client: DynamoDBClient,
) -> str:
    table_name = "item"
    client.create_table(
        AttributeDefinitions=[
            {
                "AttributeName": "pool_name",
                "AttributeType": "S",
            },
            {
                "AttributeName": "item_id",
                "AttributeType": "N",
            },
        ],
        TableName=table_name,
        KeySchema=[
            {
                "AttributeName": "pool_name",
                "KeyType": "HASH",
            },
            {
                "AttributeName": "item_id",
                "KeyType": "RANGE",
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    return table_name


class LambdaContext(NamedTuple):
    function_name: str
    function_version: str
    invoked_function_arn: str
    memory_limit_in_mb: int
    aws_request_id: str
    log_group_name: str
    log_stream_name: str

    @classmethod
    def empty(cls: type["LambdaContext"]) -> "LambdaContext":
        return LambdaContext(
            function_name="",
            function_version="",
            invoked_function_arn="",
            memory_limit_in_mb=256,
            aws_request_id="",
            log_group_name="",
            log_stream_name="",
        )


def build_lambda_event(body: dict, path_paramater: dict) -> Any:  # noqa: ANN401
    template_path = Path.cwd() / "tests" / "resource" / "apigw_event_template.json"
    with template_path.open() as f:
        template = json.load(f)
    template["body"] = json.dumps(body)
    template["pathParameters"] = path_paramater
    return template
