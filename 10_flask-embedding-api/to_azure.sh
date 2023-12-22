#!/bin/bash

# netruk44.azurecr.io/netruk44/steamvibes-api:v0.3.3

az acr build --image steamvibes-api-base:latest --registry netruk44 --file model_base.Dockerfile .

az acr build --image steamvibes-api:v0.3_x64 --registry netruk44 --file Dockerfile .