.PHONY: lint
lint:
	pylint ./blackbox/parse_json.py
	pylint ./dependency_management/* --disable=R0801
	pylint ./misc_scripts/*.py --disable=R0801
	pylint ./release_management/*.py --disable=R0801

.PHONY: fmt
fmt:
	isort ./blackbox/parse_json.py
	isort ./dependency_management/*
	isort ./misc_scripts/
	isort ./release_management/*
	black ./blackbox/parse_json.py
	black ./dependency_management/
	black ./dependency_management/compare_fedora_versions
	black ./dependency_management/set_lower_bounds
	black ./misc_scripts/*.py
	black ./release_management/
	shfmt -l -w .

.PHONY: fmt-travis
fmt-travis:
	isort --diff --check-only ./blackbox/parse_json.py
	isort --diff --check-only ./dependency_management/*
	isort --diff --check-only ./misc_scripts/
	isort --diff --check-only ./release_management/*
	black ./blackbox/parse_json.py --check
	black ./dependency_management/ --check
	black ./dependency_management/compare_fedora_versions --check
	black ./dependency_management/set_lower_bounds --check
	black ./misc_scripts/*.py --check
	black ./release_management/ --check
	shfmt -d .

.PHONY: yamllint
yamllint:
	yamllint --strict .github/workflows/*.yml

.PHONY: shellcheck
shellcheck:
	find . -name '*.sh' | xargs shellcheck --severity=warning
