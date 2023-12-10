#!/bin/bash

python3 ascross.py crosswords.samples/*.toml --format a4 --output crosswords.samples/a4.html
python3 ascross.py crosswords.samples/*.toml --format a5two --output crosswords.samples/a5two.html
python3 ascross.py crosswords.samples/*.toml --format a5two --solution --output crosswords.samples/a5two_solutions.html
python3 ascross.py crosswords.samples/thomas_minikrypto.toml --format svg --output crosswords.samples/thomas_minikrypto.svg
