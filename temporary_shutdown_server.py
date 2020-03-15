from cqhttp import CQHttp

bot = CQHttp(api_root='http://192.168.56.101:5700/')

help_string = "所有命令以'> '开头。命令列表：\n" +\
    "   > calc: 符号计算ascii数学表达式，允许使用字母变量。相乘必须用*不能连起来；幂函数必须用**不能用^。单字母常量首字母大写：E, pi, I。oo是无穷大∞。积分 integrate(表达式, (变量, 下界, 上界)) 或者 integrate(表达式, 变量)；微分 diff(表达式, 变量, 变量, 变量, ...)，如diff(sin(x), x, x, x)表示对sin(x)求x的三阶导；求和 Sum(表达式, (变量, 下界, 上界)).doit()，不加doit()不会计算。更多功能参见sympy.org。注意这些计算都是符号计算，数值计算可以用.n()或者数值计算方法，如nsolve等。\n" +\
    "   > render: 渲染LaTeX文字并以图片形式发送。这个功能是为方便文字公式相间，如果只希望渲染数学公式请用latex命令。\n"+\
    "   > latex: 渲染单个数学公式。\n"+\
    "   > ord:  序数运算。\n"+\
    "   > help: 不加参数：展示这个帮助；添加一个数学表达式作为参数：展示这个表达式的帮助文档（如果有）。\n\n"+\
    "附加功能：\n   - 复读"

@bot.on_message
def handle_msg(event):
    if event['message_type'] == "group":
        if event['message'][0:2] == '> ':
            comm = event['message'][2:].replace("&#91;", "[").replace("&#93;", "]").replace("&amp;", '&')
            comms = comm.split()
            c = comms[0].capitalize()
            if c == 'Help':
                cms = comm[4:].strip()
                if cms == '':
                    bot.send_private_msg(message=help_string, user_id=event['user_id'], auto_escape=True)
                    return {'reply': "帮助已发送至私聊"}
                return {'reply': "bot维修中", 'auto_escape': True}
            if c == 'Echo' and event['user_id'] == 2300936257:
                return {'reply': comm[4:].strip(), 'at_sender': False, 'auto_escape': True}
            return {'reply': "bot维修中", 'auto_escape': True}
    elif event['message_type'] == "private":
        bot.send_private_msg(message=help_string, user_id=event['user_id'], auto_escape=True)
        return {'reply': "Bot几乎只有群聊功能"}

bot.run(host='127.0.0.1', port=8099, debug=True)