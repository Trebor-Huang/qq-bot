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

I run CoolQ on a virtual machine, so some of the setup may not be necessary for Windows users. Also, the commands used may need to be translated to a Windows equivalent.

First get a CoolQ Pro account (which needs a subscription fee) on [CoolQ](cqp.cc), download the CoolQ software, together with the [CoolQ HTTP plugin](https://cqhttp.cc/). Install the plugin as instructed.

Then, set up the connections properly, by sorting out the ip's and ports parameters in the program config. My CoolQ HTTP plugin reports events at `host.docker.internal:8099`, and receives API requests at `5700` port, since the whole thing runs in the virtual machine. The reported events will be sent by Virtualbox to the `8099` port on the host machine, and the API requests' address is `192.168.56.101:5700`. If you are on Windows, just use localhost as the ip address. As long as the ports align up, you can do whatever you like. These settings are in the config file of CoolQ HTTP, `cq.py`, `tasks.py` and the startup command.

The temporary images generated is stored at `./img`, not included in the repo. Virtualbox syncs the content in the `./img` folder to `G:\` in the virtual machine. So you may want to change that.

## Startup

To start the bot, first start up redis using the config file (currently it is just a copy of the default config with annotations) by `redis-server redis.conf`. Then start Celery by `celery -A celery_config worker --loglevel=info`. At last start the main uwsgi server with `uwsgi --http 127.0.0.1:8099 --wsgi-file cq.py --callable application --processes 3 --threads 5 --harakiri 15 --stats 127.0.0.1:9191`.
Change the ip addresses as you wish.

## Further developments

 - Currently sympy has ways to start up matplotlib, which will make uwsgi crash.
 - It is requested that a type checker (for system F? MLTT?) be included.
 - It is requested that (at least the safe version of) Haskell compiling be included.
 - The code is actually very messy.

Anyone can request features in the issues!

## Acknowledgements

Due to a series of sad events that slowly sinked in, the acknowledgement is regretfully removed.

