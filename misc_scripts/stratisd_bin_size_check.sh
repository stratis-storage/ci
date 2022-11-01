#!/bin/bash
set -e

urls=(
	https://kojipkgs.fedoraproject.org/packages/stratisd/2.0.0/2.fc32/x86_64/stratisd-2.0.0-2.fc32.x86_64.rpm
	https://kojipkgs.fedoraproject.org/packages/stratisd/2.0.1/2.fc33/x86_64/stratisd-2.0.1-2.fc33.x86_64.rpm
	https://kojipkgs.fedoraproject.org/packages/stratisd/2.1.0/3.fc33/x86_64/stratisd-2.1.0-3.fc33.x86_64.rpm
	https://kojipkgs.fedoraproject.org/packages/stratisd/2.3.0/8.fc34/x86_64/stratisd-2.3.0-8.fc34.x86_64.rpm
	https://kojipkgs.fedoraproject.org/packages/stratisd/2.4.0/3.fc34/x86_64/stratisd-2.4.0-3.fc34.x86_64.rpm
	https://kojipkgs.fedoraproject.org/packages/stratisd/2.4.1/1.fc35/x86_64/stratisd-2.4.1-1.fc35.x86_64.rpm
	https://kojipkgs.fedoraproject.org/packages/stratisd/2.4.2/3.fc36/x86_64/stratisd-2.4.2-3.fc36.x86_64.rpm
	https://kojipkgs.fedoraproject.org/packages/stratisd/2.4.3/1.fc34/x86_64/stratisd-2.4.3-1.fc34.x86_64.rpm
)

for url in "${urls[@]}"; do
	echo "$url"
	curl -O $url
done

rpms=$(ls *.rpm)

for rpm in $rpms; do
	echo "$rpm"
	rpm2cpio $rpm | cpio -tv 2>&1 | sort -k5 -n -r | head -5
	echo
done
