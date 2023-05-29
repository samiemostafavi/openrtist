FROM python:3.7

RUN echo "deb http://ppa.launchpad.net/intel-opencl/intel-opencl/ubuntu bionic main" >> /etc/apt/sources.list \
 && echo "deb https://apt.repos.intel.com/openvino/2019/ all main" >> /etc/apt/sources.list \
 && curl https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS-2019.PUB | apt-key add - \
 && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys B9732172C4830B8F \
 && apt-get update && apt-get install -y \
    build-essential \
    clinfo \
    intel-opencl-icd \
    intel-openvino-dev-ubuntu18-2019.3.344 \
    libgtk-3.* \
    libsm6 \
    libxext6 \
    libxrender1 \
    ocl-icd-libopencl1 \
 && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Prevent NVIDIA libOpenCL.so from being loaded
#RUN mv /usr/local/cuda-11.8/targets/x86_64-linux/lib/libOpenCL.so.1 /usr/local/cuda-11.8/targets/x86_64-linux/lib/libOpenCL.so.1.bak

RUN mkdir /service
ADD . /service
RUN pip install poetry
WORKDIR /service
RUN POETRY_VIRTUALENVS_CREATE=false poetry install --only main
RUN chmod +x /service/entrypoint.sh
EXPOSE 5555 9099
ENTRYPOINT ["/service/entrypoint.sh"]
