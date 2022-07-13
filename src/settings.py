from types import MappingProxyType

from enums import Server

SERVERS = MappingProxyType(
    {
        Server.LOCAL.value: {"hostname": "http://shirvc:8000", "ssl_verify": False, "is_within_envoy": False},
        Server.DEV.value: {
            "hostname": "https://helix-dev.ara.decc.vmware.com",
            "ssl_verify": True,
            "is_within_envoy": True,
        },
        Server.BETA.value: {
            "hostname": "https://helix-beta.vela.decc.vmware.com",
            "ssl_verify": True,
            "is_within_envoy": True,
        },
    }
)

ESP_TOKEN_URL = "https://auth.esp.vmware.com/api/auth/v1/api-tokens/authorize"
ARTICAT_API_VERSION = "api/v1"

RETRY_STOP_AFTER_ATTEMPT = 4
RETRY_WAIT_MIN = 1
RETRY_WAIT_MAX = 10

COMPATIBLE_TO_SWAGGER_RESP = False

TASK_TIMEOUT_FOR_ARTIFACT_IDS = 600
TASK_TIMEOUT_FOR_ARTIFACT_PROV = 60
TASK_SLEEP_BEFORE_PULL = 3
TASK_STRING_DIGEST_INPUT = "test string"
