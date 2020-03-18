from cqhttp import CQHttp

bot = CQHttp(api_root='http://192.168.56.101:5700/')


@bot.on_message
def handle_msg(event):
    if event['message_type'] == "group":
        if event['message'][0:2] == '> ':
            comm = event['message'][2:].replace("&#91;", "[").replace("&#93;", "]").replace("&amp;", '&')
            comms = comm.split()
            c = comms[0].capitalize()
            if c == 'Echo' and event['user_id'] == 2300936257:
                return {'reply': comm[4:].strip(), 'at_sender': False, 'auto_escape': True}
            return {'reply': "bot维修中", 'auto_escape': True}
    elif event['message_type'] == "private":
        return {'reply': "Bot几乎只有群聊功能"}

bot.run(host='127.0.0.1', port=8099, debug=True)