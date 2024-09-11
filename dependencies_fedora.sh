#!/bin/bash

# Install dependencies for building and testing Stratis on Fedora.
# For clarity, packages are grouped into sections:
# - Base build tools (git, make)
# - Base toolchain (compilers and associated libraries)
# - Core library dependencies (D-Bus, device-mapper, systemd, etc.)
# - Python 3 dependences
dnf -y install git \
	make \
	clang \
	gcc \
	glibc-devel.i686 \
	glibc-devel.x86_64 \
	glibc-static \
	llvm \
	llvm-devel \
	asciidoc \
	clevis \
	clevis-luks \
	cryptsetup-devel \
	dbus-devel \
	dbus-devel.i686 \
	dbus-devel.x86_64 \
	dbus-glib-devel \
	dbus-python-devel \
	device-mapper-devel \
	device-mapper-persistent-data \
	openssl-devel \
	python3-dbus \
	systemd-devel \
	systemd-devel.i686 \
	systemd-devel.x86_64 \
	xfsprogs \
	python3-coverage \
	python3-dateutil \
	python3-justbytes \
	python3-packaging \
	python3-psutil \
	python3-pyparsing \
	python3-pyudev \
	python3-semantic_version \
	python3-setuptools \
	python3-wcwidth \
	python3-isort \
	bandit \
	black
