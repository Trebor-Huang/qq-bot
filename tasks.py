import os, time, requests
from celery_config import app

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

def latexify(source, filename, size=512, verbose=False, **preamble):
    tempfilename = "TEMP" + hex(hash(source) ^ time.time_ns())[1:]
    with open(f"{tempfilename}.tex", "w") as file:
        file.write(get_preamble(**preamble) + source + "\n\\end{document}")
    if os.system(f"xelatex -interaction nonstopmode -halt-on-error {tempfilename}.tex  > /dev/null"):
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
    definitions += "\n\\newcommand{\\R}{\\mathbb R}\n\\newcommand{\\Q}{\\mathbb Q}\n\\newcommand{\\Z}{\\mathbb Z}\n\\newcommand{\\N}{\\mathbb N}"
    usepackage += ("amssymb", "amsmath", "amsfonts")
    return r"\documentclass[varwidth,border=1pt]{standalone}" + \
      "\n\\usepackage{" + ", ".join(usepackage) + "}\n\\usepackage{xeCJK}\n" + definitions + "\n\\begin{document}\n"

@app.task
def pdf_doc(title, doc):
    doc = f"========\n{title}\n========\n" + doc.replace("\n    ", "\n")
    docname = "DOC" + hex(hash(doc))[1:] 
    with open(docname + ".rst", "w") as rst:
        rst.write(doc)
    s1 = os.system(f"rst2pdf {docname}.rst")
    s2 = os.system(f"convert -density 256 {docname}.pdf -antialias ./img/{title}.jpeg")
    s3 = os.system(f"rm *.rst *.pdf")
    return (s1, s2, s3)


@app.task
def render_latex_and_send(res, event, latex_packages, resend=False):
    try:
        filename = "TEMP" + hex(hash(res) ^ time.time_ns())[1:]
        r = latexify(res, filename="./img/" + filename, definitions="\\textwidth=7cm", usepackage=latex_packages)
        try:
            bot.delete_msg(message_id=event['message_id'])
            if resend:
                bot.send_private_msg(user_id=event['user_id'], message=event['message'])
        except Exception:
            print("Failed to recall latex spam.")
        bot.send(event=event, message=f"[CQ:image,file=file:///G:\\{filename}.jpeg]", auto_escape=False)
        return 0, r
    except RuntimeError as e:
        bot.send_private_msg(user_id=event['user_id'], message=event['message'])
        bot.send_private_msg(user_id=event['user_id'], message = "错误如下：\n" + str(e).strip(), auto_escape=True)
        try:
            bot.delete_msg(message_id=event['message_id'])
        except Exception:
            print("Failed to recall latex spam.")
        bot.send(event=event, message="LaTeX有误")
        return 1

if __name__ == "__main__":
    print(latexify(r"你好！$\displaystyle \int_{-\infty}^\infty e^{-x^2} = \sqrt{\pi}.$Yes.", "test", verbose=False))
