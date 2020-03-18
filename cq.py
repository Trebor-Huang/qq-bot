import random
import time
import numpy
import pinyin
import sympy
from sympy.parsing.sympy_parser import (implicit_multiplication_application,
                                        parse_expr, standard_transformations)
import requests
from celery import Celery
from cqhttp import CQHttp
import redis
import tasks

bot = CQHttp(api_root='http://192.168.56.101:5700/')
application = bot.wsgi
r = redis.Redis(host='127.0.0.1', port=6379, db=0)

latex_packages = ("bm", "array", "amsfonts", "amsmath", "amssymb", "mathtools", "tikz-cd", "mathrsfs", "xcolor", "mathdots")
help_string = "所有命令以'> '开头，且均支持群聊和私聊使用。命令列表：\n" +\
    "   > calc: 符号计算ascii数学表达式，允许使用字母变量。相乘必须用*不能连起来；幂函数必须用**不能用^。单字母常量首字母大写：E, pi, I。oo是无穷大∞。积分 integrate(表达式, (变量, 下界, 上界)) 或者 integrate(表达式, 变量)；微分 diff(表达式, 变量, 变量, 变量, ...)，如diff(sin(x), x, x, x)表示对sin(x)求x的三阶导；求和 Sum(表达式, (变量, 下界, 上界)).doit()，不加doit()不会计算。更多功能参见sympy.org。注意这些计算都是符号计算，数值计算可以用.n()或者数值计算方法，如nsolve等。\n" +\
    "   > render: 渲染LaTeX文字并以图片形式发送。这个功能是为方便文字公式相间，如果只希望渲染数学公式请用latex命令。\n"+\
    "   > latex: 渲染单个数学公式。\n"+\
    "   > render-r/latex-r: 同上，会将群聊中撤回的LaTeX私聊发回\n"+\
    "   > ord:  序数运算。\n"+\
    "   > help: 不加参数：展示这个帮助；添加一个数学表达式作为参数：展示这个表达式的帮助文档（如果有）。\n\n"+\
    "附加功能：\n   - 复读"

def clamp(s, l=200):
    if len(s) > l:
        return s[:l] + " ..."
    return s

@bot.on_message
def handle_msg(event):
    if random.randint(1,30) == 1:
        bot.clean_data_dir(data_dir="image")
    if event['message'][0:2] == '> ':
        # command mode
        comm = event['message'][2:].replace("&#91;", "[").replace("&#93;", "]").replace("&amp;", '&')
        comms = comm.split()
        c = comms[0].capitalize()
        if c == 'Help':
            cms = comm[4:].strip()
            if cms == '':
                bot.send_private_msg(message=help_string, user_id=event['user_id'], auto_escape=True)
                return None if event['message_type'] == "private" else {'reply': "帮助已发送至私聊"}
            if any(['\u4e00' <= c <= '\u9fff' for c in comm]):
                return {'reply': "不支持汉字变量的计算。"}
            res = parse_expr(comm[4:].strip())
            if not res.__doc__:
                return {'reply': "这个东西没有帮助文档诶"}
            bot.send_private_msg(message=f"这个对象：\n\n{str(res)}\n\n的帮助文档如下：", user_id=event['user_id'], auto_escape=True)
            tasks.send_rst_doc.delay(res.__doc__, event)
            return None if event['message_type'] == "private" else {'reply': "帮助已发送至私聊"}
        if c == 'Echo' and event['user_id'] == 2300936257:
            return {'reply': comm[4:].strip(), 'at_sender': False, 'auto_escape': True}
        if c == 'Eval' and event['user_id'] == 2300936257:
            res = eval(comm[4:].strip(), globals(), numpy.__dict__)
            return {'reply': str(res), 'at_sender': False, 'auto_escape': True}
        if c == 'Calc':
            if '^' in comm:
                bot.send(event, message="^是异或的符号，**是幂，你确定吗？")
            if any(['\u4e00' <= c <= '\u9fff' for c in comm]):
                return {'reply': "不支持汉字变量的计算。"}
            res = parse_expr(comm[4:].strip())
            return {'reply': clamp(str(res), l=200000 if event['message_type'] == 'private' else 200), 'auto_escape': True}
        if c == 'Ord':
            reply = requests.get("http://192.168.56.101:5679/ord", params={"cmd": comm[3:].strip()})
            reply_text = reply.text.strip()
            if len(reply_text) > 100 and event['message_type'] != 'private':
                bot.send_private_msg(message=reply_text, auto_escape=True, user_id=event['user_id'])
                return {"reply": "有点太长了，已发私聊"}
            return {"reply": reply.text.strip(), "auto_escape": True}
        if c == 'Render':
            tasks.render_latex_and_send.delay(comm[6:].strip(), event, latex_packages)
            return
        if c == 'Latex':
            tasks.render_latex_and_send.delay(f"$\\displaystyle {comm[5:].strip()}$", event, latex_packages, definitions="")
            return
        if c == 'Render-r':
            tasks.render_latex_and_send.delay(comm[8:].strip(), event, latex_packages, True)
            return
        if c == 'Latex-r':
            tasks.render_latex_and_send.delay(f"$\\displaystyle {comm[7:].strip()}$", event, latex_packages, True)
            return
        return {'reply': "憨批（试下 > help", 'auto_escape': True}
    if event['message_type'] == "group":
        try:
            if (event['message'][-3:].lower() == 'dai' \
            or (pinyin.get(''.join(filter(lambda c: '\u4e00' <= c <= '\u9fff', event['message'])), format="strip").strip("。，？（！…—；：“”‘’《》～·）()").strip())[-3:] == 'dai'):
                if random.randint(1,2) == 2:
                    return {'reply': "Daisuke~", 'at_sender': False, 'auto_escape': True}
            try:  # 复读
                with r.lock('repeat', blocking_timeout=5) as _:
                    # code you want executed only after the lock has been acquired
                    if rc := r.get("repeat" + str(event['group_id'])):
                        rcount = int(r.get("count" + str(event['group_id'])).decode('utf-8'))
                        # count the number of last repeat
                        if rc.decode('utf-8') == str(event['raw_message']):
                            r.incr("count" + str(event['group_id']))
                        else:
                            r.set("repeat" + str(event['group_id']), str(event['raw_message']))
                            if rcount > 1:
                                r.set("count" + str(event['group_id']), 0)
                                if random.randint(1, 5) == 2:
                                    return {'reply': "打断复读的事屑（确信", 'at_sender': False, 'auto_escape': True}
                                if random.randint(1, 7) == 6:
                                    return {'reply': "？？", 'at_sender': False, 'auto_escape': True}
                                r.set("count" + str(event['group_id']), 1)
                                return
                        if rcount >= 7:
                            r.set("count" + str(event['group_id']), 0)
                            return {'reply': "适度复读活跃气氛，过度复读影响交流。为了您和他人的健康，请勿过量复读。", 'at_sender': False, 'auto_escape': True}
                        if random.randint(1, rcount+1) >= 3:
                            r.set("count" + str(event['group_id']), 0) # prevent spamming
                            if random.randint(1, 30) == 4:
                                return {'reply': "复  读  大  失  败", 'at_sender': False, 'auto_escape': True}
                            if random.randint(1, 10) == 1:
                                return {'reply': "（", 'at_sender': False, 'auto_escape': True}
                            if random.randint(1, 20) == 33:
                                return {'reply': "打断（（", 'at_sender': False, 'auto_escape': True}
                            return {'reply': event['raw_message'], 'at_sender': False, 'auto_escape': False}
                    else:
                        r.set("repeat" + str(event['group_id']), str(event['raw_message']))
                        r.set("count" + str(event['group_id']), 1)
            except redis.lock.LockError:
                print("LockError occured")
                return
            if random.randint(1, 455) == 44 and event['group_id'] == 730695976:
                return {'reply': "3倍ice cream☆☆！！！", 'at_sender': False, 'auto_escape': True}
            if random.randint(1, 360) == 144 and event['group_id'] == 730695976:
                return {'reply': "爬", 'at_sender': False, 'auto_escape': True}
            if random.randint(1, 1000) == 111 and event['group_id'] == 80852074:
                return {'reply': "最喜欢qlbf了（", "at_sender": False, 'auto_escape': True}
        except Exception as e:
            return {'reply': f'报错了qaq: {str(type(e))}\n{clamp(str(e))}', 'auto_escape': True}
    elif event['message_type'] == "private":
        bot.send_private_msg(message=help_string, user_id=event['user_id'], auto_escape=True)
        return


@bot.on_notice('group_increase')
def handle_group_increase(event):
    print(event)
    if event['group_id'] == 80852074 and event['sub_type'] == "invite" and event['operator_id'] == 1289817086:
        bot.send(event, message='神音姐姐又拉人了', auto_escape=True)
    if event['user_id'] == event['self_id']:
        tasks.reject_unfamiliar_group(event['group_id'])
    return

@bot.on_request('friend')
def handle_friend_request(event):
    bot.send_private_msg(user_id=2300936257, message=str(event), auto_escape=True)
    return {'approve': True}

@bot.on_request('group')
def handle_group_request(event):
    print(event)
    tasks.reject_unfamiliar_group.delay(event['group_id'])
    return {'approve': True}

if __name__ == "__main__":
    bot.run(host='127.0.0.1', port=8099, debug=True)
