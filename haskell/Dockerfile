FROM ubuntu:bionic

RUN apt-get upgrade -y && apt-get update -y
RUN apt install apt-transport-https ca-certificates -y
RUN apt-get update -y
RUN apt install curl gcc -y

RUN apt-get install haskell-platform -y

RUN adduser \
  --home "/haskell" \
  --uid 1000 \
  --gecos "Haskqwq" \
  --disabled-password \
  "haskell"

USER haskell
WORKDIR /haskell
ENV SRC src
ENV IN in
ENV OUT out
ENTRYPOINT ( if [ -f "${SRC}" ]; then echo Cached; else ghc "${SRC}"; fi > "${SRC}.log" 2>&1 ) && ( cat "${IN}.in" | "./${SRC}" > "${OUT}.out" 2>&1 )
# docker run --rm --name haskell --env SRC=src --env IN=in -v $(pwd)/srcfolder:/haskell haskell:latest