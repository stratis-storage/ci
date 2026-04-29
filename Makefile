.PHONY: lint
lint:
	ruff check
	pyright

.PHONY: fmt
fmt:
	ruff check --fix --select I
	ruff format
	shfmt -l -w .

.PHONY: fmt-travis
fmt-travis:
	ruff check --select I
	ruff format --check
	shfmt -d .

.PHONY: yamllint
yamllint:
	yamllint --strict .github/workflows/*.yml

.PHONY: shellcheck
shellcheck:
	find . -name '*.sh' | xargs shellcheck --severity=warning
