from enum import Enum, unique


@unique
class ItemKey(Enum):
    RESULTS = "results"
    OJBECTS = "objects"


@unique
class Protocal(Enum):
    HTTP = "http"
    HTTPS = "https"


@unique
class Server(Enum):
    LOCAL = "local"
    HELIX_DEV = "helix_dev"
    HELIX_STAGING = "helix_staging"
    HELIX_PRODUCTION = "helix_production"


@unique
class Service(Enum):
    MDS = "mds"
    POLICY = "policy"
    ARTICAT = "articat"


@unique
class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@unique
class HttpCode(Enum):
    UNAUTHORIZED = 401


@unique
class PuncEnum(Enum):
    """
    Enumerations for punctuation marks
    """

    AT = "@"
    COLON = ":"
    COMMA = ","
    DOT = "."
    EMPTY = ""
    HYPHEN = "-"
    NEW_LINE = "\n"
    PLUS = "+"
    SLASH = "/"
    SPACE = " "
    TILDE = "~"
    UNDERSCORE = "_"


@unique
class RespItemKey(Enum):
    """
    The key for items in Http Response
    """

    RESULTS = "results"
    OJBECTS = "objects"


@unique
class TaskStatus(Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@unique
class TaskEndpointUrl(Enum):
    COMPONENT_IDS = "component-ids"
    ARTIFACT_PROV = "artifact-prov"
    STRING_DIGEST = "string-digest"
