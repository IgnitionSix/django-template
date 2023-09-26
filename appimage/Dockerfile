FROM python:3
ENV PYTHONUNBUFFERED 1
ENV NODE_VERSION=18.17.1
WORKDIR /code
RUN apt install -y curl
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
ENV NVM_DIR=/root/.nvm
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}
ENV PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"
ENV PATH="${PATH}:/home/python/.local/bin"
RUN node --version
RUN npm --version

COPY baseapp/requirements*.txt ./

RUN pip install -r requirements.txt

COPY ./baseapp /code/baseapp

WORKDIR /code/

#For some reason, django-tailwind doesn't install packages to a place that django can find them, so we'll do it manually
RUN npm install cross-env postcss postcss-loader postcss-import postcss-cssnext postcss-simple-vars postcss-nested

CMD ["/bin/sh","-c","./baseapp/run.sh"]