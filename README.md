# CS452: Cloud Computing - Final Project
By: Kaesi Manakkal

In order to run it, first build it:
```sh
$ docker build -t your_image_tag .
```

to run it, you need to set environment variables for the firebase backend:

```sh
$ docker run -p 8080:8080 -e FIREBASE_CRED="$(cat firebase_auth_secret.json | base64 -w 0)" -e FIREBASE_URL="<your_firebase_url_here>" --name cloud_project your_image_tag
 ```