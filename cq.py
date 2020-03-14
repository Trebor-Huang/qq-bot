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

bot = CQHttp(api_root='http://192.168.56.101:5700/')
application = bot.wsgi
repeat_count = dict()
latex_packages = ("bm", "array", "amsfonts", "amsmath", "amssymb", "mathtools", "tikz-cd", "mathrsfs", "xcolor", "mathdots")
help_string = "所有命令以'> '开头。命令列表：\n" +\
    "   > calc: 符号计算ascii数学表达式，允许使用字母变量。相乘必须用*不能连起来；幂函数必须用**不能用^。单字母常量首字母大写：E, pi, I。oo是无穷大∞。积分 integrate(表达式, (变量, 下界, 上界)) 或者 integrate(表达式, 变量)；微分 diff(表达式, 变量, 变量, 变量, ...)，如diff(sin(x), x, x, x)表示对sin(x)求x的三阶导；求和 Sum(表达式, (变量, 下界, 上界)).doit()，不加doit()不会计算。更多功能参见sympy.org。注意这些计算都是符号计算，数值计算可以用.n()或者数值计算方法，如nsolve等。\n" +\
    "   > render: 渲染LaTeX文字并以图片形式发送。这个功能是为方便文字公式相间，如果只希望渲染数学公式请用latex命令。\n"+\
    "   > latex: 渲染单个数学公式。\n"+\
    "   > ord:  序数运算。\n"+\
    "   > help: 不加参数：展示这个帮助；添加一个数学表达式作为参数：展示这个表达式的帮助文档（如果有）。\n\n"+\
    "附加功能：\n   - 复读"

def clamp(s, l=200):
    if len(s) > l:
        return s[:l] + " ..."
    return s

def render_latex_and_send(res, event):
        try:
            filename = "TEMP" + hex(hash(res) ^ time.time_ns())[1:]
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

@bot.on_message
def handle_msg(event):
    if random.randint(1,30) == 1:
        bot.clean_data_dir(data_dir="image")
    if event['message_type'] == "group":
        try:
            if (event['message'][-3:].lower() == 'dai' \
            or (pinyin.get(''.join(filter(lambda c: '\u4e00' <= c <= '\u9fff', event['message'])), format="strip").strip("。，？（！…—；：“”‘’《》～·）()").strip())[-3:] == 'dai'):
                if random.randint(1,2) == 2:
                    return {'reply': "Daisuke~", 'at_sender': False, 'auto_escape': True}
            if event['message'][0:2] == '> ':
                # command mode
                comm = event['message'][2:].replace("&#91;", "[").replace("&#93;", "]").replace("&amp;", '&')
                comms = comm.split()
                c = comms[0].capitalize()
                if c == 'Help':
                    cms = comm[4:].strip()
                    if cms == '':
                        bot.send_private_msg(message=help_string, user_id=event['user_id'], auto_escape=True)
                        return {'reply': "帮助已发送至私聊"}
                    if any(['\u4e00' <= c <= '\u9fff' for c in comm]):
                        return {'reply': "不支持汉字变量的计算。"}
                    res = parse_expr(comm[4:].strip())
                    if not res.__doc__:
                        return {'reply': "这个东西没有帮助文档诶"}
                    bot.send_private_msg(message=f"这个对象：\n\n{str(res)}\n\n的帮助文档如下：", user_id=event['user_id'], auto_escape=True)
                    bot.send_private_msg(message=clamp(res.__doc__, 2000), user_id=event['user_id'], auto_escape=True)
                    # TODO this is currently undoable since the image is probably too big
                    # TODO we'll send the help in pages instead
                    #! latexify.pdf_doc(comm[4:].strip(), res.__doc__)
                    #! bot.send_private_msg(message=f"[CQ:image,file=file:///G:\\{comm[4:].strip()}.jpeg]", user_id=event['user_id'], auto_escape=False)
                    return {'reply': "帮助已发送至私聊", 'auto_escape': True}
                if c == 'Echo' and event['user_id'] == 2300936257:
                    return {'reply': comm[4:].strip(), 'at_sender': False, 'auto_escape': True}
                ## These are dangerous leaky operations, and only I can use it.
                if c == 'Eval' and event['user_id'] == 2300936257:
                    res = eval(comm[4:].strip(), globals(), numpy.__dict__)
                    return {'reply': str(res), 'at_sender': False, 'auto_escape': True}
                if c == 'Calc':
                    if '^' in comm:
                        bot.send(event, message="^是异或的符号，**是幂，你确定吗？")
                    if any(['\u4e00' <= c <= '\u9fff' for c in comm]):
                        return {'reply': "不支持汉字变量的计算。"}
                    res = parse_expr(comm[4:].strip())
                    return {'reply': clamp(str(res)), 'auto_escape': True}
                if c == 'Ord':
                    reply = requests.get("http://192.168.56.101:5679/ord", params={"cmd": comm[3:].strip()})
                    reply_text = reply.text.strip()
                    if len(reply_text) > 100:
                        bot.send_private_msg(message=reply_text, auto_escape=True, user_id=event['user_id'])
                        return {"reply": "有点太长了，已发私聊"}
                    return {"reply": reply.text.strip(), "auto_escape": True}
                if c == 'Render':
                    return render_latex_and_send(comm[6:].strip(), event)
                if c == 'Latex':
                    return render_latex_and_send(f"$\\displaystyle {comm[5:].srtip()}$", event)
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
        except Exception as e:
            return {'reply': '报错了qaq: ' + clamp(str(e)), 'at_sender': False, 'auto_escape': True}
    elif event['message_type'] == "private":
        bot.send_private_msg(message=help_string, user_id=event['user_id'], auto_escape=True)
        return {'reply': "Bot几乎只有群聊功能"}


@bot.on_notice('group_increase')
def handle_group_increase(event):
    print(event)
    if event['group_id'] == 80852074 and event['sub_type'] == "invite" and event['operator_id'] == 1289817086:
        bot.send(event, message='神音姐姐又拉人了', auto_escape=True)
    return

@bot.on_request('group', 'friend')
def handle_request(event):
    print(event)
    return #{'approve': True}

if __name__ == "__main__":
    bot.run(host='127.0.0.1', port=8099, debug=True)
