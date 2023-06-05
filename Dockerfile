# ishiki-tf-epaper Dockerfile

# docker run -it --name ishiki-tf-epaper pisuke/ishiki-tf-epaper:latest

FROM pisuke/ishiki-base:latest

RUN [ "cross-build-start" ]

RUN apt-get update
RUN apt-get install -y python3-setuptools
RUN apt-get install -y python3-pip

# copy files to container
COPY requirements.txt requirements.txt
COPY ishiki-tf-epaper.py ishiki-tf-epaper.py
COPY font/ font/
COPY img/ img/

# install dependencies
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt

# run the display command
CMD ["python3", "ishiki-tf-epaper.py"]

RUN [ "cross-build-end" ]
