#!/bin/bash
set -e
set -x

for repo in stratisd devicemapper-rs libcryptsetup-rs libblkid-rs; do
	echo $repo
	git clone https://github.com/stratis-storage/$repo
	cd $repo
	case $repo in
	stratisd)
		make clippy
		make fmt-ci
		make build-all-rust
		;;
	libcryptsetup-rs)
		git submodule init
		git submodule update
		make clippy
		make fmt-ci
		make build
		;;
	*)
		make clippy
		make fmt-ci
		make build
		;;
	esac
	cd ..
done

echo "All tests completed."
