"""
The entrypoint of the CLI
"""
import logging

import click
import urllib3
from click import pass_context

from . import settings
from .e2e_test import run_e2e_test
from .enums import LogLevel, Server
from .helper import Context
from .server import Articat
from .settings import SERVERS
from .smoke_test import run_smoke_test

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


logger = logging.getLogger(__file__)


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
    default=Server.ARTICAT_BETA.value,
    type=str,
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


main.add_command(run_smoke_test)
main.add_command(run_e2e_test)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
