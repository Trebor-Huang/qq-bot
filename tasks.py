import os, time, requests, re, redis
from sympy.parsing.sympy_parser import parse_expr
from celery_config import app
from celery.exceptions import SoftTimeLimitExceeded

pattern = re.compile(r"(.+)\n    =+")
class LittleBot:
    """A small version of the bot that only sends to the http api. This avoids the flask server setup and so can be jsonified."""
    def __init__(self, api_root):
        self.api_root = api_root

    def send(self, event, message, **kwargs):
        params = event.copy()
        params['message'] = message
        params.pop('raw_message', None)  # avoid wasting bandwidth
        params.pop('comment', None)
        params.pop('sender', None)
        params.update(kwargs)
        if 'message_type' not in params:
            if 'group_id' in params:
                params['message_type'] = 'group'
            elif 'discuss_id' in params:
                params['message_type'] = 'discuss'
            elif 'user_id' in params:
                params['message_type'] = 'private'
        return self.send_msg(**params)

    def __getattr__(self, item):
        def do_call(**kwargs):
            resp = requests.post(self.api_root + item, json=kwargs, headers={})
            if resp.ok:
                data = resp.json()
                if data.get('status') == 'failed':
                    raise RuntimeError(resp.status_code, data.get('retcode'))
                return data.get('data')
            raise RuntimeError(resp.status_code)
        return do_call

bot = LittleBot('http://192.168.56.101:5700/')

def timeout_record(user_id):
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    ex = int(r.incr("timeout" + str(user_id)))
    if ex < 3:
        r.expire("timeout" + str(user_id), 3600 * 3 ** ex)
    r.close()

def clamp(s, l=200):
    if len(s) > l:
        return s[:l] + " ..."
    return s

def latexify(source, filename, size=512, verbose=False, **preamble):
    tempfilename = "TEMP" + hex(hash(source) ^ time.time_ns())[1:]
    with open(f"{tempfilename}.tex", "w") as file:
        file.write(get_preamble(**preamble) + source + "\n\\end{document}")
    if r := os.system(f"gtimeout 29s xelatex -interaction nonstopmode -halt-on-error {tempfilename}.tex  > /dev/null"):
        print(r)
        if r == 124 or r == 128+9 or r == 31744:
            time.sleep(15)
        with open(f"{tempfilename}.log", "r") as file:
            error = file.read()
        raise RuntimeError(error[error.find("\n!"):error.find("Here is how much of")])
    r1 = os.system(f"convert -density {size*4} {tempfilename}.pdf {tempfilename}.jpeg")
    r2 = os.system(f"convert {tempfilename}.jpeg -resample {size} {filename}.jpeg")
    r3 = os.system("rm *.tex *.aux *.log *.pdf *.jpeg")
    return r1,r2,r3

def get_preamble(usepackage=None, definitions=""):
    if usepackage is None:
        usepackage = ()
    definitions += "\n\\newcommand{\\R}{\\mathbb R}\n\\newcommand{\\Q}{\\mathbb Q}\n\\newcommand{\\Z}{\\mathbb Z}\n\\newcommand{\\N}{\\mathbb N}\n\\newcommand{\\e}{\\mathrm e}\n\\newcommand{\\d}{\\mathrm d}"
    usepackage += ("amssymb", "amsmath", "amsfonts")
    return r"\documentclass[varwidth,border=2pt]{standalone}" + \
      "\n\\usepackage{" + ", ".join(usepackage) + "}\n\\usepackage{xeCJK}\n" + definitions + "\n\\begin{document}\n"

@app.task(soft_time_limit=30, time_limit=60)
def render_latex_and_send(res, event, latex_packages, resend=False, definitions=None):
    try:
        filename = "TEMP" + hex(hash(res) ^ time.time_ns())[1:]
        r = latexify(res, filename="./img/" + filename, definitions="\\textwidth=7cm" if definitions is None else definitions, usepackage=latex_packages)
        try:
            bot.delete_msg(message_id=event['message_id'])
            if resend:
                bot.send_private_msg(user_id=event['user_id'], message=event['message'])
        except Exception:
            pass
        bot.send(event=event, message=f"[CQ:image,file=file:///G:\\{filename}.jpeg]", auto_escape=False, at_sender=True)
        return ("Success", (r, os.system("rm ./img/*.jpeg")))
    except RuntimeError as e:
        bot.send_private_msg(user_id=event['user_id'], message=event['message'])
        bot.send_private_msg(user_id=event['user_id'], message = "错误如下：\n" + str(e).strip(), auto_escape=True)
        try:
            bot.delete_msg(message_id=event['message_id'])
        except Exception:
            pass
        bot.send(event=event, message="LaTeX有误", at_sender=True)
        return ("Fail",)
    except SoftTimeLimitExceeded:
        os.system("rm *.tex *.aux *.log *.pdf *.jpeg")
        bot.send(event, "TLE~qwq")
        timeout_record(event['user_id'])
        return ("Timeout", event['user_id'])

@app.task
def send_rst_doc(doc, event):
    for i, d in enumerate(pattern.split(doc)):
        bot.send_private_msg(user_id=event['user_id'], message=d + "\n" + ("    " + "="*len(d) if i%2==1 else ""), auto_escape=False)
    return

@app.task
def reject_unfamiliar_group(group_id):
    while True:
        try:
            l = bot.get_group_member_list(group_id=group_id)
            print("Success.")
            break
        except RuntimeError:
            print('Error in getting group members.')
            time.sleep(30)
    if all(u['user_id'] != 2300936257 for u in l):
        bot.send_group_msg(group_id=group_id, message="只有主人Trebor在的群我才能去qaq")
        bot.set_group_leave(group_id=group_id)

@app.task
def calm_down():
    bot.set_group_whole_ban(group_id=80852074)
    time.sleep(30)
    bot.set_group_whole_ban(group_id=80852074, enable=False)

@app.task(soft_time_limit=15, time_limit=20)
def calc_sympy(comm, event):
    try:
        if '^' in comm:
            bot.send(event, message="^是异或的符号，**是幂，你确定吗？")
        if not all([c <= '\xFF' for c in comm]):
            bot.send(event, message="只准用ascii字符，够用的quq")
            return
        res = parse_expr(comm[4:].strip())
        return bot.send(event, clamp(str(res), l=20000 if event['message_type'] == 'private' else 200), auto_escape=True)
    except SoftTimeLimitExceeded:
        bot.send(event, "TLE~qwq")
        timeout_record(event['user_id'])
        return ("Timeout", event['user_id'])
    except Exception as e:
        return bot.send(event, f'报错了qaq: {str(type(e))}\n{clamp(str(e))}', auto_escape=True)

if __name__ == "__main__":
    print(latexify(r"你好！$\displaystyle \int_{-\infty}^\infty e^{-x^2} = \sqrt{\pi}.$Yes.", "test", verbose=False))
