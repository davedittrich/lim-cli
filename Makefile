# Makefile for lim

SHELL:=bash
VERSION:=19.8.2
CWD:=$(shell pwd)
ifeq ($(VIRTUAL_ENV), '')
  ENVNAME:="env"
else
  ENVNAME:=$(shell basename $(VIRTUAL_ENV) 2>/dev/null || echo "")
endif
PROJECT:=$(shell basename $(CWD))

all: help
help:
	@echo 'usage: make [VARIABLE=value] [target [target..]]'
	@echo ''
	@echo 'test - generic target for both "test-tox" and "test-bats"'
	@echo 'test-tox - run tox tests'
	@echo 'test-bats - run Bats unit tests'
	@echo 'test-bats-runtime - run Bats runtime integration/system tests'
	@echo 'release - produce a pypi production release'
	@echo 'release-test - produce a pypi test release'
	@echo 'egg - run "python setup.py bdist_egg"'
	@echo 'wheel - run "python setup.py bdist_wheel"'
	@echo 'sdist - run "python setup.py sdist"'
	@echo 'twine-check - run "twine check"'
	@echo 'install - install pip package'
	@echo 'install-active - run "python -m pip install -U ."'
	@echo 'docs-tests - generate bats test output for documentation'
	@echo 'docs - build Sphinx docs'



#HELP test - run 'tox' for testing
.PHONY: test
test: test-tox test-bats docs-tests
	@echo '[+] All tests succeeded'

.PHONY: test-tox
test-tox:
	@if [ -f .python_secrets_environment ]; then (echo '[!] Remove .python_secrets_environment prior to testing'; exit 1); fi
	tox

.PHONY: test-bats
test-bats: bats-libraries
	@if [ "$(TRAVIS)" != "true" ]; then \
		if ! type bats 2>/dev/null >/dev/null; then \
			echo "[-] Skipping bats tests"; \
		else \
			echo "[+] Running bats tests: $(shell cd tests && echo [0-9][0-9]*.bats)"; \
			bats --tap tests/[0-9][0-9]*.bats; \
		fi \
	 fi

.PHONY: test-bats-runtime
test-bats-runtime: bats-libraries
	bats --tap tests/runtime.bats

.PHONY: no-diffs
no-diffs:
	@echo 'Checking Git for uncommitted changes'
	git diff --quiet HEAD

#HELP release - package and upload a release to pypi
.PHONY: release
release: clean docs-tests docs-help docs sdist test twine-check
	$(MAKE) no-diffs
	twine upload dist/* -r pypi

#HELP release-test - upload to "testpypi"
.PHONY: release-test
release-test: clean docs-tests docs-help docs sdist test twine-check
	$(MAKE) no-diffs
	twine upload dist/* -r testpypi

#HELP egg - build an egg package
.PHONY: egg
egg:
	rm -f dist/.LATEST_EGG
	python setup.py bdist_egg
	(cd dist && ls -t *.egg 2>/dev/null | head -n 1) > dist/.LATEST_EGG
	ls -lt dist/*

#HELP wheel - build a wheel package
.PHONY: wheel
wheel:
	rm -f dist/.LATEST_WHEEL
	python setup.py bdist_wheel
	(cd dist && ls -t *.whl 2>/dev/null | head -n 1) > dist/.LATEST_WHEEL
	ls -lt dist/*.whl

#HELP sdist - build a source package
.PHONY: sdist
sdist: docs
	rm -f dist/.LATEST_TARGZ
	python setup.py sdist
	(cd dist && ls -t *.tar.gz 2>/dev/null | head -n 1) > dist/.LATEST_TARGZ
	ls -lt dist/*.tar.gz

#HELP twine-check
.PHONY: twine-check
twine-check: egg
	twine check "$(shell cat dist/.LATEST_EGG)"

#HELP clean - remove build artifacts
.PHONY: clean
clean:
	rm -f ctu*-cache.json
	rm -rf dist build *.egg-info
	find . -name '__pycache__' -delete
	find . -name '*.pyc' -delete

#HELP spotless - deep clean
.PHONY: spotless
spotless: clean
	rm -rf .eggs .tox
	(cd docs && make clean)
	rm -rf tests/libs/{bats,bats-support,bats-assert}

#HELP install - install in required Python virtual environment (default $(REQUIRED_VENV))
.PHONY: install
install:
	@if [ ! -d $(VENV_DIR) ]; then \
		echo "Required virtual environment '$(REQUIRED_VENV)' not found."; \
		exit 1; \
	fi
	@if [ ! -e "$(VENV_DIR)/bin/python" ]; then \
		echo "Cannot find $(VENV_DIR)/bin/python"; \
		exit 1; \
	else \
		echo "Installing into $(REQUIRED_VENV) virtual environment"; \
		$(VENV_DIR)/bin/pip uninstall -y $(PROJECT); \
		$(VENV_DIR)/bin/python setup.py install; \
	fi
	$(MAKE) docs-help

#HELP install-active - install in the active Python virtual environment
.PHONY: i
.PHONY: install
i install-active: wheel
	python -m pip install -U "dist/$(shell cat dist/.LATEST_WHEEL)"
	$(MAKE) docs-help

.PHONY: install-instance
install-instance: wheel
	if ssh xgt true 2>/dev/null; \
	then \
		scp dist/$(shell cat dist/.LATEST_WHEEL) xgt:; \
		ssh xgt sudo -H python3 -m pip install -U $(shell cat dist/.LATEST_WHEEL); \
	fi

#HELP docs-tests - generate bats test output for documentation
.PHONY: docs-tests
PR=pr --omit-header --omit-pagination --page-width 80
docs-tests:
	(echo '$$ make test-tox' && $(MAKE) test-tox) |\
	       $(PR) | tee docs/test-tox.txt
	$(MAKE) test-bats | $(PR) | tee docs/test-bats.txt
	(echo '$$ make test-bats-runtime' && $(MAKE) test-bats-runtime) |\
	       $(PR) | tee docs/test-bats-runtime.txt

#HELP docs-help - generate "lim help" output for documentation
.PHONY: docs-help
docs-help:
	(unset LIM_DATA_DIR; \
	 python -m lim.main help |\
		sed 's/lim.main/lim/g' |\
		sed 's/main.py/lim/g') > docs/lim-help.txt

#HELP docs - build Sphinx docs (NOT INTEGRATED YET FROM OPENSTACK CODE BASE)
.PHONY: docs
docs:
	(cd docs && make clean html)

#HELP examples - produce some example output for docs
.PHONY: examples
examples:
	lim --help

# Git submodules and subtrees are both a huge PITA. This is way simpler.

.PHONY: bats-libraries
bats-libraries: bats bats-support bats-assert

bats:
	@[ -d tests/libs/bats ] || \
		(mkdir -p tests/libs/bats; git clone http://github.com/sstephenson/bats tests/libs/bats)


bats-support:
	@[ -d tests/libs/bats-support ] || \
		(mkdir -p tests/libs/bats-support; git clone https://github.com/ztombol/bats-support tests/libs/bats-support)

bats-assert:
	@[ -d tests/libs/bats-assert ] || \
		(mkdir -p tests/libs/bats-assert; git clone https://github.com/ztombol/bats-assert tests/libs/bats-assert)

#EOF
