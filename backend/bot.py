from mirai import Mirai, MessageChain, Friend, FriendMessage, Group, Member, GroupMessage, TempMessage, At
from mirai import Plain, Quote, Source
import asyncio
import corefunc

app = Mirai(host="localhost", port="8080", authKey='Laktyqrqwq', qq=3235331859, websocket=False)

@app.receiver("FriendMessage")
async def handle_fm(app: Mirai, friend: Friend, message: FriendMessage):
    print(friend.json())
    try:
        txt = message.messageChain.getFirstComponent(Plain).text.strip()[:2]
    except Exception:
        return
    if txt == "> ":
        for _, m in corefunc.handle_command(message.messageChain, friend.id):
            # currently you can't quote friend messages..
            # the picture functionality doesn't seem to work too...
            await app.sendFriendMessage(friend=friend, message=m)


@app.receiver("TempMessage")
async def handle_tm(app: Mirai, group: Group, member: Member, message: TempMessage):
    await app.sendGroupMessage(group=group, message=[At(target=member.id), Plain(text="目前mirai的陌生人小窗功能有问题qaq：https://github.com/NatriumLab/python-mirai/issues/61")])
    return
    # TODO this functionality seems to be broken. https://github.com/NatriumLab/python-mirai/issues/61
    try:
        txt = message.messageChain.getFirstComponent(Plain).text.strip()[:2]
    except Exception:
        return
    if txt == "> ":
        for t, m in corefunc.handle_command(message.messageChain, member.id):
            if t == "DirectSend" or t == "TempSend":
                await app.sendTempMessage(group=group, member=member, message=m)
            elif t == "DirectReply" or t == "TempReply":
                await app.sendTempMessage(group=group, member=member, message=m, quoteSource=message.messageChain.getFirstComponent(Source))



@app.receiver("GroupMessage")
async def handle_gm(app: Mirai, group: Group, member: Member, message: GroupMessage):
    # TODO: 复读 禁言
    try:
        txt = message.messageChain.getFirstComponent(Plain).text.strip()[:2]
    except Exception:
        return
    if txt == "> ":
        for t, m in corefunc.handle_command(message.messageChain, member.id):
            if t == "DirectSend":
                await app.sendGroupMessage(group=group, message=m)
            elif t == "DirectReply":
                await app.sendGroupMessage(group=group, message=m, quoteSource=message.messageChain.getFirstComponent(Source))
            elif t == "TempSend" or t == "TempReply":
                await app.sendGroupMessage(group=group, message=[Plain(text="目前mirai的陌生人小窗功能有问题qwq：https://github.com/NatriumLab/python-mirai/issues/61")])
            elif t == "TempSend":
                await app.sendTempMessage(group=group, member=member, message=m)
            elif t == "TempReply":
                await app.sendTempMessage(group=group, member=member, message=m, quoteSource=message.messageChain.getFirstComponent(Source))

if __name__ == "__main__":
    app.run()