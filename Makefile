.PHONY: lint
lint:
	pylint ./blackbox/parse_json.py
	pylint ./misc_scripts/

.PHONY: lint-non-pygithub
lint-non-pygithub:
	pylint ./blackbox/parse_json.py
	pylint ./misc_scripts/generate_test_config.py

.PHONY: fmt
fmt:
	isort ./blackbox/parse_json.py
	isort ./misc_scripts/
	black ./blackbox/parse_json.py
	black ./misc_scripts/

.PHONY: fmt-travis
fmt-travis:
	isort --diff --check-only ./blackbox/parse_json.py
	isort --diff --check-only ./misc_scripts/
	black ./blackbox/parse_json.py --check
	black ./misc_scripts/ --check

.PHONY: yamllint
yamllint:
	yamllint --strict .github/workflows/main.yml
