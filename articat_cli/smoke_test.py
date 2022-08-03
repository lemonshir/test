"""
The module for the smoke test
"""
import logging
import sys
import traceback

import click
from click import pass_obj

from .helper import Context, convert_url_to_pkg_srp_uid, fetch_pkg_prov_data_by_srp_uid
from .server import Articat

logger = logging.getLogger(__file__)


@click.command()
@pass_obj
def run_smoke_test(ctx_obj: Context):
    try:
        server: Articat = ctx_obj.server
        artifact_url = "https://build-artifactory.eng.vmware.com/jcenter-cache/junit/junit/4.13/junit-4.13.jar"
        srp_uid = convert_url_to_pkg_srp_uid(server, artifact_url)
        logger.info(f"The SRP Unique Id is {srp_uid}")
        prov_data = fetch_pkg_prov_data_by_srp_uid(server, srp_uid)
        logger.info(f"The prov data is {prov_data}")
        logging.info("The smoke test has completed successfully.")
    except Exception as e:
        if ctx_obj.trace_back:
            traceback.print_exc()
        logging.error(f"The smoke test has failed! Error msg: {e}")
        sys.exit(1)
