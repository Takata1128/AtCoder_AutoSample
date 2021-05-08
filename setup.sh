#! /bin/bash
url="$1"
username="$2"
password="$3"
pipenv run python3 ./setup.py "$url" "$username" "$password" 