FROM alpine:3.12.4

RUN apk --no-cache -U add \
    docker \
    git \
    openjdk8 \
    py-pip \
    python3

RUN pip3 install garminconnect
RUN pip3 install pyyaml