import os
from celery.exceptions import SoftTimeLimitExceeded

def compile_latex(src):
    os.system("rm ./latex_output/*")
    os.system("ulimit -t 30")
    with open("latex/texput.tex", "w") as f:
        f.write(src)
    os.system("docker container rm latex_container 2> /dev/null")
    try:
        compile_return = os.system("docker run -m 1GB -v /Users/trebor/Desktop/coolq/latex/texput.tex:/home/latex/texput.tex --name latex_container treborhuang/latex --rm")
    except SoftTimeLimitExceeded:
        return ("Timeout", (), "")
    copy_return = os.system("docker cp latex_container:/home/latex/ ./latex_output/")
    # The results will be in ./latex_output/latex/texput.*
    if compile_return != 0:
        with open(f"./latex_output/latex/texput.log", "r") as f:
            logs = f.read()
        error_log = logs[logs.find("\n!"):logs.find("Here is how much of")]
        if error_log:
            return ("Failed", (compile_return, copy_return), error_log.strip())
        return ("Failed-NoError", (compile_return, copy_return), logs)
    convert_return = os.system("convert -density 500 ./latex_output/latex/texput.pdf ./latex_output/latex/texput.jpeg")
    resize_return = os.system("convert ./latex_output/latex/texput.jpeg -resample 300 ./img/final.jpeg")
    return ("Done", (compile_return, copy_return, convert_return, resize_return), "[CQ:image,file=file:///G:\\final.jpeg]")

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
