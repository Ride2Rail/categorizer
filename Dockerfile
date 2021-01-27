# base image
FROM python:3.8.2

# set maintainer (MAINTAINER is deprecated)
# See:
#   https://docs.docker.com/engine/reference/builder/#maintainer-deprecated
LABEL maintainer="cristian.consonni@eurecat.org"

# upgrade pip
RUN pip3 install --no-cache-dir --upgrade pip

# add user 'app'
RUN useradd -m app

# set work directory to /home/app
WORKDIR /home/app

# copy requirements to /home/app/requirements.txt
COPY --chown=app:app requirements.txt* requirements.txt

# copy categorizer.py to /home/app/categorizer.py
COPY --chown=app:app ./app /home/app/

# copy directory with protobuf definitions
COPY --chown=app:app ./proto/r2r /home/app/r2r

# install requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# switch to 'app' user
USER app:app

ENV PYTHONUNBUFFERED=1

# exec categorizer.py as entrypoint
CMD ["python3", "/home/app/main.py"]
