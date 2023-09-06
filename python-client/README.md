# Openrtist_Sinfonia

## Overview
This is the Desktop demo python client for Openrtist.
The backend can be deployed with Sinfonia.


## Dependencies:
The project uses [poetry](https://python-poetry.org/) to manage dependencies. To install all dependencies, [install `poetry`](https://python-poetry.org/docs/#installation) and run the below command:
```bash
poetry install
```

## Usage:
### Run from source code:
```bash
./sinfonia_wrapper.py
```

## Use new features
Load frames from a video file instead of a webcam and end the client session after a certain duration, and save measurements into a json file
```
./src/openrtist/sinfonia_wrapper.py -v ./Big_Buck_Bunny_1080_10s_5MB.mp4 -c $SERVER -o $OUTPUT_ADDR --quiet True -u $DURATION
```

## Build Docker container
```
docker build -t samiemostafavi/openrtist-client . --no-cache
docker image push samiemostafavi/openrtist-client
```

## Use Docker container
```
docker run -it --rm -v .:/tmp/ --net=host -e IMG_WIDTH=180 -e IMG_HEIGHT=90 -e SERVER=openrtist-demo.cmusatyalab.org:9099 -e OUTPUT_ADDR=/tmp/test.json -e DURATION=30 samiemostafavi/openrtist-client
```
