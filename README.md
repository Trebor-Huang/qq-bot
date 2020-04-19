# QQ bot

## Building instructions

TODO

## Starting instructions

 - Start mirai with `docker run --interactive --rm -p 8080:8080 -v $(pwd)/mirai-dockerized/mirai:/mirai -w /mirai mirai:latest`, and type `login [QQ] [QQ Password]`.
 - Start redis with `redis-server redis.conf`
 - `cd backend`
 - Start the bot by executing `bot.py` *in the `backend` directory*
