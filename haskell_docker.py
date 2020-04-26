import os, hashlib
from celery.exceptions import SoftTimeLimitExceeded

def runghc(src, infile):
    usrc = hashlib.sha256(src.encode("utf-8")).hexdigest()
    uin = hashlib.sha256(infile.encode("utf-8")).hexdigest()
    uout = hashlib.sha256((usrc + uin).encode("utf-8")).hexdigest()
    if not os.path.isfile("./srcfolder/" + uin + ".in"):
        with open("./srcfolder/" + uin + ".in", "w") as fin:
            fin.write(infile)
    if not os.path.isfile("./srcfolder/" + usrc + ".hs"):
        with open("./srcfolder/" + usrc + ".hs", "w") as fsrc:
            fsrc.write(src)
    ret = os.system(f"docker run --rm --name haskell_{uout} -m 256MB --env SRC={usrc} --env IN={uin} --env OUT={uout} -v $(pwd)/srcfolder:/haskell haskell:latest")
    with open("./srcfolder/" + usrc + ".log") as f:
        log = f.read().strip()
    if not os.path.isfile("./srcfolder/" + uout + ".out"):
        return ("No-output", ret, "", log)
    else:
        with open("./srcfolder/" + uout + ".out") as f:
            output = f.read().strip()
        return ("Done", ret, output, log)

if __name__ == "__main__":
    src = """module Main where

main :: IO ()
main = do
  putStrLn "Hello world!"
  r <- getLine
  putStrLn r
"""
    print(runghc(src, ""))
