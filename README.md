# qq-bot
A bot on Tencent QQ that provides services in mathematics and rhythm games group chats based on [CoolQ](https://cqp.cc).

## Functionalities

The bot supports:
 - Repeating (this is a phenomenon in certain subcultural groups that tend to repeat random messages)
 - Symbolic computation via `sympy`
 - Ordinal computation
 - LaTeX rendering
 - Miscellaneous memes in rhythm game culture

## Dependencies

This program requires:
 - cqhttp
 - celery
 - redis (both the executable and the python library)
 - numpy
 - sympy
 - pinyin

## Startup

To start the bot, first start up redis using the config file (currently it is just a copy of the default config with annotations) by `redis-server redis.conf`. Then start Celery by `celery -A celery_config worker --loglevel=info`. At last start the main uwsgi server with `uwsgi --http 127.0.0.1:8099 --wsgi-file cq.py --callable application --processes 3 --threads 2 --harakiri 30 --stats 127.0.0.1:9191`.

## Basic Framework

Since I only own a Mac, it is a bit complicated to get CoolQ running. I set up a virtual machine running Windows 7, installed the main components on the virtual machine, and set up [a service](https://cqhttp.cc/) (available on the CoolQ BBS) that reports events and provides an API via HTTP requests. The service is then directly connected to the host machine. I decided to put the main code on the host machine for ease of management. This is written in Python using a framework provided by the developers of the CoolQ HTTP service. There is also a small part of the code on the virtual machine (I know it's complicated and perhaps bad practice, making it open source is also a way to help me improve this), that guards a [program](http://www.mtnmath.com/ord_0_3_1/ordinal.pdf) that does ordinal number computations. If a message is sent in a group chat requesting for some computation, it is first sent to the CoolQ program on the virtual machine, and by the HTTP service sent to the host machine running the main code, and then sent to the guardian service on the virtual machine (since it seems that the ordinal calculator only supports Windows).
I do not want to put a LaTeX distribution in my small virtual machine, so the main code has to be on the host.

## Further developments

 - It is requested that a type checker (for system F? MLTT?) be included.
 - It is requested that (at least the safe version of) Haskell compiling be included.
 - The code is actually very messy.

Anyone can request features in the issues!

## Acknowledgements

Many thanks to [@ice-1000](https://github.com/ice1000) who generously paid for the Pro functionalities of CoolQ.

