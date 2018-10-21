# Multidropbox
## Run dropbox in docker with app status indicators. Run multiple instances at once

### Build the dropbox docker image
`docker build -f --tag docker-dropbox docker-dropbox/Dockerfile .`
### Run the run-docker-dropbox.sh script
`run-docker-dropbox.py [-h] [--create-instance] [--mount-path MOUNT_PATH] [--image-tag IMAGE_TAG] instance-name`

```
Run dropbox in a docker container. Interrogates container and displays status
as app indicator

positional arguments:
  instance-name         an integer for the accumulator

optional arguments:
  -h, --help            show this help message and exit
  --image-tag IMAGE_TAG
                        Tag of the docker image to run

Create a new instance:
  --create-instance     Create the docker instance (if not created)
  --mount-path MOUNT_PATH
                        Path of the folder to use for this dropbox instance
```