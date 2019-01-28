#!/usr/bin/env fish
pipenv run isort **.py
pipenv run black **.py **.pyi
