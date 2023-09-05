FROM python:3
ENV PYTHONUNBUFFERED 1
WORKDIR /code
COPY ./baseapp/requirements.txt /code/
RUN pip install -r requirements.txt
COPY ./baseapp /code/baseapp
CMD ["/bin/sh","-c","./baseapp/run.sh"]