FEDORA_RELEASE=37
build:
	podman build . \
        --file Containerfile-tang \
        --tag ghcr.io/stratis-storage/stratisd/tang:${FEDORA_RELEASE}

GITHUB_USERNAME ?=
GITHUB_API_KEY ?=
test-creds:
	echo "Testing that GITHUB_USERNAME and GITHUB_API_KEY environment variables are non-empty"
	@test "${GITHUB_USERNAME}"
	@test "${GITHUB_API_KEY}"

push: test-creds
	podman push \
        --creds=${GITHUB_USERNAME}:${GITHUB_API_KEY} \
        ghcr.io/stratis-storage/stratisd/tang:${FEDORA_RELEASE}
