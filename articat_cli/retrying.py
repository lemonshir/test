import logging
from functools import partial, wraps
from typing import Callable, Iterator

import settings
from requests.exceptions import HTTPError
from tenacity import RetryCallState, Retrying
from tenacity.retry import retry_base
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential

logger = logging.getLogger(__file__)


def log_before_retry(func: Callable, args: Iterator, kwargs: dict, state: RetryCallState):
    """
    log before the func is retried
    """
    if state.attempt_number > 1:
        logger.debug(
            f"This is the {state.attempt_number} times calling the func '{func}' with "
            f"args <{args}> and kwargs <{kwargs}>"
        )


class _IsConnectionError(retry_base):
    """
    Retry if the exception is the 'ConnectionError' which might be recoverable.
    """

    def __call__(self, retry_state: RetryCallState) -> bool:
        if not retry_state.outcome or not retry_state.outcome.failed:
            return False
        exception = retry_state.outcome.exception()
        return isinstance(exception, ConnectionError)


class _IsHttpServerError(retry_base):
    """
    Retry if the exception is 'HTTPError' with server error code which might be recoverable.
    """

    def __call__(self, retry_state: RetryCallState) -> bool:
        if not retry_state.outcome or not retry_state.outcome.failed:
            return False
        exception = retry_state.outcome.exception()
        if not isinstance(exception, HTTPError):
            return False
        http_status_code = exception.response.status_code
        return 500 <= http_status_code < 600


class _IsUnauthenticatedError(retry_base):
    """
    Retry if the exception is caused by an unauthenticated request which can be
    fixed by the login again or refreshing the token
    """

    def __call__(self, retry_state) -> bool:
        if not retry_state.outcome or not retry_state.outcome.failed:
            return False
        exception = retry_state.outcome.exception()
        if not isinstance(exception, HTTPError):
            return False
        http_status_code = exception.response.status_code
        if http_status_code == 401:
            return True
        return False


is_connection_error = _IsConnectionError()
is_http_server_error = _IsHttpServerError()
is_server_error = is_connection_error | is_http_server_error
is_unauthenticated_error = _IsUnauthenticatedError()
is_recoverable_error = is_server_error | is_unauthenticated_error


def retry_decorator(func):
    @wraps(func)
    def _retry(*args, **kwargs):
        for attempt in Retrying(
            retry=is_recoverable_error,
            before=partial(log_before_retry, func, args, kwargs),
            stop=stop_after_attempt(settings.RETRY_STOP_AFTER_ATTEMPT),
            wait=wait_exponential(min=settings.RETRY_WAIT_MIN, max=settings.RETRY_WAIT_MAX),
            reraise=True,
        ):
            with attempt:
                return func(*args, **kwargs)

    return _retry
