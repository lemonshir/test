"""
The entrypoint of the CLI
"""
import logging
import sys
import traceback
from dataclasses import dataclass
from typing import Dict

import click
import settings
import urllib3
from click import pass_context, pass_obj
from enums import LogLevel, Server
from exceptions import UrlUnconverted
from server import Articat
from settings import SERVERS

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


logger = logging.getLogger(__file__)


@dataclass
class Context:
    server_alias: str
    log_level: str
    trace_back: bool
    is_within_envoy: bool
    is_csp_prod: bool
    csp_client_id: str
    csp_client_secret: str


def get_server_help_msg() -> str:
    servers = ", ".join(sorted(SERVERS.keys()))
    return f"the alias of server. Options: {servers}. You can also specify your own server instance url here."


def get_log_help_msg() -> str:
    log_levels = ", ".join([l.name for l in LogLevel])
    return f"the log level. Options: {log_levels}"


def get_articat_server(context: Context) -> Articat:
    server_config = SERVERS.get(context.server_alias, {})
    if not server_config:
        server_config = {
            "hostname": context.server_alias,
            "is_within_envoy": context.is_within_envoy,
            "ssl_verify": False,
        }
        if context.is_csp_prod:
            server_config["csp_token_url"] = settings.CSP_TOKEN_URL
        else:
            server_config["csp_token_url"] = settings.CSP_STG_TOKEN_URL
    server_config["csp_client_id"] = context.csp_client_id
    server_config["csp_client_secret"] = context.csp_client_secret
    return Articat(**server_config)


@click.group()
@click.option(
    "-s",
    "--server-alias",
    default=Server.BETA.value,
    show_default=True,
    help=get_server_help_msg(),
)
@click.option(
    "-l",
    "--log-level",
    show_default=True,
    default=LogLevel.INFO.value,
    help=get_log_help_msg(),
)
@click.option(
    "--trace-back/--no-trace-back",
    show_default=True,
    default=True,
    help="Whether print the traceback when an unexpected error happens",
)
@click.option(
    "--is-within-envoy/--not-within-envoy",
    show_default=True,
    default=False,
    help="Whether the server is within the Helix Envoy",
)
@click.option(
    "--is-csp-prod/--not-csp-prod",
    show_default=True,
    default=False,
    help="Whether use the CSP prod env to generate the token",
)
@click.option(
    "--csp-client-id",
    required=True,
    type=str,
    envvar="CSP_CLIENT_ID",
    help="the client id of the CSP OAuth APP",
)
@click.option(
    "--csp-client-secret",
    required=True,
    type=str,
    envvar="CSP_CLIENT_SECRET",
    help="the client secret of the CSP OAuth APP",
)
@pass_context
def main(
    ctx,
    server_alias,
    log_level,
    trace_back,
    is_within_envoy,
    is_csp_prod,
    csp_client_id,
    csp_client_secret,
):
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(filename)s<%(funcName)s>:%(lineno)s: %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
    )
    ctx.obj = Context(
        server_alias=server_alias,
        log_level=log_level,
        trace_back=trace_back,
        is_within_envoy=is_within_envoy,
        is_csp_prod=is_csp_prod,
        csp_client_id=csp_client_id,
        csp_client_secret=csp_client_secret,
    )
    ctx.obj.server = get_articat_server(ctx.obj)


@main.command()
@pass_obj
def run_smoke_test(ctx_obj: Context):
    server: Articat = ctx_obj.server
    try:
        srp_uid = convert_url_to_pkg_srp_uid(server)
        logger.info(f"The SRP Unique Id is {srp_uid}")
        prov_data = fetch_pkg_prov_data_by_srp_uid(server, srp_uid)
        logger.info(f"The prov data is {prov_data}")
        logging.info("The smoke test has completed successfully.")
    except Exception as e:
        if ctx_obj.trace_back:
            traceback.print_exc()
        logging.error(f"The smoke test has failed! Error msg: {e}")
        sys.exit(1)


def convert_url_to_pkg_srp_uid(server: Articat) -> str:
    artifact_url = "https://build-artifactory.eng.vmware.com/jcenter-cache/junit/junit/4.13/junit-4.13.jar"
    input_data = {"inputs": [artifact_url]}
    json_resp: Dict = server.convert_url_to_pkg_srp_uid(input_data)
    outputs = json_resp.get("outputs")
    assert outputs
    comp_ids = outputs.get("comp_ids")
    if not comp_ids:
        raise UrlUnconverted(artifact_url)
    return comp_ids[0]


def fetch_pkg_prov_data_by_srp_uid(server: Articat, srp_uid: str) -> Dict:
    input_data = {"inputs": [srp_uid]}
    json_resp: Dict = server.fetch_pkg_prov_data_by_srp_uid(input_data)
    outputs = json_resp.get("outputs")
    return outputs


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
