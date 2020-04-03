import os, time, requests, re, redis, brainfuck
import sympy
from sympy.parsing.sympy_parser import parse_expr
from celery_config import app
from celery.exceptions import SoftTimeLimitExceeded

pattern = re.compile(r"(.+)\n    =+")
whitelist = ['abs',
 'all',
 'any',
 'ascii',
 'bin',
 'divmod',
 'hex',
 'iter',
 'max',
 'min',
 'next',
 'oct',
 'pow',
 'round',
 'sorted',
 'None',
 'True',
 'bool',
 'complex',
 'dict',
 'enumerate',
 'filter',
 'float',
 'frozenset',
 'int',
 'list',
 'map',
 'range',
 'reversed',
 'set',
 'slice',
 'tuple',
 'type',
 'zip']
blacklist = ['__version__',
 '__sympy_debug',
 'SYMPY_DEBUG',
 'external',
 'cache',
 'cacheit',
 'Lambda',
 'codegen',
 'printing',
 'Id',
 'plot',
 'textplot',
 'plot_backends',
 'plot_implicit',
 'plot_parametric',
 'pager_print',
 'pretty',
 'pretty_print',
 'pprint',
 'pprint_use_unicode',
 'pprint_try_use_unicode',
 'print_latex',
 'print_mathml',
 'print_python',
 'print_code',
 'print_glsl',
 'print_fcode',
 'print_rcode',
 'print_jscode',
 'print_gtk',
 'preview',
 'print_tree',
 'StrPrinter',
 'dotprint',
 'print_maple_code',
 'interactive',
 'init_session',
 'init_printing',
 'deprecated',
 'class_registry',
 'C',
 'ClassRegistry']

calc_dict = {d:sympy.__dict__[d] for d in sympy.__dict__ 
  if (d not in __builtins__ or d in whitelist) or d not in blacklist}

def foolsopen(*args, **kwargs):
    class foolFile:
        def read(self, *args):
            return "坏耶"
        def write(self, *args):
            return -114514
        def readline(self, *args):
            return "坏耶"
        def readlines(self, *args):
            return ["坏", "耶"]
        def writeline(self, *args):
            return -114514
        def writelines(self, *args):
            return -114514
        def closed(self):
            return True
        def close(self):
            return "好耶"
    return foolFile()

fools_dict = {
    "eval" : lambda _: "坏耶",
    "compile" : lambda _: "坏耶",
    "open" : foolsopen,
}

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

def timeout_record(user_id, amount = 10000):
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    ex = int(r.incr("timeout" + str(user_id), amount))
    if ex < 30000:
        r.expire("timeout" + str(user_id), int(3600 * 3 ** (ex/10000)))
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
    definitions += "\n\\newcommand{\\R}{\\mathbb R}\n\\newcommand{\\Q}{\\mathbb Q}\n\\newcommand{\\Z}{\\mathbb Z}\n\\newcommand{\\N}{\\mathbb N}\n\\newcommand{\\e}{\\mathrm e}\n"
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
        bot.send(event=event, message=f"[CQ:at,qq={event['user_id']}]\n[CQ:image,file=file:///G:\\{filename}.jpeg]", auto_escape=False, at_sender=True)
        return ("Success", (r, os.system("rm ./img/*.jpeg")))
    except RuntimeError as e:
        bot.send(event=event, message="LaTeX有误", at_sender=True)
        try:
            bot.send_private_msg(user_id=event['user_id'], message=event['message'])
            bot.send_private_msg(user_id=event['user_id'], message = "错误如下：\n" + str(e).strip(), auto_escape=True)
        except Exception:
            bot.send(event, message="似乎你不允许陌生人私聊，这样我发送不了错误诶", at_sender=True)
        try:
            bot.delete_msg(message_id=event['message_id'])
        except Exception:
            pass
        return ("Fail",)
    except SoftTimeLimitExceeded:
        os.system("rm *.tex *.aux *.log *.pdf *.jpeg")
        bot.send(event, f"[CQ:at,qq={event['user_id']}]\nTLE~qwq")
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

@app.task(soft_time_limit=15, time_limit=20)
def calc_sympy(comm, event):
    try:
        if '^' in comm:
            bot.send(event, message="^是异或的符号，**是幂，你确定吗？")
        if not all([c <= '\xFF' for c in comm]):
            bot.send(event, message="只准用ascii字符，够用的quq")
            return
        if '"' in comm or "'" in comm:
            bot.send(event, message=comm)
            timeout_record(event['user_id'])
            return
        res = parse_expr(comm[4:].strip(), global_dict=calc_dict, local_dict=fools_dict)
        message = clamp(str(res), l=20000 if event['message_type'] == 'private' else 200)
        message = message.replace("[", "&#91;").replace("]", "&#93;").replace("&", "&amp;")
        return bot.send(event, f"[CQ:at,qq={event['user_id']}]\n" + message, auto_escape=False)
    except SoftTimeLimitExceeded:
        bot.send(event, f"[CQ:at,qq={event['user_id']}]\nTLE~qwq", auto_escape=False)
        timeout_record(event['user_id'])
        return ("Timeout", event['user_id'])
    except Exception as e:
        return bot.send(event, f'\n报错了qaq: {str(type(e))}\n{clamp(str(e))}', auto_escape=True)

@app.task
def run_bf(event, code, inp=""):
    r, g = brainfuck.run(code, inp, 10000)
    if g == 0:
        bot.send(event, "TLE!", at_sender=True)
    bot.send(event, "结果为:\n" + r, auto_escape=True, at_sender=True)
    timeout_record(event['user_id'], 10000 - g)
    return g, inp

if __name__ == "__main__":
    print(latexify(r"你好！$\displaystyle \int_{-\infty}^\infty e^{-x^2} = \sqrt{\pi}.$Yes.", "test", verbose=False))
