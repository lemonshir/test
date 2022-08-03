"""
The module for the e2e test
"""
import json
import logging
import sys
import traceback
from pathlib import Path

import click
import urllib3
from click import File
from click import Path as ClickPath
from click import pass_obj

from . import settings
from .exceptions import TaskFailed, TaskTimeout, UrlUnconverted
from .helper import Context, convert_url_to_pkg_srp_uid, fetch_pkg_prov_data_by_srp_uid
from .server import Articat
from .utils import join_url_segs

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


logger = logging.getLogger(__file__)


class Report:
    ATTRS_FOR_FAILED_URL = [
        "unconverted_urls",
        "timeout_in_conversion",
        "task_failed_in_conversion",
        "unexpected_error_in_conversion",
        "timeout_in_fetch_prov_data",
        "task_failed_in_fetch_prov_data",
        "unexpected_error_in_fetch_prov_data",
    ]
    ATTRS = [
        "non_artifactory_urls",
        "artifactory_urls",
        "successful_urls",
    ] + ATTRS_FOR_FAILED_URL

    def __init__(self):
        for attr in Report.ATTRS:
            setattr(self, attr, [])
        self.unexpected_errors = {}

    @classmethod
    def create(cls, report_dict: dict) -> "Report":
        report = Report()
        for attr in Report.ATTRS:
            value = report_dict.get(attr, [])
            setattr(report, attr, value)
        report.unexpected_errors = report_dict.get("unexpected_errors", {})
        return report

    def print(self):
        count_of_total_urls = len(self.non_artifactory_urls) + len(self.artifactory_urls)
        logger.info(f"Totally {count_of_total_urls} urls")
        for attr in Report.ATTRS:
            count_of_url = len(getattr(self, attr))
            logger.info(f"Totally {count_of_url} {attr} urls")

    def to_dict(self) -> dict:
        report_dict = {}
        for attr in Report.ATTRS:
            report_dict[attr] = getattr(self, attr)
        report_dict["unexpected_errors"] = self.unexpected_errors
        return report_dict

    def dump_to_json_file(self, file_path: Path):
        with file_path.open("w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_json_file(cls, file_path: Path):
        with file_path.open() as f:
            report_dict = json.load(f)
        return cls.create(report_dict)

    def add_successful_url(self, url: str):
        self.successful_urls.append(url)
        for attr in Report.ATTRS_FOR_FAILED_URL:
            url_list = getattr(self, attr)
            if url in url_list:
                url_list.remove(url)
        self.unexpected_errors.pop(url, None)


@click.command()
@click.option(
    "--observer-json-file",
    required=True,
    type=File(),
    help="the json file of the observer result",
)
@click.option(
    "--report-json-file",
    default=Path.home() / "report.json",
    type=ClickPath(path_type=Path),
    help="the json file of the test report",
)
@click.option(
    "--use-pre-report/--not-use-pre-report",
    show_default=True,
    default=True,
    help="If use the pre-report, skip the urls which are successful before",
)
@pass_obj
def run_e2e_test(ctx_obj: Context, observer_json_file: str, report_json_file: str, use_pre_report: bool):
    try:
        if use_pre_report and report_json_file.exists():
            report = Report.load_from_json_file(report_json_file)
        else:
            report = Report()
        observer_json_result = json.load(observer_json_file)
        for entry in observer_json_result["artifact_repositories"]:
            host = f"{settings.HTTPS_PROTOCAL}{entry['host']}"
            for path in entry["path"]:
                url = join_url_segs([host, path])
                if host in settings.ARTIFACTORY_HOSTS:
                    if url not in report.artifactory_urls:
                        report.artifactory_urls.append(url)
                else:
                    if url not in report.non_artifactory_urls:
                        report.non_artifactory_urls.append(url)
        server: Articat = ctx_obj.server
        count = 0
        for url in report.artifactory_urls:
            count += 1
            logger.info(f"Handling the {count}th url: {url}")
            if url in report.successful_urls:
                logger.info(f"Skip the successful url in the previous report: {url}")
                continue
            srp_uid = _convert_url_to_pkg_srp_uid(server, url, report)
            if srp_uid:
                _fetch_pkg_prov_data_by_srp_uid(server, url, srp_uid, report)
            if count % 20 == 0:
                report.dump_to_json_file(report_json_file)
            report.print()
        report.dump_to_json_file(report_json_file)
        report.print()
        logger.info("The e2e test has finished successfully!")
    except Exception as e:
        if ctx_obj.trace_back:
            traceback.print_exc()
        logging.error(f"The smoke test has failed! Error msg: {e}")
        sys.exit(1)


def _convert_url_to_pkg_srp_uid(server: Articat, url: str, report: Report) -> str:
    try:
        return convert_url_to_pkg_srp_uid(server, url)
    except UrlUnconverted:
        if url not in report.unconverted_urls:
            report.unconverted_urls.append(url)
    except TaskTimeout:
        if url not in report.timeout_in_conversion:
            report.timeout_in_conversion.append(url)
    except TaskFailed:
        if url not in report.task_failed_in_conversion:
            report.task_failed_in_conversion.append(url)
    except Exception as e:
        if url not in report.unexpected_error_in_conversion:
            report.unexpected_error_in_conversion.append(url)
        report.unexpected_errors[url] = str(e)
    return ""


def _fetch_pkg_prov_data_by_srp_uid(server: Articat, url: str, srp_uid: str, report: Report):
    try:
        fetch_pkg_prov_data_by_srp_uid(server, srp_uid)
        report.add_successful_url(url)
    except TaskTimeout:
        if url not in report.timeout_in_fetch_prov_data:
            report.timeout_in_fetch_prov_data.append(url)
    except TaskFailed:
        if url not in report.task_failed_in_fetch_prov_data:
            report.task_failed_in_fetch_prov_data.append(url)
    except Exception as e:
        if url not in report.unexpected_error_in_fetch_prov_data:
            report.unexpected_error_in_fetch_prov_data.append(url)
        report.unexpected_errors[url] = str(e)
