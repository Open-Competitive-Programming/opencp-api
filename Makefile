DOCKER=docker
IMGTAG=opencp/opencp-api:latest

.PHONY: all build push

all: build push

build:
	$(DOCKER) build . -t $(IMGTAG)

push:
	$(DOCKER) push $(IMGTAG)