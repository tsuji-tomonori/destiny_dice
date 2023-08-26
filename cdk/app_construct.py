from typing import Any, Self

from aws_cdk import aws_apigateway as apigw
from constructs import Construct

from cdk.infra_construct import InfraConstruct
from cdk.lmd_construct import LambdaConstruct
from cdk.paramater import build_name


class AppConstruct(Construct):
    def __init__(
        self: Self,
        scope: Construct,
        construct_id: str,
        infra: InfraConstruct,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.api = apigw.RestApi(
            scope=self,
            id="api",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
            ),
            rest_api_name=build_name("api", "destiny_dice"),
            description="destiny_dice",
        )
        pools = self.api.root.add_resource("pools")
        pool_name = pools.add_resource("{pool_name}")
        dice = pool_name.add_resource("dice")

        self.create_pool = LambdaConstruct(self, "create_pool", infra)
        pool_name.add_method(
            http_method="POST",
            integration=apigw.LambdaIntegration(
                handler=self.create_pool.function,
            ),
        )
        assert self.create_pool.function.role is not None
        infra.table_pool.grant_read_write_data(self.create_pool.function.role)
        self.create_pool.function.add_environment(
            key="POOL_TABLE_NAME",
            value=infra.table_pool.table_name,
        )
        infra.table_item.grant_read_write_data(self.create_pool.function.role)
        self.create_pool.function.add_environment(
            key="ITEM_TABLE_NAME",
            value=infra.table_item.table_name,
        )

        self.list_pool = LambdaConstruct(self, "list_pool", infra)
        pools.add_method(
            http_method="GET",
            integration=apigw.LambdaIntegration(
                handler=self.list_pool.function,
            ),
        )
        assert self.list_pool.function.role is not None
        infra.table_pool.grant_read_data(self.list_pool.function.role)
        self.list_pool.function.add_environment(
            key="POOL_TABLE_NAME",
            value=infra.table_pool.table_name,
        )

        self.delete_pool = LambdaConstruct(self, "delete_pool", infra)
        pool_name.add_method(
            http_method="DELETE",
            integration=apigw.LambdaIntegration(
                handler=self.delete_pool.function,
            ),
        )
        assert self.delete_pool.function.role is not None
        infra.table_pool.grant_read_write_data(self.delete_pool.function.role)
        self.delete_pool.function.add_environment(
            key="POOL_TABLE_NAME",
            value=infra.table_pool.table_name,
        )
        infra.table_item.grant_read_write_data(self.delete_pool.function.role)
        self.delete_pool.function.add_environment(
            key="ITEM_TABLE_NAME",
            value=infra.table_item.table_name,
        )

        self.dice = LambdaConstruct(self, "dice", infra)
        dice.add_method(
            http_method="GET",
            integration=apigw.LambdaIntegration(
                handler=self.dice.function,
            ),
        )
        assert self.dice.function.role is not None
        infra.table_pool.grant_read_data(self.dice.function.role)
        self.dice.function.add_environment(
            key="POOL_TABLE_NAME",
            value=infra.table_pool.table_name,
        )
        infra.table_item.grant_read_data(self.dice.function.role)
        self.dice.function.add_environment(
            key="ITEM_TABLE_NAME",
            value=infra.table_item.table_name,
        )
