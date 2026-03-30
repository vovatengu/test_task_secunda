PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
BACKEND := backend

.PHONY: backend-install backend-uninstall clean-egg-info structure

backend-install:
	$(PIP) install -e $(BACKEND)/

backend-uninstall:
	$(PIP) uninstall -y payment-processing-backend 2>/dev/null || true

# Remove setuptools metadata (normally lives under $(BACKEND)/ next to pyproject.toml; never commit it).
clean-egg-info:
	rm -rf $(BACKEND)/*.egg-info $(BACKEND)/src/*.egg-info

structure:
	@find $(BACKEND)/src -type f -name '*.py' | sort | sed 's|^$(BACKEND)/||'
