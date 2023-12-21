#!/bin/bash

az acr build --image steamvibes-api-base:latest --registry netruk44 -- file model_base.Dockerfile .

az acr build --image steamvibes-api:v0.1_x64 --registry netruk44 --file Dockerfile .