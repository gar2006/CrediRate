# The Trust Ledger - Build System

.PHONY: help setup db build run clean test

VENV = venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

help:
	@echo "Available commands:"
	@echo "  make setup   - Create Python virtual environment and install dependencies"
	@echo "  make db      - Initialize the SQLite database and seed mock data"
	@echo "  make build   - Full build pipeline (setup + db)"
	@echo "  make run     - Start the Flask backend server"
	@echo "  make clean   - Remove the virtual environment and database file"

setup: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements.txt
	@echo "Setting up virtual environment..."
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt
	@touch $(VENV)/bin/activate
	@echo "Setup complete."

db: setup
	@echo "Initializing database..."
	$(PYTHON) db_setup.py

build: setup db
	@echo "Build complete! You can now use 'make run'"

run: setup
	@echo "Starting the application..."
	$(PYTHON) app.py

clean:
	@echo "Cleaning up project artifacts..."
	rm -rf $(VENV)
	rm -rf __pycache__
	rm -f trust_ledger.db
	@echo "Clean complete."
