#all:
#	docker run -d --rm -p 5000:8080 cloudproj
#
#build:
#	docker build -t cloudproj .

all:

scp:
	scp -r -P 2022 . root@localhost:/app/

ssh:
	ssh -p 2022 root@localhost