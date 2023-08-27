import json
import os
import traceback
from typing import Any, NamedTuple, Self

import boto3
import botocore
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource

logger = Logger()
dynamodb_client = boto3.client("dynamodb")
dynamodb_resource = boto3.resource("dynamodb")


class ClientError(Exception):
    def __init__(self: Self, input_param: str, message: str) -> None:
        self.message = message
        super().__init__(f"{message}: {input_param}")


class ServerError(Exception):
    def __init__(self: Self, input_param: str, message: str) -> None:
        super().__init__(f"{message}: {input_param}")


class EnvParam(NamedTuple):
    POOL_TABLE_NAME: str
    ITEM_TABLE_NAME: str

    @classmethod
    def from_env(cls: type["EnvParam"]) -> "EnvParam":
        try:
            return EnvParam(**{k: os.environ[k] for k in EnvParam._fields})
        except Exception as e:
            raise ServerError(
                json.dumps(os.environ),
                "Required environment variables are not set.",
            ) from e


class ApiEvent(NamedTuple):
    pool_name: str
    items: list[dict]

    @classmethod
    def from_event(cls: type["ApiEvent"], event: dict[str, Any]) -> "ApiEvent":
        try:
            body = json.loads(event["body"])
            return ApiEvent(
                pool_name=event["pathParameters"]["pool_name"],
                items=body["items"],
            )
        except Exception as e:
            raise ClientError(event["body"], "Invalid parameter.") from e

    def to_dynamo_items(self: Self) -> list[dict]:
        return [
            d | {"pool_name": self.pool_name, "item_id": i}
            for i, d in enumerate(self.items)
        ]


def put_items(
    db_resource: DynamoDBServiceResource,
    table_name: str,
    items: list[dict],
) -> None:
    logger.info(json.dumps(items))
    logger.info(table_name)
    table = db_resource.Table(table_name)
    try:
        with table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)
    except botocore.exceptions.ClientError as error:
        if error.response["Error"]["Code"] == "InternalServerError":
            raise ServerError(
                json.dumps(item),
                error.response["Error"]["Message"],
            ) from error
        else:
            raise ClientError(
                json.dumps(item),
                error.response["Error"]["Message"],
            ) from error


def delete_items(
    db_resource: DynamoDBServiceResource,
    table_name: str,
    keys: list[dict],
) -> None:
    if len(keys) == 0:
        return
    table = db_resource.Table(table_name)
    try:
        with table.batch_writer() as batch:
            for key in keys:
                batch.delete_item(Key=key)
    except botocore.exceptions.ClientError as error:
        if error.response["Error"]["Code"] == "InternalServerError":
            raise ServerError(
                json.dumps(key),
                error.response["Error"]["Message"],
            ) from error
        else:
            raise ClientError(
                json.dumps(key),
                error.response["Error"]["Message"],
            ) from error


def scan_items(client: DynamoDBClient, db_name: str, query: str) -> list[str]:
    paginator = client.get_paginator("scan")
    response_iterator = paginator.paginate(
        TableName=db_name,
    )
    try:
        return list(response_iterator.search(query))
    except botocore.exceptions.ClientError as error:
        if error.response["Error"]["Code"] == "InternalServerError":
            raise ServerError(
                query,
                error.response["Error"]["Message"],
            ) from error
        elif error.response["Error"]["Code"] == "ResourceNotFoundException":
            return []
        else:
            raise ClientError(
                query,
                error.response["Error"]["Message"],
            ) from error


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
    try:
        return list(response_iterator.search(query))
    except botocore.exceptions.ClientError as error:
        if error.response["Error"]["Code"] == "InternalServerError":
            raise ServerError(
                query,
                error.response["Error"]["Message"],
            ) from error
        elif error.response["Error"]["Code"] == "ResourceNotFoundException":
            return []
        else:
            raise ClientError(
                query,
                error.response["Error"]["Message"],
            ) from error


def get_item(
    db_resource: DynamoDBServiceResource,
    table_name: str,
    key: dict,
) -> dict[str, Any] | None:
    table = db_resource.Table(table_name)
    try:
        return table.get_item(Key=key).get("Item")
    except botocore.exceptions.ClientError as error:
        if error.response["Error"]["Code"] == "InternalServerError":
            raise ServerError(
                json.dumps(key),
                error.response["Error"]["Message"],
            ) from error
        elif error.response["Error"]["Code"] == "ResourceNotFoundException":
            return None
        else:
            raise ClientError(
                json.dumps(key),
                error.response["Error"]["Message"],
            ) from error


class Response(NamedTuple):
    status_code: int
    message: str

    def data(self: Self) -> dict[str, Any]:
        return {
            "statusCode": self.status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, DELETE",
                "Access-Control-Allow-Credentials": True,
                "Access-Control-Allow-Headers": "origin, x-requested-with",
            },
            "body": json.dumps(
                {
                    "message": self.message,
                },
            ),
            "isBase64Encoded": False,
        }


def service(
    body: ApiEvent,
    db_client: DynamoDBClient,
    db_resource: DynamoDBServiceResource,
    env: EnvParam,
) -> Response:
    response_pool = get_item(
        db_resource=db_resource,
        table_name=env.POOL_TABLE_NAME,
        key={"pool_name": body.pool_name},
    )
    if response_pool is not None:
        raise ClientError(
            input_param=body.pool_name,
            message=f"pool_name is already exists: {body.pool_name}",
        )
    response_items = query_items(
        client=db_client,
        db_name=env.ITEM_TABLE_NAME,
        key="pool_name",
        value=body.pool_name,
        query="Items[].item_id.N",
    )
    delete_items(
        db_resource=db_resource,
        table_name=env.ITEM_TABLE_NAME,
        keys=[{"pool_name": body.pool_name, "item_id": int(x)} for x in response_items],
    )
    put_items(
        db_resource=db_resource,
        table_name=env.ITEM_TABLE_NAME,
        items=body.to_dynamo_items(),
    )
    put_items(
        db_resource=db_resource,
        table_name=env.POOL_TABLE_NAME,
        items=[{"pool_name": body.pool_name, "num_item": len(body.items)}],
    )
    return Response(
        status_code=200,
        message="success",
    )


@logger.inject_lambda_context(
    correlation_id_path="requestContext.requestId",
)
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    try:
        return service(
            body=ApiEvent.from_event(event),
            db_client=dynamodb_client,
            db_resource=dynamodb_resource,
            env=EnvParam.from_env(),
        ).data()
    except ServerError:
        logger.error(traceback.format_exc())
        return Response(
            status_code=500,
            message="internal server error. Please access again after some time.",
        ).data()
    except ClientError as ce:
        logger.warning(traceback.format_exc())
        return Response(
            status_code=400,
            message=f"client error. {ce.message}",
        ).data()
    except Exception:
        logger.error(traceback.format_exc())
        return Response(
            status_code=500,
            message="internal server error. Please contact the operator.",
        ).data()
