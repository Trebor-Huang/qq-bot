from mirai import MessageChain, Plain, Image
import latexify_docker

manual = {
    "total":
"""好耶！""",
    "render": "这里会有这个命令的帮助"
#"""渲染LaTeX文字。如果希望渲染公式请用 $ ... $ 或者 \\( ... \\) 括起来；不支持行间公式（即 $$ ... $$ 或者 \\[ ... \\] 括起的公式），可以用 $ \\displaystyle ... $ 代替。

#\t如果希望添加LaTeX宏包，可以用 "\\begin{bot-usepackage} 包1 包2 ... \\end{bot-usepackage}" + 正文 声明希望用到的宏包，如果没有安装，可以联系bot作者。

#\t如果希望添加LaTeX preamble里的内容，可以类似地用 "\\begin{bot-defs} ... \\end{bot-defs}" + 正文 添加。这个声明必须在bot-usepackage声明的后面。""",
}

def handle_command(command: MessageChain, user: int):
    # protocol: a list of
    # ("DirectReply", [message chain]) -> replies with the message
    # ("DirectSend", [message chain]) -> merely sends the message
    # ("TempReply", [message chain]) -> replies in temp message
    # ("TempSend", [message chain]) -> sends temp message
    com_split = command.getFirstComponent(Plain).text.strip()[2:].split(maxsplit=1)
    c = com_split[0].strip().lower()
    if c == "render":
        if len(com_split) > 1:
            return docker_latex(com_split[1].strip())
        return [
            ("DirectReply", [Plain(text="render命令的帮助已经私聊")]),
            ("TempReply", [Plain(text=manual["render"])])
        ]
    return [("DirectReply", [Plain(text=manual["total"])])]

def docker_latex(src: str):
    pkgs = ()
    defs = ""
    try:
        if src[:22] == "\\begin{bot-usepackage}":
            src = src[22:]
            pkg, src = src.split("\\end{bot-usepackage}", maxsplit=1)
            pkgs = tuple(pkg.split())
        if src[:16] == "\\begin{bot-defs}":
            src = src[16:]
            defs, src = src.split("\\end{bot-defs}", maxsplit=1)
    except ValueError:
        return [("DirectReply", [Plain(text="格式不正确喵～")])]
    src_ltx = latexify_docker.get_source(src, pkgs, defs)
    r, rets, l = latexify_docker.compile_latex(src_ltx)
    print(r, rets)
    if r == "Timeout":
        return [("DirectReply", [Plain(text="TLE~qwq")])]
        # timeout_record(event['user_id'])
    elif r == "Failed":
        return [
            ("DirectReply", [Plain(text="出错了qaq")]),
            ("TempReply", l)
        ]
    elif r == "Failed-NoError":
        return [
            ("DirectReply", [Plain(text="出错了qaq，而且不是一般的编译错误，跟我主人说吧qwq")])
        ]
    elif r == "Done":
        return [
            ("DirectReply", [Image.fromFileSystem(path=f"./latex_process/resized{l}.jpeg")])
        ]
