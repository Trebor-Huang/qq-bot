import random, os, time, atexit
import numpy, pinyin
import sympy
from sympy.parsing.sympy_parser import parse_expr
import requests
from celery import Celery
from cqhttp import CQHttp
from flask import jsonify
import redis, sqlite3, datetime
import tasks, custom_settings
# docker run --name=coolq -d -p 9000:9000 -p 5700:5700 -v $(pwd)/coolq:/home/user/coolq coolq/wine-coolq
blacklist = ["智障", "傻逼", "傻b", "你国", "贵国", "死妈", "死🐴", "老子", "贵群", "弱智", "政治", "脑残", "尼玛"]

bot = CQHttp(api_root=custom_settings.CQHTTP_API)
application = bot.wsgi
r = redis.Redis(host='127.0.0.1', port=6379, db=0)
admin = [2300936257, 1458814497, 2782676253, 3415064240]
owner = 2300936257
get_qq = lambda s: int(''.join(list(filter(str.isnumeric, s))))

# coolq error codes
# -2 未收到服务器回复，可能未发送成功
#-26 消息太长

help_string = """
不仔细读帮助文档的话，不会用是必然的，请仔细读，这里已经包含了你需要的所有信息。
所有命令以西文大于号">"和一个空格开头，基本上支持群聊和私聊使用。

"> calc " + 表达式
\t符号计算ascii数学表达式，允许使用字母变量。
\t注意，相乘必须用"*"号连接；幂要用"**"而不能用"^"；
\t常量的书写格式：E, I, pi；oo代表无限大；
\t积分 integrate(表达式, (变量, 下界, 上界)) 或者 integrate(表达式, 变量)；
\t微分 diff(表达式, 变量, 变量, 变量, ...)，如diff(sin(x), x, x, x)表示对sin(x)求x的三阶导；
\t求和 summation(表达式, (变量, 下界, 上界))。
\t注意这些计算都是符号计算，数值计算可以用.n()或者数值计算方法，如nsolve等。
\t更多功能参见sympy.org。

"> render " + LaTeX文字
\t渲染LaTeX段落。如果希望渲染公式请用 $ ... $ 或者 \\( ... \\) 括起来；支持行间公式（即 $$ ... $$ 或者 \\[ ... \\] 括起的公式）。
\t如果希望添加LaTeX宏包，可以在最开头用"\\begin{bot-usepackage} 包1 包2 ... \\end{bot-usepackage}"声明希望用到的宏包，如果没有安装，可以联系bot作者。
\t如果希望添加LaTeX preamble里的内容，可以紧接着用""\\begin{bot-defs} ... \\end{bot-defs}"添加。

"> render-r " + LaTeX文字
\t与上一个命令相同，会私聊回发你的LaTeX代码。

"> latex " + LaTeX公式
\t渲染数学公式，用法与上面的命令相同。

"> latex-r " + LaTeX公式
\t同理。

上面四个命令会进行缓存。如果发现机器人响应很快，但是结果不正确，请联系机器人管理员。

"> brainfk " + Brainfuck程序 [ + "| input |" + ascii输入 ]
\tBrainfuck程序，输入和输出都是ascii，纸带向右无限延伸，每个格子范围是0~255（取模）。

"> haskell " + Haskell程序 [ + "| input |" + stdin输入 ]
\tHaskell程序，必须以"Module Main where"开头。

"> coq " + Coq命令
\tCoq交互。必须要管理员启动群内coq模块才能使用。一个群只会有一个coq会话。

"> coqstart"
\t（仅群管理）启动群内coq模块。

"> coqstop"
\t（仅群管理）关闭群内coq模块。

"> ping"
\t仅限私聊，如果机器人在线，会回复PONG。可以用来测试机器人在线以及网络情况。

"> help " [ + calc命令可用的函数 ]
\t不加参数：显示这个帮助信息；添加参数：显示sympy函数的帮助文档（如果有）。
\t注意，这里的帮助文档仅限calc命令的帮助，比如"> help solve"。没有其他东西的帮助。

附加功能：
 - 复读

""".strip()

def clamp(s, l=200):
    if len(s) > l:
        return s[:l] + " ..."
    return s

def evaluate_user(user_id):
    timeouts = r.get("timeout" + str(user_id))
    return timeouts is None or (int(timeouts) < 30000)

@bot.on_message
def handle_msg(event):
    if event['message_type'] == "group":
        sqlconn = sqlite3.connect("history.db")
        cursor = sqlconn.cursor()
        cursor.execute("INSERT INTO history VALUES (?, ?, ?, ?, ?)", (event["message_id"], event["group_id"], event["user_id"], datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), event["message"]))
        sqlconn.commit()
        sqlconn.close()
    if event['message'][0:2] == '> ' and event['message'] != "> ":
        if not evaluate_user(event['user_id']):
            return {'reply': "不喜欢你qwq（给我发女装照片好不好quq", 'at_user': True, 'auto_escape': True}
        try:
            # command mode
            comm = event['message'][2:].replace("&#91;", "[").replace("&#93;", "]").replace("&amp;", '&')
            comms = comm.split()
            c = comms[0].capitalize()
            if c == 'Forgive' and event['user_id'] in admin:
                r.set("timeout" + str(get_qq(comms[1])), 0)
                return {'reply': "原谅你啦 [CQ:at,qq=%s]" % str(get_qq(comms[1])), "at_sender": False, "auto_escape":False}
            if c == 'Ban' and event['user_id'] in admin and event['message_type'] == 'group':
                return bot.set_group_ban(group_id=event['group_id'], user_id=get_qq(comms[1]), duration=30 if len(comms) < 3 else int(comms[2]))
            if c == 'History' and event['user_id'] in admin and event['message_type'] == 'group':
                sqlconn = sqlite3.connect("history.db")
                cursor = sqlconn.cursor()
                requirements = comm[7:].strip()
                # trusted
                for i, (fmsgid, fuserid, ftime, fcontent) in enumerate(cursor.execute(f"SELECT msgid, userid, time, content FROM history WHERE {requirements} AND groupid={event['group_id']} ORDER BY time")):
                    if i > 5:
                        bot.send_private_msg(message = f"#{fmsgid} - [CQ:at,qq={fuserid}] - {ftime}\n\n{fcontent}", user_id=event['user_id'])
                    else:
                        bot.send(event, f"#{fmsgid} - [CQ:at,qq={fuserid}] - {ftime}\n\n{fcontent}")
                sqlconn.close()
                return
            if c == 'Help':
                cms = comm[4:].strip()
                if cms == '':
                    try:
                        bot.send_private_msg(message=help_string, user_id=event['user_id'], auto_escape=True)
                    except Exception:
                        bot.send(event, message=f"[CQ:at,qq={event['user_id']}]似乎你（或者群主设置）不允许群内陌生人私聊")
                        return
                    return None if event['message_type'] == "private" else {'reply': "帮助已发送至私聊"}
                if any(['\u4e00' <= c <= '\u9fff' for c in comm]):
                    return {'reply': "不支持汉字变量的计算。"}
                res = parse_expr(comm[4:].strip())
                if isinstance(res, sympy.Symbol):
                    return {'reply': "这东西是个符号"}
                if not res.__doc__:
                    return {'reply': "这个东西没有帮助文档诶"}
                try:
                    bot.send_private_msg(message=f"这个对象：\n\n{str(res)}\n类型是{type(res)}\n\n的帮助文档如下，请稍等：", user_id=event['user_id'], auto_escape=True)
                except Exception:
                    bot.send(event, message="似乎你（或者群主设置）不允许群内陌生人私聊", at_sender=True)
                    return
                tasks.send_rst_doc.delay(res.__doc__, event)
                return None if event['message_type'] == "private" else {'reply': "帮助已发送至私聊"}
            elif c == 'Echo' and event['user_id'] in admin:
                return {'reply': comm[4:].strip(), 'at_sender': False, 'auto_escape': True}
            elif c == 'Eval' and event['user_id'] in admin:
                res = eval(comm[4:].strip(), globals(), numpy.__dict__)
                return {'reply': str(res), 'at_sender': False, 'auto_escape': True}
            elif c == 'Purge' and event['user_id'] in admin:
                c0 = os.system("rm ./coolq/data/image/*.cqimg ./coolq/data/image/*.jpeg")
                c1 = os.system("rm ./coolq/data/record/*")
                c2 = os.system("rm ./latex_process/*.jpeg")
                c3 = os.system("rm ./latex/texput.tex")
                c4 = os.system("rm ./latex_output/*")
                c5 = os.system("rm ./srcfolder/*")
                return {'reply': str((c0, c1, c2, c3, c4, c5))}
            elif c == 'Ping' and event['message_type'] == "private":
                return {'reply': 'PONG', 'at_sender': False}
            elif c == 'Calc':
                tasks.calc_sympy.delay(comm, event)
                return
            elif c == 'Ord':
                return {"reply": "目前暂停了这项功能"}
            elif c == 'Render':
                tasks.docker_latex.delay(comm[6:].strip(), False, event)
                return
            elif c == 'Render-r':
                tasks.docker_latex.delay(comm[8:].strip(), True, event)
                return
            elif c == 'Latex':
                tasks.docker_latex.delay(comm[6:].strip(), False, event, True)
                return
            elif c == 'Latex-r':
                tasks.docker_latex.delay(comm[8:].strip(), True, event, True)
                return
            elif c == 'Brainfk':
                res = comm[8:].split("| input |")
                if len(res) > 2:
                    raise ValueError("输入格式不正确qwq")
                tasks.run_bf.delay(event, *res, useascii=True)
                return
            elif c == 'Brainfk-n':
                res = comm[10:].split("| input |")
                if len(res) > 2:
                    raise ValueError("输入格式不正确qwq")
                tasks.run_bf.delay(event, *res, useascii=False)
                return
            elif c == 'Haskell':
                bot.send_private_msg(user_id=owner, message=str(event['sender']) + "\n\n" + comm[8:], auto_escape=True)
                res = comm[8:].split("| input |")
                if len(res) > 2:
                    raise ValueError("输入格式不正确qwq")
                tasks.run_hs.delay(event, *res)
                return
            elif c == "Coq" and event['message_type'] == "group":
                coqcmd = comm[4:].strip()
                result = requests.post("http://localhost:9001/query", json={"id": event['group_id'], "cmd": coqcmd})
                if result.ok:
                    rj = result.json()
                    if len(rj['content']) > 200:
                        bot.send_private_msg(message=clamp(rj['content'], 10000), user_id = event['user_id'])
                    return {"reply": rj['status'] + "\n" + clamp(rj['content']), "at_sender":True}
                else:
                    return {"reply": "坏耶：\n" + clamp(result.text, 300), "at_sender":True, "auto_escape":True}
            elif (c == "Coqstart" or c == "Coqstop") and event['message_type'] == "group":
                try:
                    role = event['sender']['role']
                except:
                    return {"reply": "qwq"}
                if role in ["owner", "admin"] or event['user_id'] in admin:
                    result = requests.post("http://localhost:9001/" + 
                      ("create_session" if c == "Coqstart" else "release_session"), json={"id": event['group_id']})
                    if result.ok:
                        return {"reply": "好耶ww", "at_sender":True}
                    else:
                        return {"reply": "坏耶：\n" + clamp(result.text, 100), "at_sender":True, "auto_escape":True}
            if ('电' in comm or '⚡' in comm) and event['message_type'] == "group":
                shock = int(r.incr("shock"))
                if shock > 10:
                    r.expire("shock", 1500)
                    return {'reply': "没电了qaq"}
                r.expire("shock", 15 * shock**2)
                level = comm.count("电") + 5 * comm.count("⚡") + shock * 1.5
                d = int(random.gauss(15*60 + 10 * level ** 2, level * 2))
                if d > 24 * 60 * 60:
                    d = 24 * 60 * 60
                bot.set_group_ban(group_id = event['group_id'], user_id = event['user_id'], duration = d)
                return {'reply': "您被电了 %s 秒！%s" % (d, "（"*int(min(5, level)))}
            return {'reply': "qwq（试下 > help", 'auto_escape': True}
        except Exception as e:
            return {'reply': f'报错了qaq: {str(type(e))}\n{clamp(str(e))}', 'auto_escape': True}
    if event['message_type'] == "group":
        if any(i in event['message'].lower() for i in blacklist):
            return {"reply": "这么说是不对的", "at_sender": False}
        try:
            # miscellanous, lowest priority
            if (event['message'][-3:].lower() == 'dai' \
            or (pinyin.get(''.join(filter(lambda c: '\u4e00' <= c <= '\u9fff', event['message'])), format="strip").strip("。，？（！…—；：“”‘’《》～·）()").strip())[-3:] == 'dai'):
                if random.randint(1,2) == 2:
                    return {'reply': "Daisuke~", 'at_sender': False, 'auto_escape': True}
            if '贴贴' in event['message'] and event['user_id'] == 1458814497:
                return {'reply': "（要贴贴！", 'at_sender': False, 'auto_escape': True}
            if event['message'].strip().strip(",.!?！？，。…“”'\"").upper() == "PUSHEEN":
                return {'reply': "[CQ:image,file=pusheen.png]", 'at_sender': False}
            if 'POPEEN' in event['message'].upper():
                return {'reply': "[CQ:image,file=popeen.jpg]", 'at_sender': False}
        except Exception as e:
            if str(e) == "(200, -26)":
                return {'reply': f'消息可能太长了', 'auto_escape': True}
            return {'reply': f'报错了qaq: {str(type(e))}\n{clamp(str(e))}', 'auto_escape': True}
    elif event['message_type'] == "private":
        return {'reply': "qwq（试下 > help", 'auto_escape': True}


@bot.on_notice('group_increase')
def handle_group_increase(event):
    print(event)
    if event['group_id'] == 80852074 and event['sub_type'] == "invite" and event['operator_id'] == 1289817086:
        bot.send(event, message='神音姐姐又拉人了', auto_escape=True)
    if event['user_id'] == event['self_id']:
        tasks.reject_unfamiliar_group.delay(event['group_id'])

@bot.on_request('friend')
def handle_friend_request(event):
    bot.send_private_msg(user_id=owner, message=str(event), auto_escape=True)

@bot.on_request('group')
def handle_group_request(event):
    if event['sub_type'] == "invite":
        bot.send_private_msg(user_id=owner, message=str(event), auto_escape=True)
        bot.send_private_msg(user_id=event['user_id'], message="只能拉我进有主人在的群qwq", auto_escape=True)

@atexit.register
def on_exit():
    print(">>> Closing <<<")
    r.close()

if __name__ == "__main__":
    bot.run(host='127.0.0.1', port=8099, debug=True)
