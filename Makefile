.PHONY: lint
lint:
	pylint ./blackbox/parse_json.py
	pylint ./batch_cancel.py

.PHONY: fmt
fmt:
	isort ./blackbox/parse_json.py
	isort ./batch_cancel.py
	black ./blackbox/parse_json.py
	black ./batch_cancel.py

.PHONY: fmt-travis
fmt-travis:
	isort --diff --check-only ./blackbox/parse_json.py
	isort --diff --check-only ./batch_cancel.py
	black ./blackbox/parse_json.py --check
	black ./batch_cancel.py --check

.PHONY: yamllint
yamllint:
	yamllint --strict .github/workflows/main.yml
