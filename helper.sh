#!/bin/bash

source env_file

if [ "$1" = "build" ] ; then
    echo rebuild docker image
    sudo -E docker compose up --build -d
else
    sudo -E docker compose up -d
fi