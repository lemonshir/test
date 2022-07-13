# Project introduction

This project serves as the CLI of the Articat service.

## User guide

This project has been published to this VMware [PyPI Repo](https://build-artifactory.eng.vmware.com/artifactory/api/pypi/pace-pypi-local/simple)
in the [Artifactory](https://build-artifactory.eng.vmware.com/). It can be
installed as a command line tool by all Python package installers.

### Installation

#### Pip

You can add this repository via the `--extra-index-url` parameter.

```bash
pip install articat-cli --extra-index-url https://build-artifactory.eng.vmware.com/artifactory/api/pypi/pace-pypi-local/simple
```

#### Poetry

You can add this repository to the `pyproject.toml` file in your project.

```bash
[[tool.poetry.source]]
name = "ves_pypi"
url = "https://build-artifactory.eng.vmware.com/artifactory/api/pypi/pace-pypi-local/simple"
```

then add it by

```bash
poetry add articat-cli
```

### Shell completion

After this project is installed, you can enable the `shell` completion for your shell.

#### bash

Add this to `~/.bashrc`:

```bash
_ARTICAT_CLI_CMD="articat-cli"
if command -v $_ARTICAT_CLI_CMD >/dev/null 2>&1; then
    eval "$(_ARTICAT_CLI_COMPLETE=bash_source $_ARTICAT_CLI_CMD)"
fi
```

#### zsh

Add this to `~/.zshrc`:

```bash
_ARTICAT_CLI_CMD="articat-cli"
if command -v $_ARTICAT_CLI_CMD >/dev/null 2>&1; then
    eval "$(_ARTICAT_CLI_COMPLETE=zsh_source $_ARTICAT_CLI_CMD)"
fi
```

### Usage as a CLI tool

After this project is installed as a Python package, you can execute the
following command to see the usage.

```bash
articat-cli --help
```

#### ESP API token

The ESP API token is required to generate the access token which is used to
communicate with Helix services. The API token can be generated [here](https://auth.esp.vmware.com/api-tokens/).
You can either specify it via the command line option or export it as the environment
variable which can be used by this tool automatically with:

```bash
export ESP_API_TOKEN=<YOUR_ESP_API_TOKEN>
```

**NOTE:** The access token will be refreshed automatically if it expires when the
CLI is running.

### Usage as a library

#### Basic Usage

The class `Helix` or `HttpServer` can be inherited and extended as necessary. For example,

```python
from srp_validator.server import HelixServer


class PolicyServer(Helix):
    def __init__(self, **kwargs):
        super().__init__(service="policy", **kwargs)

    def list_policies(self):
        """
        List all policies
        """
        sub_url = "controls"
        full_url = self.get_full_url(sub_url)
        return self.get(full_url)
```

#### Defaul Retry Policy

##### Retry Condition

By default, all HTTP methods in `HttpServer` will be retried if any of the recoverable
errors below happens:

1. a `ConnectionError` is raised
2. 500 <= status code < 600
3. status code == 401, which means the token has expired

##### Retry Attempt

There will be at most 4 attempts to retry

## Development Guide

Please go through the following check list to ensure that you can setup
the development env.

### Clone the repository and config commit template

```bash
git clone git@gitlab.eng.vmware.com:osm-dev/articat-cli.git
cd articat-cli
git config commit.template etc/git-commit-template.md
```

### Python version

We use the `Python ^3.9`.

### Install [poetry](https://python-poetry.org/)

We use `poetry` to manage the dependencies in this project. You can install it by:

```bash
pip install poetry
```

You can then enable the tab completion by following the
[doc](https://python-poetry.org/docs/#enable-tab-completion-for-bash-fish-or-zsh).
The most frequently used commands should be `poetry add` and `poetry remove`.
For example, you can use `poetry add --dev` to add dependencies only required by
the development env and use `poetry add` to add dependencies required by the production env. In the both situation, `poetry` will update the `pyproject.toml` and `poetry.lock` automatically for you.  
You can refer to the [poetry documentaion](https://python-poetry.org/docs/) for more information.

### Setup Python virtual env

```bash
$ python3 -m venv articat-cli
$ source articat-cli/bin/activate
# Go to the project directory to install the dependencies
$ poetry install
```

### Setup [pre-commit](https://pre-commit.com/)

```bash
pre-commit install -f -c etc/pre-commit-config.yaml
```

The following hooks will be run automatically in the `pre-commit` phase:

- [black](https://github.com/psf/black): The uncompromising Python code formatter

- [isort](https://github.com/timothycrosley/isort): A Python utility to sort imports

- [pylint](https://github.com/PyCQA/pylint): A tool to analyse Python code

### Publish to Artifactory

```bash
# Update the `verson` in the `pyproject.toml` first
poetry config repositories.ves_pypi https://build-artifactory.eng.vmware.com/artifactory/api/pypi/pace-pypi-local
poetry config http-basic.ves_pypi YOUR_AD_ID_WITHOUT_DOMAIN YOUR_AD_PASSWORD
poetry publish -r ves_pypi --build
```
