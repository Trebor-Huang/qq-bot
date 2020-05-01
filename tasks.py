import os, time, requests, re, redis, brainfuck
import sympy
from sympy.parsing.sympy_parser import parse_expr
from celery_config import app
from celery.exceptions import SoftTimeLimitExceeded
import latexify_docker, haskell_docker
import fcntl
import custom_settings

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

bot = LittleBot(custom_settings.CQHTTP_API)

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

@app.task(soft_time_limit=70, time_limit = 90)
def docker_latex(src, resend, event, ismath=False):
    pkgs = ()
    defs = ""
    if src[:22] == "\\begin{bot-usepackage}":
        src = src[22:]
        pkg, src = src.split("\\end{bot-usepackage}")
        pkgs = tuple(pkg.split())
    if src[:16] == "\\begin{bot-defs}":
        src = src[16:]
        defs, src = src.split("\\end{bot-defs}")
    if ismath:
        src = "\\( \\displaystyle " + src + "\\)"
    src_ltx = latexify_docker.get_source(src, pkgs, defs)
    r, rets, l = latexify_docker.compile_latex(src_ltx)
    try:
        if resend or (r not in ["Done", "Cached"]):
            bot.send_private_msg(user_id=event['user_id'], message=event['message'])
        if r == "Timeout":
            bot.send_private_msg(user_id=event['user_id'], message="TLE~qwq")
            timeout_record(event['user_id'])
        elif r == "Failed":
            bot.send(event, message=f"[CQ:at,qq={event['user_id']}]\n" + "出错了qaq")
            bot.send_private_msg(user_id=event['user_id'], message=l)
        elif r == "Failed-NoError":
            bot.send(event, message=f"[CQ:at,qq={event['user_id']}]\n" + "出错了qaq，而且很不寻常，跟我主人说吧qwq")
        elif r in ["Done", "Cached"]:
            bot.send(event, message=f"[CQ:at,qq={event['user_id']}]\n" + l)
    except Exception as e:
        bot.send(event, message="似乎你（或者群主设置）不允许群内陌生人私聊，或者网络错误："+str(e)+"请将错误代码和发生的时间告诉我的主人", at_sender=True)
    return r, rets


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
            bot.send(event, message="qwq?", auto_escape=False)
            timeout_record(event['user_id'])
            return
        res = parse_expr(comm[4:].strip(), global_dict=calc_dict, local_dict=fools_dict)
        message = clamp(str(res), l=20000 if event['message_type'] == 'private' else 200)
        return bot.send(event, message, auto_escape=True, at_sender=True)
    except SoftTimeLimitExceeded:
        bot.send(event, f"[CQ:at,qq={event['user_id']}]\nTLE~qwq", auto_escape=False)
        timeout_record(event['user_id'])
        return ("Timeout", event['user_id'])
    except Exception as e:
        return bot.send(event, f'\n报错了qaq: {str(type(e))}\n{clamp(str(e))}', auto_escape=True)

@app.task(soft_time_limit=15, time_limit=20)
def run_bf(event, code, inp="", useascii=True):
    try:
        r= brainfuck.run(code, inp, useascii)
        bot.send(event, "结果为:\n" + clamp(r), auto_escape=True, at_sender=True)
    except SoftTimeLimitExceeded:
        bot.send(event, f"[CQ:at,qq={event['user_id']}]\nTLE~qwq")
        timeout_record(event['user_id'])
        return ("Timeout", event['user_id'])
    return inp

@app.task(soft_time_limit=60, time_limit=70, rate_limit="10/m")
def run_hs(event, src, inp=""):
    try:
        status, code, out, comlog = haskell_docker.runghc(src, inp)
        if code == 0: # Finished
            if status == "Done":
                bot.send(event, "结果为:\n" + clamp(out), auto_escape=True, at_sender=True)
                bot.send_private_msg(user_id=event['user_id'], auto_escape=True, message="编译日志：\n" + comlog)
                if len(out) > 200:
                    bot.send_private_msg(user_id=event['user_id'], auto_escape=True, message="完整结果：\n" + out)
            elif status == "No-output":
                bot.send(event, "成功运行，没有输出。", at_sender=True)
            else:
                print("WTF? at run_hs()")
        elif code == 35072:
            bot.send(event, "TLE~好坏qwq", at_sender=True)
        else:
            print(status, code)
            bot.send(event, "出错了qaq", at_sender=True)
            bot.send_private_msg(user_id=event['user_id'], auto_escape=True, message="编译日志：\n" + comlog)
            bot.send_private_msg(user_id=event['user_id'], auto_escape=True, message="完整结果：\n" + out)
    except SoftTimeLimitExceeded:
        bot.send(event, f"[CQ:at,qq={event['user_id']}]\nTLE~qwq")
        timeout_record(event['user_id'])
        return ("Timeout", event['user_id'])
    except Exception as e:
        return bot.send(event, f'\n报错了qaq: {str(type(e))}\n{clamp(str(e))}', auto_escape=True)
