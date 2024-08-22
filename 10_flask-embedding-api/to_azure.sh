#!/bin/bash

az acr build --image steamvibes-api-base:latest --registry netruk44 --file model_base.Dockerfile .

az acr build --image netruk44/steamvibes-api:v0.5 --registry netruk44 --file Dockerfile .

# Remember to delete base image from ACR after build