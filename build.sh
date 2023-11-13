#!/bin/bash


mkdir build/

rm -rf venv
python3 -m venv venv
source venv/bin/activate

curl -o req.txt https://raw.githubusercontent.com/Josakko/tor-redirect/main/requirements.txt
pip3 install -r req.txt

python3 -m nuitka main.py --clang --clean-cache=all --remove-output --output-dir=build --onefile --standalone # --follow-imports

deactivate
rm -rf venv
rm -rf req.txt

mv build/main.bin build/tor-redirect

echo "Compiling finished!"