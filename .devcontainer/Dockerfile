FROM ubuntu:latest

RUN apt update && \
    apt install -y \
        locales \
        language-pack-en \
        ruby-full \
        npm && \
    gem install bundler

# The posts use Unicode characters, so we need to configure a UTF-8 locale
RUN \
    locale-gen en_US.utf8 && \
    update-locale LANG=en_US.utf8
ENV LANG=en_US.utf8
