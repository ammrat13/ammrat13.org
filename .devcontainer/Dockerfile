FROM ubuntu:resolute
ARG BUNDLER_VERSION=4.0.12

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        locales \
        language-pack-en \
        build-essential \
        ruby-full \
        npm && \
    rm -rf /var/lib/apt/lists/* && \
    gem install bundler --version ${BUNDLER_VERSION} --no-document

# The posts use Unicode characters, so we need to configure a UTF-8 locale
ENV LC_ALL=en_US.utf8
ENV LANG=en_US.utf8
ENV LANGUAGE=en_US.utf8
