#!/bin/bash
cd "$(dirname "$0")"
source ~/.bashrc
echo ~/.bashrc
echo $PATH
python3 manager.py
