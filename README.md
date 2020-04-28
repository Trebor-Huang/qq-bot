Mirai is a wonderful QQ-bot backend, and I'm going to abandon CoolQ soon (like, as soon as mirai goes to version 1.0.0). The instructions here will no longer be updated, until I migrate completely to mirai.

# qq-bot
A bot on Tencent QQ that provides services in mathematics and rhythm games group chats based on [CoolQ](https://cqp.cc).

## Functionalities

The bot supports:
 - Repeating (this is a phenomenon in certain subcultural groups that tend to repeat random messages)
 - Symbolic computation via `sympy`
 - LaTeX rendering
 - Random banning (bans the user on his/her own request)
 - Brainf**k interpreter
 - Haskell compiler
 - Coq interactive environment
 - Miscellaneous memes in rhythm game culture

## Dependencies

This program requires:
 - cqhttp
 - celery
 - redis (both the executable and the python library)
 - Some LaTeX distribution
 - numpy
 - sympy
 - pinyin
 - imagemagick

## Setup

TODO.

## Startup

To start the bot, first start up redis using the config file (currently it is just a copy of the default config with annotations) by `redis-server redis.conf`. Then start Celery by `celery -A celery_config worker --loglevel=info`. Start the Coq hosting server by directly running `coq_server.py`. At last start the main uwsgi server with `uwsgi --http 127.0.0.1:8099 --wsgi-file cq.py --callable application --processes 3 --threads 5 --harakiri 15 --stats 127.0.0.1:9191`.
Change the ip addresses as you wish.

## Further developments

 - It is requested that a type checker (for system F? MLTT?) be included.
 - The code is actually very messy.

Anyone can request features in the issues!
