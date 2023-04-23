#all:
#	docker run -d --rm -p 5000:8080 cloudproj
#
#

all: scp

scp:
	scp -r -P 2022 . root@localhost:/app/

ssh:
	ssh -p 2022 root@localhost

docker:
	docker run -dt -p 5000:8080 -p 2022:22 --name cp_dev --entrypoint=/bin/sh cloudproj

build:
	docker build -t cloudproj .