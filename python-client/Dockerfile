FROM amd64/python:3.8
ARG DEBIAN_FRONTEND=noninteractive

RUN apt update
RUN apt-get install ffmpeg libsm6 libxext6  -y
#RUN apt-get install -y '^libxcb.*-dev' libx11-xcb-dev libglu1-mesa-dev libxrender-dev libxi-dev libxkbcommon-dev libxkbcommon-x11-dev
#RUN apt-get install libxcb-xinerama0 -y
RUN apt-get install -y build-essential \
    clinfo \
    intel-opencl-icd \
    libgtk-3-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    ocl-icd-libopencl1
RUN apt install git -y
WORKDIR /app

RUN git clone https://github.com/samiemostafavi/openrtist
WORKDIR /app/openrtist/python-client
RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false
RUN poetry install

ENV QT_QPA_PLATFORM=offscreen
RUN chmod +x entrypoint.sh
CMD ["./entrypoint.sh"]
