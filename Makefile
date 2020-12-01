.PHONY: lint
lint:
	pylint ./blackbox/parse_json.py

.PHONY: fmt
fmt:
	isort ./blackbox/parse_json.py
	black ./blackbox/parse_json.py

.PHONY: fmt-travis
fmt-travis:
	isort --diff --check-only ./blackbox/parse_json.py
	black ./blackbox/parse_json.py --check

.PHONY: yamllint
yamllint:
	yamllint --strict .github/workflows/main.yml
