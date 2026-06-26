#!/bin/bash
cd "$(dirname "$0")"
python3 run_open_notator.py
echo
echo "Done. Press any key to close this window."
read -n 1
