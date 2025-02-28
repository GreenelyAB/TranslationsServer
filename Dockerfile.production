FROM python:3.10-slim

EXPOSE 5512

RUN mkdir -p /services/TranslationsService/LOGS/

RUN apt-get update
RUN apt-get install -y ca-certificates gpg git libpq-dev gcc openssh-client curl
RUN python -m pip install -U pip

RUN pip3 install --no-cache --upgrade pip setuptools

RUN mkdir -p /etc/apt/keyrings
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
RUN echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" >> /etc/apt/sources.list.d/nodesource.list
RUN apt-get update && apt-get install -y nodejs

RUN npm install npm@latest -g

WORKDIR /app
COPY Gruntfile.js .
COPY package.json .
COPY package-lock.json .

RUN mkdir /node-packages
COPY package.json /node-packages
COPY package-lock.json /node-packages
RUN npm install --prefix=/node-packages

RUN ln -s /node-packages/node_modules /app/node_modules

RUN mkdir -p /root/.ssh/
RUN ssh-keyscan -H github.com >> /root/.ssh/known_hosts

WORKDIR /app/src
COPY requirements.txt .
RUN --mount=type=ssh pip install -r requirements.txt

COPY src/ .

WORKDIR /app/src
