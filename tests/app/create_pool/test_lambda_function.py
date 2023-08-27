import json
import os

import boto3
from moto import dynamodb

from tests.app.utils import (
    LambdaContext,
    build_lambda_event,
    create_item_table,
    create_pool_table,
    delete_items,
    get_item,
    query_items,
)


def set_env_and_create_db():
    os.environ["AWS_ACCESS_KEY_ID"] = "AKIAIOSFODNN7EXAMPLE"
    os.environ[
        "AWS_SECRET_ACCESS_KEY"
    ] = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"  # noqa: S105
    os.environ["AWS_DEFAULT_REGION"] = "us-west-2"
    client = boto3.client("dynamodb")
    os.environ["POOL_TABLE_NAME"] = create_pool_table(client)
    os.environ["ITEM_TABLE_NAME"] = create_item_table(client)
    os.environ["POWERTOOLS_SERVICE_NAME"] = "create_pool"
    os.environ["LOG_LEVEL"] = "INFO"


@dynamodb.mock_dynamodb
def test_gp():
    # 1. 初期化
    set_env_and_create_db()
    from src.app.create_pool.lambda_function import lambda_handler

    # 2. テストの実行
    res = lambda_handler(
        event=build_lambda_event(
            body={
                "items": [
                    {
                        "item_name": "hoge",
                    },
                ],
            },
            path_paramater={
                "pool_name": "test",
            },
        ),
        context=LambdaContext.empty(),
    )

    # 3. アサーション
    # API の結果チェック
    assert res["statusCode"] == 200
    assert json.loads(res["body"]) == {"message": "success"}
    # pool table の状態確認
    pool_record = get_item(
        db_resource=boto3.resource("dynamodb"),
        table_name="pool",
        key={
            "pool_name": "test",
        },
    )
    assert pool_record == {"pool_name": "test", "num_item": 1}
    # item table の状態確認
    # 1件抜き出して項目に問題がないか確認する
    item_record = get_item(
        db_resource=boto3.resource("dynamodb"),
        table_name="item",
        key={
            "pool_name": "test",
            "item_id": 0,
        },
    )
    assert item_record == {
        "pool_name": "test",
        "item_id": 0,
        "item_name": "hoge",
    }
    # すべて抜き出し何件あるか確認する
    item_records = query_items(
        client=boto3.client("dynamodb"),
        db_name="item",
        key="pool_name",
        value="test",
        query="Items[].item_id.N",
    )
    assert item_records == ["0"]


@dynamodb.mock_dynamodb
def test_gp_1000():
    # 1. 初期化
    set_env_and_create_db()
    from src.app.create_pool.lambda_function import lambda_handler

    # 2. テストの実行
    res = lambda_handler(
        event=build_lambda_event(
            body={
                "items": [{"item_name": str(i)} for i in range(1000)],
            },
            path_paramater={
                "pool_name": "test_1000",
            },
        ),
        context=LambdaContext.empty(),
    )

    # 3. アサーション
    # API の結果チェック
    assert res["statusCode"] == 200
    assert json.loads(res["body"]) == {"message": "success"}
    # pool table の状態確認
    pool_record = get_item(
        db_resource=boto3.resource("dynamodb"),
        table_name="pool",
        key={
            "pool_name": "test_1000",
        },
    )
    assert pool_record == {"pool_name": "test_1000", "num_item": 1000}
    # item table の状態確認
    # 1件抜き出して項目に問題がないか確認する
    item_record = get_item(
        db_resource=boto3.resource("dynamodb"),
        table_name="item",
        key={
            "pool_name": "test_1000",
            "item_id": 0,
        },
    )
    assert item_record == {
        "pool_name": "test_1000",
        "item_id": 0,
        "item_name": "0",
    }
    # すべて抜き出し何件あるか確認する
    item_records = query_items(
        client=boto3.client("dynamodb"),
        db_name="item",
        key="pool_name",
        value="test_1000",
        query="Items[].item_id.N",
    )
    assert item_records == [str(x) for x in range(1000)]


@dynamodb.mock_dynamodb
def test_delete_items():
    # 1. 初期化
    set_env_and_create_db()
    from src.app.create_pool.lambda_function import lambda_handler

    # まずはデータを入れる
    res = lambda_handler(
        event=build_lambda_event(
            body={
                "items": [{"item_name": str(i)} for i in range(1000)],
            },
            path_paramater={
                "pool_name": "delete_items",
            },
        ),
        context=LambdaContext.empty(),
    )
    # put table だけ消すことで, 実行時にエラーがありゴミデータが残った状態を作る
    delete_items(
        db_resource=boto3.resource("dynamodb"),
        table_name="pool",
        keys=[
            {
                "pool_name": "delete_items",
            },
        ],
    )

    # 2. テストの実行
    res = lambda_handler(
        event=build_lambda_event(
            body={
                "items": [{"item_name": "hoge"} for i in range(5000)],
            },
            path_paramater={
                "pool_name": "delete_items",
            },
        ),
        context=LambdaContext.empty(),
    )

    # 3. アサーション
    # API の結果チェック
    assert res["statusCode"] == 200
    assert json.loads(res["body"]) == {"message": "success"}
    # pool table の状態確認
    pool_record = get_item(
        db_resource=boto3.resource("dynamodb"),
        table_name="pool",
        key={
            "pool_name": "delete_items",
        },
    )
    assert pool_record == {"pool_name": "delete_items", "num_item": 5000}
    # item table の状態確認
    # 1件抜き出して項目が置き換わっていることを確認する
    item_record = get_item(
        db_resource=boto3.resource("dynamodb"),
        table_name="item",
        key={
            "pool_name": "delete_items",
            "item_id": 0,
        },
    )
    assert item_record == {
        "pool_name": "delete_items",
        "item_id": 0,
        "item_name": "hoge",
    }
    # すべて抜き出し何件あるか確認する
    item_records = query_items(
        client=boto3.client("dynamodb"),
        db_name="item",
        key="pool_name",
        value="delete_items",
        query="Items[].item_id.N",
    )
    assert item_records == [str(x) for x in range(5000)]
