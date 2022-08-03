from dataclasses import dataclass
from typing import Dict

from .exceptions import UrlUnconverted
from .server import Articat


def convert_url_to_pkg_srp_uid(server: Articat, artifact_url: str) -> str:
    input_data = {"inputs": [artifact_url]}
    json_resp: Dict = server.convert_url_to_pkg_srp_uid(input_data)
    outputs = json_resp.get("outputs")
    assert outputs
    comp_ids = outputs.get("comp_ids")
    if not comp_ids:
        raise UrlUnconverted(artifact_url)
    srp_uid = comp_ids[0]
    return srp_uid


def fetch_pkg_prov_data_by_srp_uid(server: Articat, srp_uid: str) -> Dict:
    input_data = {"inputs": [srp_uid]}
    json_resp: Dict = server.fetch_pkg_prov_data_by_srp_uid(input_data)
    outputs = json_resp.get("outputs")
    return outputs


@dataclass
class Context:
    server_alias: str
    log_level: str
    trace_back: bool
    is_within_envoy: bool
    is_csp_prod: bool
    csp_client_id: str
    csp_client_secret: str
