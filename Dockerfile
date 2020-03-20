FROM debian:stretch

RUN apt-get update \
    && apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    default-jre \
    wget \
    supervisor \
    nano \
    curl \
    pkg-config

RUN mkdir /www && \
    mkdir /www/simulator_app && \
    cd /www

ADD gunicorn.conf /etc/supervisor/conf.d/gunicorn.conf
ADD requirements.txt /www
ADD simulator_app/* /www/simulator_app/
ADD simulator.py /www/

# Install the python dependencies, as given from the repository:
RUN pip3 install --no-cache-dir -r /www/requirements.txt

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN groupadd -g 999 appuser && \
    useradd -r -u 999 -g appuser appuser
USER appuser

ENTRYPOINT ["supervisord"]
