FROM debian:testing

ARG USER_NAME=latex
ARG USER_HOME=/home/latex
ARG USER_ID=1000
ARG USER_GECOS=LaTeX

RUN adduser \
  --home "$USER_HOME" \
  --uid $USER_ID \
  --gecos "$USER_GECOS" \
  --disabled-password \
  "$USER_NAME"

ARG WGET=wget
ARG GIT=git
ARG SSH=openssh-client
ARG MAKE=make
ARG PANDOC=pandoc
ARG PCITEPROC=pandoc-citeproc
ARG PYGMENTS=python3-pygments
ARG FIG2DEV=fig2dev
ARG JRE=default-jre-headless

RUN apt-get update --assume-yes
RUN apt install apt-transport-https ca-certificates --assume-yes
COPY sources.list /etc/apt/
RUN apt-get update --assume-yes

RUN apt-get install -y \
  texlive-full \
  # some auxiliary tools
  "$WGET" \
  "$GIT" \
  "$SSH" \
  "$MAKE" \
  # markup format conversion tool
  "$PANDOC" \
  "$PCITEPROC" \
  # XFig utilities
  "$FIG2DEV" \
  # syntax highlighting package
  "$PYGMENTS" \
  # Java runtime environment (e.g. for arara)
  "$JRE" && \
  # Removing documentation packages *after* installing them is kind of hacky,
  # but it only adds some overhead while building the image.
  apt-get --purge remove -y .\*-doc$ && \
  # Remove more unnecessary stuff
  apt-get clean -y

WORKDIR /home/latex
ENTRYPOINT ulimit -t 30 && xelatex -interaction nonstopmode -halt-on-error texput.tex
# docker run -m 1GB -v /Users/trebor/Desktop/coolq/latex/texput.tex:/home/latex/texput.tex --name latex_container treborhuang/latex --rm
# docker cp latex_container:/home/latex/ ./
