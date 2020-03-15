from celery import Celery

app = Celery('cq', broker='redis://127.0.0.1:6379/0', include=['tasks'])

app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    app.start()