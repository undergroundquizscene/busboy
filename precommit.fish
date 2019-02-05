#!/usr/bin/env fish
pipenv run isort **.py **.pyi
pipenv run black **.py **.pyi
