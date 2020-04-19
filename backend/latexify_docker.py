import os, uuid
import redis

def compile_latex(src):
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    # phase I
    with r.lock("LATEX-1"):
        u = str(uuid.uuid4())
        os.system("ulimit -t 30")
        with open("./latex/texput.tex", "w") as f:
            f.write(src)
        os.system("docker container rm latex_container 2> /dev/null")
        timeout=False
        compile_return = os.system("docker run -m 1GB -v /Users/trebor/Desktop/Docker/mirai/backend/latex/texput.tex:/home/latex/texput.tex --name latex_container treborhuang/latex > /dev/null")
    if timeout:
        r.close()
        return ("Timeout", (), "")
    # phase II
    with r.lock("LATEX-2"):
        os.system("rm -dfR ./latex_output/") # if you don't delete the folder, docker cp will just create a latex/ folder inside the latex_output/ folder.
        copy_return = os.system("docker cp latex_container:/home/latex/ ./latex_output/")
        os.system("docker container rm latex_container > /dev/null")
        if compile_return != 0:
            with open(f"./latex_output/texput.log", "r") as f:
                logs = f.read()
    if compile_return != 0:
        r.close()
        error_log = logs[logs.find("\n!"):logs.find("Here is how much of")]
        if error_log:
            return ("Failed", (compile_return, copy_return), error_log.strip())
        return ("Failed-NoError", (compile_return, copy_return), logs)
    # phase III
    with r.lock("LATEX-3"):
        convert_return = os.system(f"convert -density 500 ./latex_output/texput.pdf ./latex_process/{u}.jpeg")
        resize_return = os.system(f"convert ./latex_process/{u}.jpeg -resample 300 ./latex_process/resized{u}.jpeg")
    r.close()
    if convert_return or resize_return:
        return ("Failed", (compile_return, copy_return, convert_return, resize_return), "请告诉我的主人：" + str(((compile_return, copy_return, convert_return, resize_return))))
    return ("Done", (compile_return, copy_return, convert_return, resize_return), u)

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
