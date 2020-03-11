"""start:
uwsgi --http 127.0.0.1:8099 --wsgi-file cq.py --callable application --processes 1 --threads 2 --harakiri 30 --stats 127.0.0.1:9191
"""
import random
import time
import numpy
import pinyin
import sympy
from sympy.parsing.sympy_parser import (implicit_multiplication_application,
                                        parse_expr, standard_transformations)
import requests
from cqhttp import CQHttp
import latexify

def clamp(s, l=200):
    if len(s) > l:
        return s[:l] + " ..."
    return s

sleeping = False
bot = CQHttp(api_root='http://192.168.56.101:5700/')
application = bot.wsgi
repeat_count = dict()
latex_packages = ("bm", "array", "amsfonts", "amsmath", "amssymb", "mathtools", "tikz-cd", "mathrsfs", "xcolor")

BP_raw = """Adrenaline is pumping
Adrenaline is pumping
Generator
Automatic Lover
Atomic
Atomic
Overdrive
Blockbuster
Brainpower
Call me a leader
Cocaine
Dont you try it
Dont you try it
Innovator
Killer machine
Theres no fate
Take control
Brainpower
Let
the
bass
kick"""

BrainPower = ''.join(BP_raw.lower().split())

BP_out = [
    ('Adrenaline is pumping', 18),
    ('Adrenaline is pumping', 37),
    ('Generator', 46),
    ('Automatic Lover', 60),
    ('Atomic', 66),
    ('Atomic', 72),
    ('Overdrive', 81),
    ('Blockbuster', 92),
    ('Brainpower', 102),
    ('Call me a leader', 115),
    ('Cocaine', 122),
    ("Don't you try it", 134),
    ("Don't you try it", 146),
    ('Innovator', 155),
    ('Killer machine', 168),
    ('Theres no fate', 180),
    ('Take control', 191),
    ('Brainpower', 201),
    ('Let', 204),
    ('the', 207),
    ('bass', 211),
    ('kick--', 215)
]

def next_in_lyrics(rsn):
    for (l, i) in BP_out:
        if rsn < i:
            return l, i-rsn
    return ("", -1)

BrainPower_final = "O-oooooooooo AAAAE-A-A-I-A-U- JO-oooooooooooo AAE-O-A-A-U-U-A- E-eee-ee-eee AAAAE-A-E-I-E-A- JO-ooo-oo-oo-oo EEEEO-A-AAA-AAAA"

def clean(r):
    return list(filter(str.isalpha, r.strip()))

def send_private_in_paragraphs(message, user_id, auto_escape):
    for m in (message.replace("\n\n", "\u1234").split("\u1234")):
        bot.send_private_msg(user_id=user_id, message=m, auto_escape=auto_escape)

bp_stage = 1
regular_stage_number = -1
# are you   -- 1
# re-       -- 2 (cycle)
# regular   -- 3
bpgid = -1

def regular_progress(inp):
    # returns progress in regular_stage_number
    rsn = regular_stage_number + 1
    p = 0
    while inp and BrainPower[rsn] == inp[0]:
        inp = inp[1:]
        rsn += 1
        p += 1
    return p

def brainpower(gid, inp):
    global bp_stage, regular_stage_number, bpgid
    inp = ''.join(list(filter(str.isalpha, ''.join(inp.lower().strip().split()))))
    if "停" in inp and bpgid == gid:
        bp_stage = 1
        regular_stage_number = -1
        bpgid = -1
        return
    if bp_stage == 1:
        if len(inp) < 6:
            # not starting
            return
        if inp[:6] == 'areyou':
            print('starting')
            bp_stage = 2
            bpgid = gid
            # see if further re-'s
            inp = inp[6:]
            while len(inp) >=2 and inp[:2] == 're':
                bp_stage = 3
                inp = inp[2:]
            # does not consider further advances
            if bp_stage == 2:
                return "Re-re-re-re-"
            elif bp_stage == 3:
                bp_stage = 2
                if random.randint(1,3) != 1:
                    return "re"
                return ""
        else:
            # not starting
            return
    if bp_stage == 2 and bpgid == gid:
        if len(inp) < 2:
            print('interrupted')
            if random.randint(1,3) == 2:
                return "re-re-re-（试图继续"
            else:
                bp_stage = 1
                regular_stage_number = -1
                bpgid = -1
                return "？怎么不脑力（"
        while len(inp) >= 2 and inp[:2] == 're':
            # strip off 're's
            inp = inp[2:]
        p = regular_progress(inp)
        if p >= 1:
            bp_stage = 3
            print('start the normal lyrics')
            _, n = next_in_lyrics(p)
            # see if already ended
            if n == -1:
                # already ended
                regular_stage_number = 0
                bp_stage = 1
                return '\n'.join([BrainPower_final] * random.randint(1, 3))
            # not ended yet
            regular_stage_number += p
            # never respond here
        else:
            print('still in cycle')
            r = random.randint(1,3)
            if r == 1:
                print('not respond')
                return ""
            elif r == 2:
                print('respond in cycle')
                return "re-"
            elif r == 3:
                print('start normal lyrics')
                bp_stage = 3
                regular_stage_number = 18
                return "Adrenaline is pumping"
    elif bp_stage == 3 and gid == bpgid:
        print("In normal lyrics")
        p = regular_progress(inp)
        print("Progressed: ", p)
        if p == 0:
            print("interrupted")
            if random.random() >= 0.05:
                print("try to continue")
                l, n = next_in_lyrics(regular_stage_number)
                print(l, n)
                regular_stage_number += n
                return f"事{l}（指正"
            print("stop")
            regular_stage_number = -1
            bp_stage = 1
            bpgid = -1
            return "（脑力失败"
        regular_stage_number += p
        print("Current stage:", regular_stage_number)
        if regular_stage_number == len(BrainPower) - 1:
            print("ended normal lyric.")
            bp_stage = 1
            regular_stage_number = -1
            bpgid = -1
            if random.randint(1, 5) != 3:
                return '\n'.join([BrainPower_final] * random.randint(1, 3))
            else:
                return "脑 力 大 成 功（"
        else:
            print("still in normal lyric")
            l, n = next_in_lyrics(regular_stage_number)
            print(l,n, len(clean(l)))
            # only join if n is exact and not last
            if len(clean(l)) == n and l != "kick--":
                if random.randint(1,2) == 2:
                    regular_stage_number += n
                    return l
                else:
                    return ""

def calc_cmd(event, comm):
    res = parse_expr(comm[4:].strip(), transformations=standard_transformations + (implicit_multiplication_application,))
    bot.send(event, str(res), auto_escape= True)

app = 0
help_string = "所有命令以'> '开头。命令列表：\n" +\
    "   > calc: 符号计算ascii数学表达式，允许使用字母变量。相乘必须用*不能连起来；幂函数必须用**不能用^。单字母常量首字母大写：E, pi, I。oo是无穷大∞。积分 integrate(表达式, (变量, 下界, 上界)) 或者 integrate(表达式, 变量)；微分 diff(表达式, 变量, 变量, 变量, ...)，如diff(sin(x), x, x, x)表示对sin(x)求x的三阶导；求和 Sum(表达式, (变量, 下界, 上界)).doit()，不加doit()不会计算。更多功能参见sympy.org。注意这些计算都是符号计算，数值计算可以用.n()或者数值计算方法，如nsolve等。\n" +\
    "   > render: 渲染LaTeX文字并以图片形式发送。这个功能是为方便文字公式相间，如果只希望渲染数学公式请用latex命令。\n"+\
    "   > latex: 渲染单个数学公式。\n"+\
    "   > ord:  序数运算。\n"+\
    "   > help: 不加参数：展示这个帮助；添加一个数学表达式作为参数：展示这个表达式的帮助文档（如果有）。\n\n"+\
    "附加功能：\n   - 复读\n   - 脑力\n这些功能不是命令，不能用'> '触发，具体方法比较显然，请自己探索。"


@bot.on_message
def handle_msg(event):
    global repeat_count, app, sleeping
    if random.randint(1,100) == 1:
        bot.clean_data_dir(data_dir="image")
    if event['message_type'] == "group":
        #if "草" in event['message']:
        #    return {'reply': """草(消歧义)\n\n你可能指：\n草(中文)\n草(日文)\n草(中日双语)\n草(英文)\n草(一种植物)\n草(Minecraft)\n草(两格高)\n草(化学式)\n草(鲁迅刻在桌上的字符)""", 'at_sender': False, 'auto_escape': True}
        if sleeping:
            if event['message'] == "> wake" and event['user_id'] == 2300936257:
                sleeping = False
                return {'reply': "来了qwq", "at_sender": "False"}
            return
        if (event['message'][-3:].lower() == 'dai' \
          or (pinyin.get(''.join(filter(lambda c: '\u4e00' <= c <= '\u9fff', event['message'])), format="strip").strip("。，？（！…—；：“”‘’《》～·）()").strip())[-3:] == 'dai'):
            if random.randint(1,2) == 2:
                return {'reply': "Daisuke~", 'at_sender': False, 'auto_escape': True}
        if (r := brainpower(event['group_id'], event['message'])) is not None:
            repeat_count = dict()
            app = (app + 1) % 4
            print(bp_stage, regular_stage_number, r)
            if bp_stage == 3:
                print(next_in_lyrics(regular_stage_number))
            if r == "":
                return
            return {'reply': r + [" ", "（", "（（", "!"][app], 'at_sender': False, 'auto_escape': True}
        if event['message'][0:2] == '> ':
            # command mode
            comm = event['message'][2:].replace("&#91;", "[").replace("&#93;", "]").replace("&amp;", '&')
            comms = comm.split()
            c = comms[0].capitalize()
            if c == 'Help':
                cms = comm[4:].strip()
                print("--- Help here. ---", cms)
                if cms == '':
                    bot.send_private_msg(message=help_string, user_id=event['user_id'], auto_escape=True)
                    return {'reply': "帮助已发送至私聊"}
                try:
                    if any(['\u4e00' <= c <= '\u9fff' for c in comm]):
                        return {'reply': "不支持汉字变量的计算。"}
                    res = parse_expr(comm[4:].strip())
                    if not res.__doc__:
                        return {'reply': "这个东西没有帮助文档诶"}
                    bot.send_private_msg(message=f"这个对象：\n\n{str(res)}\n\n的帮助文档如下：", user_id=event['user_id'], auto_escape=True)
                    bot.send_private_msg(message=clamp(res.__doc__, l=2000), user_id=event['user_id'], auto_escape=True)
                    return {'reply': "帮助已发送至私聊", 'auto_escape': True}
                except Exception as e:
                    return {'reply': '报错了qaq: ' + str(e), 'at_sender': False, 'auto_escape': True}
            if c == 'Echo' and event['user_id'] == 2300936257:
                return {'reply': comm[4:].strip(), 'at_sender': False, 'auto_escape': True}
            ## These are dangerous leaky operations, and only I can use it.
            if c == 'Eval' and event['user_id'] == 2300936257:
                try:
                    res = eval(comm[4:].strip(), globals(), numpy.__dict__)
                    return {'reply': str(res), 'at_sender': False, 'auto_escape': True}
                except Exception as e:
                    return {'reply': '报错了qaq: ' + str(e), 'at_sender': False, 'auto_escape': True}
            if c == 'Calc':
                try:
                    if '^' in comm:
                        bot.send(event, message="^是异或的符号，**是幂，你确定吗？")
                    if any(['\u4e00' <= c <= '\u9fff' for c in comm]):
                        return {'reply': "不支持汉字变量的计算。"}
                    res = parse_expr(comm[4:].strip())#, transformations=standard_transformations + (implicit_multiplication_application,))
                    return {'reply': clamp(str(res)), 'auto_escape': True}
                except Exception as e:
                    return {'reply': '报错了qaq: ' + str(e), 'at_sender': False, 'auto_escape': True}
            
            if c == 'Ord':
                reply = requests.get("http://192.168.56.101:5679/ord", params={"cmd": comm[3:].strip()})
                reply_text = reply.text.strip()
                if len(reply_text) > 100:
                    bot.send_private_msg(message=reply_text, auto_escape=True, user_id=event['user_id'])
                    return {"reply": "有点太长了，已发私聊"}
                return {"reply": reply.text.strip(), "auto_escape": True}
            if c == 'Render':
                try:
                    res = comm[6:]
                    filename = "RENDER" + hex(hash(res) ^ time.time_ns())[1:]
                    latexify.latexify(res, filename="./img/" + filename, definitions="\\textwidth=7cm", usepackage=latex_packages)
                    # print("Sync", requests.get("http://192.168.56.101:5679/sync"))
                    try:
                        bot.delete_msg(message_id=event['message_id'])
                    except Exception:
                        print("Failed to recall latex spam.")
                    return {'reply': f"[CQ:image,file=file:///G:\\{filename}.jpeg]", 'auto_escape': False, 'at_sender': True}
                except RuntimeError as e:
                    bot.send_private_msg(user_id=event['user_id'], message=event['message'])
                    bot.send_private_msg(user_id=event['user_id'], message = "错误如下：\n" + str(e).strip(), auto_escape=True)
                    try:
                        bot.delete_msg(message_id=event['message_id'])
                    except Exception:
                        print("Failed to recall latex spam.")
                    return {'reply': 'LaTeX有错，已发私聊'}
                except Exception as e:
                    return {'reply': '报错了qaq: ' + clamp(str(e)), 'at_sender': False, 'auto_escape': True}
            if c == 'Latex':
                try:
                    res = comm[5:]
                    filename = "LATEX" + hex(hash(res) ^ time.time_ns())[1:]
                    #sympy.preview(f"$${res}$$", viewer='file', output='png', filename=f'./img/{hash(res)}.png', euler=False, dvioptions=["-T", "tight", "-z", "0", "--truecolor", "-D 500"], packages=latex_packages)
                    latexify.latexify(f"$\\displaystyle {res}$", filename='./img/' + filename, usepackage=latex_packages)
                    try:
                        bot.delete_msg(message_id=event['message_id'])
                    except Exception:
                        print("Failed to recall latex spam.")
                    return {'reply': f"[CQ:image,file=file:///G:\\{filename}.jpeg]", 'auto_escape': False, 'at_sender': True}
                except RuntimeError as e:
                    bot.send_private_msg(user_id=event['user_id'], message=event['message'])
                    bot.send_private_msg(user_id=event['user_id'], message = "错误如下：\n" + str(e).strip(), auto_escape=True)
                    try:
                        bot.delete_msg(message_id=event['message_id'])
                    except Exception:
                        print("Failed to recall latex spam.")
                    return {'reply': 'LaTeX有错，已发私聊'}
                except Exception as e:
                    return {'reply': '报错了qaq: ' + clamp(str(e)), 'at_sender': False, 'auto_escape': True}
            if c == 'Sleep' and event['user_id'] == 2300936257:
                sleeping = True
                return {'reply': 'zzz', 'at_sender': False}
            return {'reply': "憨批（试下 > help", 'auto_escape': True}
        if event['group_id'] in repeat_count:
            # count the number of last repeat
            if repeat_count[event['group_id']][0] == str(event['raw_message']):
                repeat_count[event['group_id']][1] += 1
            else:
                repeat_count[event['group_id']][0] = str(event['raw_message'])
                if repeat_count[event['group_id']][1] > 1:
                    repeat_count[event['group_id']][1] = 0
                    if random.randint(1, 5) == 2:
                        return {'reply': "打断复读的事屑（确信", 'at_sender': False, 'auto_escape': True}
                    if random.randint(1, 7) == 6:
                        return {'reply': "？？", 'at_sender': False, 'auto_escape': True}
                repeat_count[event['group_id']][1] = 1
            if repeat_count[event['group_id']][1] >= 7:
                repeat_count[event['group_id']][1] = 0
                return {'reply': "适度复读活跃气氛，过度复读影响交流。为了您和他人的健康，请勿过量复读。", 'at_sender': False, 'auto_escape': True}
        else:
            repeat_count[event['group_id']] = [str(event['raw_message']), 1]
        if random.randint(1, repeat_count[event['group_id']][1]+1) >= 3:
            repeat_count[event['group_id']][1] = 0 # prevent spamming
            if random.randint(1, 30) == 4:
                return {'reply': "复  读  大  失  败", 'at_sender': False, 'auto_escape': True}
            if random.randint(1, 10) == 1:
                return {'reply': "（", 'at_sender': False, 'auto_escape': True}
            if random.randint(1, 20) == 33:
                return {'reply': "打断（（", 'at_sender': False, 'auto_escape': True}
            return {'reply': event['raw_message'], 'at_sender': False, 'auto_escape': False}
        if random.randint(1, 455) == 44 and event['group_id'] == 730695976:
            return {'reply': "3倍ice cream☆☆！！！", 'at_sender': False, 'auto_escape': True}
        if random.randint(1, 360) == 144 and event['group_id'] == 730695976:
            return {'reply': "爬", 'at_sender': False, 'auto_escape': True}
        if random.randint(1, 1000) == 111 and event['group_id'] == 80852074:
            return {'reply': "最喜欢qlbf了（", "at_sender": False, 'auto_escape': True}
    elif event['message_type'] == "private":
        bot.send_private_msg(message=help_string, user_id=event['user_id'], auto_escape=True)
        return {'reply': "Bot几乎只有群聊功能"}


@bot.on_notice('group_increase')
def handle_group_increase(event):
    print(event)
    if event['group_id'] == 80852074 and event['sub_type'] == "invite" and event['operator_id'] == 1289817086:
        bot.send(event, message='神音姐姐又拉人了', auto_escape=True)
    if random.randint(1, 30) == 16:
        bot.send(event, message='其实每次有个人加群就欢迎是很憨的，但是这段代码放在这里可以提醒我如何在有人加群的时候触发动作，所以我才没有删掉（', auto_escape=True)
    return

@bot.on_request('group', 'friend')
def handle_request(event):
    print(event)
    return #{'approve': True}

if __name__ == "__main__":
    bot.run(host='127.0.0.1', port=8099, debug=True)
