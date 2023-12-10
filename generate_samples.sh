#!/bin/bash

python3 ascross.py crosswords.samples/*.toml --format a4 --page-num 1 --output crosswords.samples/a4.html
python3 ascross.py crosswords.samples/*.toml --format a5two --page-num 2 --output crosswords.samples/a5two.html
python3 ascross.py crosswords.samples/*.toml --format a5two --page-num 2 --solution --output crosswords.samples/a5two_solutions.html
python3 ascross.py crosswords.samples/thomas_minikrypto.toml --format svg --output crosswords.samples/thomas_minikrypto.svg
