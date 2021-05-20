.PHONY: lint
lint:
	pylint ./blackbox/parse_json.py
	pylint ./dependency_management/*
	pylint ./misc_scripts/

.PHONY: lint-non-pygithub
lint-non-pygithub:
	pylint ./blackbox/parse_json.py
	pylint ./misc_scripts/generate_test_config.py

.PHONY: fmt
fmt:
	isort ./blackbox/parse_json.py
	isort ./dependency_management/*
	isort ./misc_scripts/
	black ./blackbox/parse_json.py
	black ./dependency_management/
	black ./misc_scripts/

.PHONY: fmt-travis
fmt-travis:
	isort --diff --check-only ./blackbox/parse_json.py
	isort --diff --check-only ./dependency_management/*
	isort --diff --check-only ./misc_scripts/
	black ./blackbox/parse_json.py --check
	black ./dependency_management/ --check
	black ./misc_scripts/ --check

.PHONY: yamllint
yamllint:
	yamllint --strict .github/workflows/main.yml
