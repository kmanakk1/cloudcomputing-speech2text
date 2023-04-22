all:
	docker run -d --rm -p 5000:8080 cloudproj

build:
	docker build -t cloudproj .