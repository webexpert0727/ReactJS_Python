FROM debian:9

MAINTAINER elikho "elikho.hookcoffee@gmail.com"

ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive
ENV SYSTEM_USER django
ENV SYSTEM_GROUP webapp

RUN apt-get update && apt-get install -y --no-install-recommends \
    nano \
    curl \
    make \
    gosu \
    gnupg2 \
    git-core \
    build-essential \
    libtool \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libevent-dev \
    libssl-dev \
    libbz2-dev \
    libreadline-dev \
    libmagic-dev \
    libncurses-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libopenblas-dev \
    liblapack-dev \
    libgeoip-dev \
    openssl \
    gfortran \
    gettext \
    python-pip \
    python-dev \
    python-numpy \
    locales \
    # vim net-tools htop
    && rm -rf /var/lib/apt/lists/*

RUN localedef -i en_US -c -f UTF-8 en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

RUN curl -sL https://deb.nodesource.com/setup_8.x | bash - && \
    curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - && \
    echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends nodejs yarn && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -r $SYSTEM_GROUP -g 1000 && \
    useradd -u 1000 -r -g $SYSTEM_GROUP -m -d /var/www $SYSTEM_USER && \
    chown -R $SYSTEM_USER:$SYSTEM_GROUP /var/www

RUN yarn global add bower postcss-cli autoprefixer && \
    yarn cache clean

RUN bash -c 'mkdir -p /var/www/{env,src,logs,generated/{addresses,labels},assets/{media,static}}'

RUN pip install --no-cache-dir virtualenv && \
    /usr/local/bin/virtualenv /var/www/env && \
    chown -R $SYSTEM_USER:$SYSTEM_GROUP /var/www

COPY ./requirements /var/www/src/requirements

ARG REQUIREMENTS=base
RUN gosu $SYSTEM_USER bash -c "\
    source /var/www/env/bin/activate && \
    pip install --no-cache-dir -r /var/www/src/requirements/${REQUIREMENTS}.txt"

COPY .babelrc package.json yarn.lock webpack* /var/www/src/
COPY frontend /var/www/src/frontend
COPY static/fonts /var/www/src/static/fonts

WORKDIR /var/www/src

ARG BUILD_ENV=production
RUN set -ex; \
    yarn install --pure-lockfile; \
    yarn run build; \
    if [ "$BUILD_ENV" = "production" ]; then \
        yarn cache clean && rm -rf node_modules; \
    fi

COPY ./services/app/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

COPY . /var/www/src/
RUN chown -R $SYSTEM_USER:$SYSTEM_GROUP /var/www/src

RUN gosu $SYSTEM_USER bash -c "\
        source /var/www/env/bin/activate && \
        python manage.py bower install"

VOLUME ["/var/www/assets", "/var/www/logs"]

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]

CMD ["gunicorn", "giveback_project.wsgi:application"]
