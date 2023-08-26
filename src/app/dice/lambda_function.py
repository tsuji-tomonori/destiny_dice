import json
import os
import random
import traceback
from decimal import Decimal
from typing import Any, NamedTuple, Self

import boto3
import botocore
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from mypy_boto3_dynamodb import DynamoDBServiceResource

logger = Logger()
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

    @classmethod
    def from_event(
        cls: type["ApiEvent"],
        event: dict[str, Any],
    ) -> "ApiEvent":
        try:
            return ApiEvent(
                pool_name=event["pathParameters"]["pool_name"],
            )
        except Exception as e:
            raise ClientError(event["body"], "Invalid parameter.") from e


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


def decimal_default_proc(obj: Any) -> int:  # noqa: ANN401
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError


class Response(NamedTuple):
    status_code: int
    message: str | dict

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
                default=decimal_default_proc,
            ),
            "isBase64Encoded": False,
        }


def service(
    body: ApiEvent,
    db_resource: DynamoDBServiceResource,
    env: EnvParam,
) -> Response:
    response_pool = get_item(
        db_resource=db_resource,
        table_name=env.POOL_TABLE_NAME,
        key={"pool_name": body.pool_name},
    )
    if response_pool is None:
        raise ClientError(
            input_param=body.pool_name,
            message=f"pool_name is empty: {body.pool_name}",
        )
    key = {
        "pool_name": body.pool_name,
        "item_id": random.randint(0, response_pool["num_item"] - 1),
    }
    response_items = get_item(
        db_resource=db_resource,
        table_name=env.ITEM_TABLE_NAME,
        key=key,
    )
    if response_items is None:
        raise ServerError(
            input_param=json.dumps(key),
            message="item dose not exist",
        )
    return Response(
        status_code=200,
        message=response_items,
    )


@logger.inject_lambda_context(
    correlation_id_path="requestContext.requestId",
)
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    try:
        return service(
            body=ApiEvent.from_event(event),
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
