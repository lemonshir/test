"""
Module which contains the classes for HttpServer
"""

import functools
import logging
import time
import typing as t
from abc import ABC, abstractmethod
from typing import Dict, Iterator

import requests
from requests import Response, Session
from requests.auth import HTTPBasicAuth
from requests.hooks import HOOKS
from requests.sessions import merge_hooks
from tenacity import retry
from tenacity.retry import retry_if_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_fixed

from . import settings
from .enums import RespItemKey, Service, TaskEndpointUrl, TaskStatus
from .exceptions import TaskFailed, TaskTimeout
from .retrying import retry_decorator
from .utils import join_url_segs

logger = logging.getLogger(__file__)


class HttpRespHook:
    """Base hook class"""

    def __str__(self) -> str:
        return self.__class__.__name__


class LogHook(HttpRespHook):
    """The hook to generate the log"""

    def __call__(self, resp: Response, *_args, **_kwargs) -> None:
        http_method: str = resp.request.method
        logger.info(f"{self}: {http_method.upper()} {resp.request.url} {resp.status_code}")


class AuthHook(HttpRespHook):
    """The hook to refresh access token if it got expired"""

    def __init__(self, server: "Helix"):
        self._server = server

    def __call__(self, resp: Response, *_args, **_kwargs) -> None:
        url: str = resp.request.url
        if url.lower().startswith(self._server.root_url.lower()) and resp.status_code == 401:
            self._server.authenticate()
            logger.info(f"{self}: The access token is refreshed")


def resp_decorator(func):
    """
    This decorator adds some attributes in "swagger_client.rest.RESTResponse" to the instance
    of the class "requests.Response" so that we can replace the default REST client provided
    by the 'Swagger' with our own REST client which supports more functions like the
    retrying, session and logging. This leverages the duck typing in Python.
    """

    @functools.wraps(func)
    def decorate_resp(*args, **kwargs):
        resp: Response = func(*args, **kwargs)
        try:
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Exception: {e}. \nResp.content: {resp.content.decode()}")
            raise e from None

        if not settings.COMPATIBLE_TO_SWAGGER_RESP:
            return resp

        def getheaders():
            return resp.headers

        def getheader(name, default=None):
            return resp.headers.get(name, default)

        resp.getheaders = getheaders
        resp.getheader = getheader
        resp.data = resp.content
        resp.status = resp.status_code
        return resp

    return decorate_resp


class HttpServer(ABC):
    def __init__(
        self,
        hostname: str,
        service_name: str = "",
        api_version: str = "",
        item_key: str = RespItemKey.RESULTS.value,
        ssl_verify: bool = True,
    ):
        self._hostname = hostname
        self._service_name = service_name
        self._api_version = api_version
        self._root_url = join_url_segs([self._hostname, self._service_name, self._api_version])
        self._item_key = item_key
        self._session = requests.Session()
        self._session.verify = ssl_verify
        self.register_resp_hooks()

    def register_resp_hooks(self) -> None:
        """
        Register hooks to preprocess the Http response
        """
        log_hook = LogHook()
        self._customized_hooks = {HOOKS[0]: [log_hook]}
        self._session.hooks = merge_hooks(self._customized_hooks, self._session.hooks)

    @property
    def session(self) -> Session:
        return self._session

    @property
    def root_url(self) -> str:
        return self._root_url

    def join_url(self, sub_url: str) -> str:
        return join_url_segs([self.root_url, sub_url])

    def set_csrf(self, csrf_token: str) -> None:
        """
        Set the CSRF token to include in the headers for requests.
        """
        self._session.headers.update({"X-CSRF-TOKEN": csrf_token})

    @retry_decorator
    @resp_decorator
    def _raw_get(
        self,
        url: str,
        headers: t.Optional[Dict[str, str]] = None,
        params: t.Optional[Dict[str, str]] = None,
        timeout: t.Optional[float] = 5,
    ) -> Response:
        """
        Return an un-interpreted response for a GET of a full URL.
        """
        if params is None:
            params = {}
        if headers is None:
            headers = self._session.headers
        else:
            headers.update(self._session.headers)
        return self._session.get(url, params=params, headers=headers, timeout=timeout)

    def GET(
        self,
        url: str,
        *_args,
        headers: t.Optional[Dict[str, str]] = None,
        query_params: t.Optional[Dict[str, str]] = None,
        _request_timeout=None,
        **_kwargs,
    ) -> Response:
        """
        A wrapper method for the internal method '_raw_get', which returns all
        the results.
        It's best to use this method when the queryset is small. For a large
        queryset, use the method 'get_by_page' instead.
        """
        return self._raw_get(
            url,
            params=query_params,
            headers=headers,
            timeout=_request_timeout,
        )

    def get_by_page(
        self,
        url: str,
        headers: t.Optional[Dict[str, str]] = None,
        query_params: t.Optional[Dict[str, str]] = None,
        _request_timeout=None,
    ) -> Iterator[Dict[str, t.Any]]:
        """
        Perform a stream of GET requests by pagination
        """
        if query_params is None:
            query_params = {}
        not_done = True
        while not_done:
            resp = self._raw_get(
                url,
                params=query_params,
                headers=headers,
                timeout=_request_timeout,
            )
            json_resp = resp.json()
            items = json_resp.get(self.item_key, [])
            url = json_resp.get("next")
            not_done = bool(items) and bool(url)
            for value in items:
                yield value

    @retry_decorator
    @resp_decorator
    def POST(
        self,
        url: str,
        *_args,
        headers: t.Optional[Dict[str, str]] = None,
        body: t.Optional[Dict[str, t.Any]] = None,
        data: t.Optional[Dict[str, t.Any]] = None,
        **kwargs,
    ) -> Response:
        """
        Perform a POST request against the Http server.
        """
        if headers is None:
            headers = self._session.headers
        else:
            headers.update(self._session.headers)
        return self._session.post(url, json=body, data=data, headers=headers, **kwargs)

    @resp_decorator
    @retry_decorator
    def PATCH(
        self,
        url: str,
        *_args,
        headers: t.Optional[Dict[str, str]] = None,
        body: t.Optional[Dict[str, t.Any]] = None,
        **_kwargs,
    ) -> Response:
        """
        Perform a PATCH request against the Http server.
        """
        if headers is None:
            headers = self._session.headers
        else:
            headers.update(self._session.headers)
        return self._session.patch(url, data=body, headers=headers)

    @resp_decorator
    @retry_decorator
    def DELETE(
        self,
        url: str,
        *_args,
        headers: t.Optional[Dict[str, str]] = None,
        **_kwargs,
    ) -> Response:
        """
        Perform a DELETE request against the Http server.
        """
        if headers is None:
            headers = self._session.headers
        else:
            headers.update(self._session.headers)
        return self._session.delete(url, headers=headers)

    def get(self, *args, **kwargs) -> Dict:
        return self.GET(*args, **kwargs).json()

    def post(self, *args, **kwargs) -> Dict:
        return self.POST(*args, **kwargs).json()

    def patch(self, *args, **kwargs) -> Dict:
        return self.PATCH(*args, **kwargs).json()

    def delete(self, *args, **kwargs) -> Dict:
        return self.DELETE(*args, **kwargs).json()

    @abstractmethod
    def authenticate(self):
        """
        Authenticate in the server
        """


class Helix(HttpServer):
    """
    Base class for services on the Helix platform which will be accessed outside
    of the Envoy
    """

    def __init__(
        self,
        hostname,
        service_name,
        api_version,
        csp_token_url=None,
        csp_client_id=None,
        csp_client_secret=None,
        **kwargs,
    ):
        if not kwargs.pop("is_within_envoy"):
            service_name = None
        super().__init__(hostname, service_name, api_version, **kwargs)
        self._csp_token_url = csp_token_url
        self._csp_client_id = csp_client_id
        self._csp_client_secret = csp_client_secret
        self.register_auth_hooks()

    @property
    def csp_client_id(self):
        return self._csp_client_id

    def register_auth_hooks(self) -> None:
        """
        Register hooks to preprocess the Http response
        """
        auth_hook = AuthHook(self)
        self._session.hooks[HOOKS[0]].append(auth_hook)

    def authenticate(self) -> None:
        """
        This is the unified mechanism to authenticate in the Helix platform:
        generate the temporary access token from the API Token and update the
        header with the new access token
        """
        data = "grant_type=client_credentials"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        basic_auth = HTTPBasicAuth(self._csp_client_id, self._csp_client_secret)
        resp = self.POST(self._csp_token_url, data=data, auth=basic_auth, headers=headers)
        self._access_token = resp.json()["access_token"]
        self._session.headers["Authorization"] = f"Bearer {self._access_token}"
        logger.debug(f"Authorization: {self._session.headers['Authorization']}")


class Articat(Helix):
    ARTIFACT_IDS = "artifact-ids"
    ARTIFACT_PROV = "artifact-prov"
    STRING_DIGEST = "string-digest"

    def __init__(self, hostname, *args, **kwargs):
        super().__init__(hostname, Service.ARTICAT.value, settings.ARTICAT_API_VERSION, *args, **kwargs)

    @retry(
        retry=retry_if_exception_type((TaskFailed, TaskTimeout)),
        wait=wait_fixed(3),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def execute_task(self, task_endpoint_url, post_data, timeout) -> Dict:
        full_url = join_url_segs([self.root_url, task_endpoint_url, "tasks"])
        json_resp = self.post(full_url, body=post_data)
        task_status = TaskStatus(json_resp["status"])
        task_url = json_resp["task_url"]
        if task_status in [TaskStatus.CANCELLED, TaskStatus.FAILED, TaskStatus.SUCCEEDED]:
            old_task_url = task_url
            logger.info(f"This task has been executed before: {task_url}")
            url_with_force_option = f"{full_url}?force=1"
            json_resp = self.post(url_with_force_option, body=post_data)
            task_status = TaskStatus(json_resp["status"])
            task_url = json_resp["task_url"]
            assert task_url != old_task_url, "The task url is not changed by a force post"
        logging.info(f"A new task is created: {task_url}")
        json_resp = self.pull_until_task_is_done_or_timeout(task_url, timeout)
        task_status = TaskStatus(json_resp["status"])
        if task_status in [TaskStatus.FAILED, TaskStatus.CANCELLED]:
            logger.error(f"The task status is '{task_status.value}'")
            raise TaskFailed()
        return json_resp

    def pull_until_task_is_done_or_timeout(self, task_url, timeout) -> Dict[str, str]:
        time_spent = 0
        while time_spent < timeout:
            json_resp = self.get(task_url)
            task_status = TaskStatus(json_resp["status"])
            if task_status in [TaskStatus.SUCCEEDED, TaskStatus.CANCELLED, TaskStatus.FAILED]:
                return json_resp
            time.sleep(settings.TASK_SLEEP_BEFORE_PULL)
        raise TaskTimeout

    def convert_url_to_pkg_srp_uid(self, post_data):
        return self.execute_task(TaskEndpointUrl.ARTIFACT_IDS.value, post_data, settings.TASK_TIMEOUT_FOR_ARTIFACT_IDS)

    def fetch_pkg_prov_data_by_srp_uid(self, post_data):
        return self.execute_task(
            TaskEndpointUrl.ARTIFACT_PROV.value, post_data, settings.TASK_TIMEOUT_FOR_ARTIFACT_PROV
        )

    def string_digest(self):
        post_data = {"inputs": [settings.TASK_STRING_DIGEST_INPUT]}
        return self.execute_task(
            TaskEndpointUrl.ARTIFACT_PROV.value, post_data, settings.TASK_TIMEOUT_FOR_ARTIFACT_PROV
        )
