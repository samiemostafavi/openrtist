#!/bin/bash


# Remove the existing config file if it exists
if [ -f src/openrtist/config.py ]; then
    rm src/openrtist/config.py
fi

# Write the Python configuration to the specified file
cat <<EOL > src/openrtist/config.py
PORT = 9099
STYLE_DISPLAY_INTERVAL = 300
CAM_FPS = ${FPS:-"30"}
IMG_WIDTH = ${IMG_WIDTH:-"1024"}
IMG_HEIGHT = ${IMG_HEIGHT:-"768"}
START_STYLE_STRING = "udnie"
SOURCE_NAME = "openrtist"
EOL

sh -c './src/openrtist/sinfonia_wrapper.py -v ./Big_Buck_Bunny_1080_10s_5MB.mp4 -c $SERVER -o $OUTPUT_ADDR --quiet True -u $DURATION'

sleep infinity
