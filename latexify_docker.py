import os, hashlib
from celery.exceptions import SoftTimeLimitExceeded
import custom_settings
import redis

def compile_latex(src):
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    u = hashlib.sha256(src.encode('utf-8')).hexdigest()
    if not os.path.isfile(f"{custom_settings.CQ_IMG_DIR}{u}.jpeg"):
        # phase I
        with r.lock("LATEX-1"):
            with open(f"latex/{u}.tex", "w") as f:
                f.write(src)
            timeout=False
            try:
                compile_return = os.system(f"ulimit -t 30 ; docker run -m 1GB -v $(pwd)/latex/{u}.tex:/home/latex/texput.tex --name latex_container{u} treborhuang/latex > /dev/null")
            except SoftTimeLimitExceeded:
                timeout=True
        if timeout:
            r.close()
            return ("Timeout", (), "")
        # phase II
        with r.lock("LATEX-2"):
            os.system(f"rm -rf ./latex_output/{u} | grep -v No")
            copy_return = os.system(f"docker cp latex_container{u}:/home/latex/ ./latex_output/{u}/")
            os.system(f"docker container rm latex_container{u} > /dev/null")
            if compile_return != 0:
                with open(f"./latex_output/{u}/texput.log", "r") as f:
                    logs = f.read()
        if compile_return != 0:
            r.close()
            error_log = logs[logs.find("\n!"):logs.find("Here is how much of")]
            if error_log:
                return ("Failed", (compile_return, copy_return), error_log.strip())
            return ("Failed-NoError", (compile_return, copy_return), logs)
        # phase III
        with r.lock("LATEX-3"):
            convert_return = os.system(f"convert -density 500 ./latex_output/{u}/texput.pdf ./latex_process/{u}.jpeg")
            resize_return = os.system(f"convert ./latex_process/{u}.jpeg -resample 400 {custom_settings.CQ_IMG_DIR}{u}.jpeg")
        r.close()
        if convert_return or resize_return:
            return ("Failed", (compile_return, copy_return, convert_return, resize_return), "请告诉我的主人：" + str(((compile_return, copy_return, convert_return, resize_return))))
    else:
        r.close()
        return ("Cached", (), f"[CQ:image,file={u}.jpeg]")
    return ("Done", (compile_return, copy_return, convert_return, resize_return), f"[CQ:image,file={u}.jpeg]")

def get_preamble(usepackage=(), definitions=""):
    definitions += "\n\\newcommand{\\R}{\\mathbb R}\n\\newcommand{\\Q}{\\mathbb Q}\n\\newcommand{\\Z}{\\mathbb Z}\n\\newcommand{\\N}{\\mathbb N}\n\\newcommand{\\e}{\\mathrm e}\n"
    usepackage += ("amssymb", "amsmath", "amsfonts")
    return r"\documentclass[varwidth,border=2pt]{standalone}" + \
      "\n\\usepackage{" + ", ".join(usepackage) + "}\n\\usepackage{xeCJK}\n" + definitions + "\n\\begin{document}\n"


def get_source(source, usepackage=(), definitions=""):
    return get_preamble(usepackage, definitions) + source + "\n\\end{document}\n"

if __name__ == "__main__":
    src_test = get_source("$ a^2 + b^2 $")
    compile_latex(src_test)
