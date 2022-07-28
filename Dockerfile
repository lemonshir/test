# Copyright (c) 2022 VMware, Inc.  All rights reserved.
# VMware Confidential

FROM harbor-repo.vmware.com/dockerhub-proxy-cache/library/python:3.9-slim-bullseye

# Ensure console output isn't cached in case we crash or terminate
# the container.
ENV PYTHONUNBUFFERED 1
ENV LANG C.UTF-8

# Install necessary system packages
COPY etc/sources.bullseye.list /etc/apt/sources.list
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get -qq -y install libpq-dev

# Install python packages
RUN ln -s -f /usr/bin/python3 /usr/bin/python
RUN python3 -m pip install --upgrade pip --quiet
RUN pip install articat-cli --extra-index-url https://build-artifactory.eng.vmware.com/artifactory/api/pypi/pace-pypi-local/simple

RUN mkdir /articat-cli

WORKDIR /articat-cli

ENTRYPOINT ["articat-cli"]
