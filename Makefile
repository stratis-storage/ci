.PHONY: lint
lint:
	pylint ./blackbox/parse_json.py
	pylint ./dependency_management/*
	pylint ./misc_scripts/*

.PHONY: lint-non-pygithub
lint-non-pygithub:
	pylint ./blackbox/parse_json.py
	pylint ./misc_scripts/* --ignore=batch_cancel.py

.PHONY: fmt
fmt:
	isort ./blackbox/parse_json.py
	isort ./dependency_management/*
	isort ./misc_scripts/
	black ./blackbox/parse_json.py
	black ./dependency_management/
	black ./dependency_management/compare_fedora_versions
	black ./dependency_management/set_lower_bounds
	black ./misc_scripts/*
	shfmt -l -w .

.PHONY: fmt-travis
fmt-travis:
	isort --diff --check-only ./blackbox/parse_json.py
	isort --diff --check-only ./dependency_management/*
	isort --diff --check-only ./misc_scripts/
	black ./blackbox/parse_json.py --check
	black ./dependency_management/ --check
	black ./dependency_management/compare_fedora_versions --check
	black ./dependency_management/set_lower_bounds --check
	black ./misc_scripts/* --check
	shfmt -d .

.PHONY: yamllint
yamllint:
	yamllint --strict .github/workflows/*.yml

.PHONY: shellcheck
shellcheck:
	find . -name '*.sh' | xargs shellcheck --severity=warning
