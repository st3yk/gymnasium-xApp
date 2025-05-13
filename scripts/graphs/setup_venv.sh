#!/bin/env bash

VENV_DIR="gph"

echo "Creating virtual environment in '${VENV_DIR}'..."
python3 -m venv "${VENV_DIR}"

echo "Activating virtual environment..."
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

echo "Virtual environment has been set up."
echo "To activate it, run: source ${VENV_DIR}/bin/activate"
echo "To deactivate, run: deactivate"
