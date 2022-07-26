from types import MappingProxyType

from .enums import Server

ESP_TOKEN_URL = "https://auth.esp.vmware.com/api/auth/v1/api-tokens/authorize"
CSP_TOKEN_URL = "https://console.cloud.vmware.com/csp/gateway/am/api/auth/token"
CSP_STG_TOKEN_URL = "https://console-stg.cloud.vmware.com/csp/gateway/am/api/auth/token"
ARTICAT_API_VERSION = "api/v1"

RETRY_STOP_AFTER_ATTEMPT = 4
RETRY_WAIT_MIN = 1
RETRY_WAIT_MAX = 10

COMPATIBLE_TO_SWAGGER_RESP = False

TASK_TIMEOUT_FOR_ARTIFACT_IDS = 600
TASK_TIMEOUT_FOR_ARTIFACT_PROV = 60
TASK_SLEEP_BEFORE_PULL = 3
TASK_STRING_DIGEST_INPUT = "test string"

SERVERS = MappingProxyType(
    {
        Server.LOCAL.value: {
            "hostname": "http://shirvc:8000",
            "ssl_verify": False,
            "is_within_envoy": False,
            "csp_token_url": CSP_STG_TOKEN_URL,
        },
        Server.DEV.value: {
            "hostname": "https://helix-dev.ara.decc.vmware.com",
            "ssl_verify": True,
            "is_within_envoy": True,
            "csp_token_url": CSP_STG_TOKEN_URL,
        },
        Server.ARA_DEV.value: {
            "hostname": "https://articat.ara.decc.vmware.com",
            "ssl_verify": True,
            "is_within_envoy": False,
            "csp_token_url": CSP_STG_TOKEN_URL,
        },
        Server.BETA.value: {
            "hostname": "https://helix-beta.vela.decc.vmware.com",
            "ssl_verify": True,
            "is_within_envoy": True,
            "csp_token_url": CSP_STG_TOKEN_URL,
        },
        Server.VELA_BETA.value: {
            "hostname": "https://articat.vela.decc.vmware.com",
            "ssl_verify": True,
            "is_within_envoy": False,
            "csp_token_url": CSP_STG_TOKEN_URL,
        },
        Server.ESP_BETA.value: {
            "hostname": "https://helix-beta.vela.decc.vmware.com",
            "ssl_verify": True,
            "is_within_envoy": True,
            "csp_token_url": CSP_TOKEN_URL,
        },
        Server.PAVO_BETA.value: {
            "hostname": "https://articat.pavo.decc.vmware.com",
            "ssl_verify": True,
            "is_within_envoy": False,
            "csp_token_url": CSP_STG_TOKEN_URL,
        },
    }
)
