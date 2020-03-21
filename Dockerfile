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

COPY supervisord.conf /etc/supervisor/alt.conf
COPY gunicorn.conf /etc/supervisor/conf.d/gunicorn.conf
COPY requirements.txt /www
COPY wsgi.py /www
COPY simulator_app/ /www/simulator_app/
COPY simulator.py /www/

# Install the python dependencies, as given from the repository:
RUN pip3 install --no-cache-dir -r /www/requirements.txt

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN groupadd -g 1001 appuser && \
    useradd -l -u 1000 -g appuser appuser
RUN chown --changes --silent --no-dereference --recursive --from 0:0 1000:1001 /usr/bin/supervisord /var/log/supervisor

RUN touch /var/log/gunicorn.nx.log && chown appuser:appuser /var/log/gunicorn.nx.log /var/run /run
RUN chown -R appuser:appuser /www

USER appuser

ENTRYPOINT ["/bin/bash"]
