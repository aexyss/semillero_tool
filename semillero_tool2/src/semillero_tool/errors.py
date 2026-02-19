class SemilleroToolError(Exception):
    """Base error for semillero_tool."""


class ExcelReadError(SemilleroToolError):
    pass


class SchemaError(SemilleroToolError):
    pass


class AmbiguityError(SemilleroToolError):
    pass


class ConfigError(SemilleroToolError):
    pass
