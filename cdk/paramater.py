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
}


def build_name(service: str, hostname: str) -> str:
    return f"dice-{service}-{hostname}"
