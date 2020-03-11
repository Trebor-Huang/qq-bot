import os
from flask import Flask
from flask import request
from pexpect.popen_spawn import PopenSpawn

app = Flask(__name__)
child = PopenSpawn("ord.exe")
child.sendline("opts psi")
child.expect("ordCalc> ")
child.expect("ordCalc> ")

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/ord', methods=['GET'])
def ordinal():
    if 'exit' in request.args['cmd'] or 'quit' in request.args['cmd']:
        return "（这么想让我退出吗qaq"
    if any(i in request.args['cmd'] for i in ['cmdCheck', 'cppList', 'export', 'log', 'read', 'save', 'setDbg', 'yydebug']):
        return "功能被阉了（"
    child.sendline(request.args['cmd'])
    child.sendline()
    r = child.expect(['Type ENTER to Continue:', 'ordCalc> '])
    re = child.before.decode('utf-8')
    if r == 1 and len(re) == 0:
        child.expect('ordCalc> ')
        return "（没有输出）"
    while not (r == 1 and len(child.before) == 0):
        print(child.before)
        if r == 0:
            child.sendline()
        else:
            re += 'ordCalc> '
        r = child.expect(['Type ENTER to Continue:', 'ordCalc> '])
        re += child.before.decode('utf-8')
    return re[:-9]
    
app.run(host='192.168.56.101', port=5679, debug=True)
