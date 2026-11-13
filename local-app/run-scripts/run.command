#!/bin/zsh
set -e
cd "$(dirname "$0")/.."

if ! command -v python3 >/dev/null 2>&1; then
	if command -v brew >/dev/null 2>&1; then
		brew install python
	else
		osascript -e 'display dialog "Python 3 is required but not installed. Please install Python 3 and run this again." buttons {"OK"} default button "OK"'
		exit 1
	fi
fi

if [ ! -d ".venv" ]; then
	python3 -m venv .venv
fi

"./.venv/bin/python" -m pip install --upgrade pip >/dev/null 2>&1 || true
"./.venv/bin/python" -m pip install -r requirements.txt
"./.venv/bin/python" main.py
