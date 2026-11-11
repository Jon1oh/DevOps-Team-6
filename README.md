# How to run the program with docker

```powershell
docker load -i ai_scam_detector_image.tar
```
1. Import the docker image.

```powershell
docker images
```
2. Verify the image exists and is loaded.

```powershell
docker volume create scam-db
```

3. Create a persistent docker volume for the program to store its database files.

```powershell
docker run --rm -it -v scam-db:/app/data ai_scam_detector
```
4. Run the application. It will start with an empty database.