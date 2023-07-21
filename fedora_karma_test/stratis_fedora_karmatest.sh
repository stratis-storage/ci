#!/bin/bash
set -e
set -x

for repo in stratisd devicemapper-rs libcryptsetup-rs libblkid-rs; do
	echo $repo
	git clone https://github.com/stratis-storage/$repo
	cd $repo
	if [ $repo != 'stratisd' ]; then
		make clippy
		make fmt-ci
		make build
	else
		make clippy
		make fmt-ci
		make build-all-rust
	fi
	cd ..
done

echo "All tests completed."
