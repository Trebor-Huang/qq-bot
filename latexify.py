import os, time
todevnull = " > /dev/null"
def latexify(source, filename, size=256, verbose=False, **preamble):
    tempfilename = "TEMP" + hex(hash(source) ^ time.time_ns())[1:]
    with open(f"{tempfilename}.tex", "w") as file:
        file.write(get_preamble(**preamble) + source + "\n\\end{document}")
    if os.system(f"xelatex -interaction nonstopmode -halt-on-error {tempfilename}.tex  > /dev/null"):
        with open(f"{tempfilename}.log", "r") as file:
            error = file.read()
            print(error)
        raise RuntimeError(error[error.find("\n!"):error.find("Here is how much of")])
    os.system(f"convert -density {size*8} {tempfilename}.pdf {tempfilename}.jpeg")
    os.system(f"convert {tempfilename}.jpeg -resample {size} {filename}.jpeg")
    os.system("rm *.tex *.aux *.log *.pdf *.jpeg")

def get_preamble(usepackage=None, definitions=""):
    if usepackage is None:
        usepackage = ()
    definitions += "\n\\newcommand{\\R}{\\mathbb R}\n\\newcommand{\\Q}{\\mathbb Q}\n\\newcommand{\\Z}{\\mathbb Z}\n\\newcommand{\\N}{\\mathbb N}"
    usepackage += ("amssymb", "amsmath", "amsfonts")
    return r"\documentclass[varwidth,border=1pt]{standalone}" + \
      "\n\\usepackage{" + ", ".join(usepackage) + "}\n\\usepackage{xeCJK}\n" + definitions + "\n\\begin{document}\n"

if __name__ == "__main__":
    print(latexify(r"你好！$\displaystyle \int_{-\infty}^\infty e^{-x^2} = \sqrt{\pi}.$Yes.", "test", verbose=False))
