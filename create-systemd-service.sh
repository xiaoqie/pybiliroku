#!/bin/sh
if [ "$#" -ne 1 ]; then
    echo "Usage: ./create-systemd-service.sh NAME OF PIPENV SCRIPT"
    exit
fi

echo "#/etc/systemd/system/pybiliroku-$1.service
[Unit]
Description=pybiliroku $1
After=network.target

[Service]
User=`whoami`
Group=`id -g -n`
ExecStart=`which pipenv` run $1
Environment=\"PYTHONUNBUFFERED=TRUE\"
WorkingDirectory=`pwd`

[Install]
WantedBy=multi-user.target
"
