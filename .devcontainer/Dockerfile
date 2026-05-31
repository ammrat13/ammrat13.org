FROM ubuntu:noble
ARG BUNDLER_VERSION=2.5.22

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
RUN \
    locale-gen en_US.utf8 && \
    update-locale LANG=en_US.utf8
ENV LANG=en_US.utf8
