from re import Pattern
from typing import Any

from pydantic import (
    GetCoreSchemaHandler,
    GetPydanticSchema,
    validate_call,
)
from pydantic_core.core_schema import (
    CoreSchema,
    custom_error_schema,
    chain_schema,
    str_schema,
)


@validate_call
def regex_validator(pattern: Pattern[str], error_message: str):

    def get_pydantic_core_schema(
        source: type[Any],
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        schema = chain_schema(
            steps=[
                handler(source),
                custom_error_schema(
                    schema=str_schema(pattern=pattern),
                    custom_error_type="value_error",
                    custom_error_context={"error": error_message},
                ),
            ]
        )
        return schema

    return GetPydanticSchema(get_pydantic_core_schema)
