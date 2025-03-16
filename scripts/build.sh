#!/bin/env bash

PARENT_IMAGE=python_xapp_runner:i-release # built from oran-sc-ric repo
TAG=xapp-stable-baselines3
VERSION=2.4.1 # version aligned with stable-baselines3


echo "docker build --build-arg PARENT_IMAGE=${PARENT_IMAGE} -t ${TAG}:${VERSION} ."
docker build --build-arg PARENT_IMAGE=${PARENT_IMAGE} -t ${TAG}:${VERSION} .
