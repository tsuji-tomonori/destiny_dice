from pathlib import Path

import tomllib

with (Path.cwd() / "pyproject.toml").open("rb") as f:
    project = tomllib.load(f)["project"]["name"]


paramater = {
    "lambda": {
        "create_pool": {
            "env": {
                "LOG_LEVEL": "INFO",
            },
            "memory_size": 128,
        },
        "list_pool": {
            "env": {
                "LOG_LEVEL": "INFO",
            },
            "memory_size": 128,
        },
        "delete_pool": {
            "env": {
                "LOG_LEVEL": "INFO",
            },
            "memory_size": 128,
        },
        "dice": {
            "env": {
                "LOG_LEVEL": "INFO",
            },
            "memory_size": 128,
        },
    },
    "waf": {
        "common": {
            "addresses": [],
            "ip_address_version": "IPV4",
            "metric_name": project,
            "priority": 100,
        },
        "apigw": {
            "scope": "REGIONAL",
        },
    },
}


def build_name(service: str, hostname: str) -> str:
    return f"dice-{service}-{hostname}"
