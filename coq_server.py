import pexpect, re
import json
import threading
from flask import Flask, jsonify, request
class Coq:
    def start(self):
        self.coq = pexpect.spawn('bash -c "coqtop | cat ; exit"', echo=False)
        self.coq.expect("Coq <")

    def stop(self):
        self.coq.close()

    def __init__(self):
        self.start()

    def _input(self, cmd):
        self.coq.sendline(cmd)
        self.coq.expect(re.compile(rb"^.+? <", flags=re.RegexFlag.M), timeout=5)
        return self.coq.before.decode('utf-8')

    def sendline(self, cmd):
        if not self.coq.isalive():
            self.start()
        try:
            ret = self._input(cmd)
        except pexpect.TIMEOUT:
            self.coq.sendcontrol('C')
            self.coq.expect(re.compile(rb"^.+? <", flags=re.RegexFlag.M))
            return ("Failed", "Time out.")
        except pexpect.EOF:
            self.coq.close()
            return ("Failed", "Coq stopped.")
        return ("Success", ret)

sessions = {}

app = Flask(__name__)
@app.route("/")
def index():
    return jsonify({"sessions": str(sessions)})

@app.route("/create_session", methods=["POST"])
def create():
    if 'id' not in request.json:
        return "No id given", 400
    if request.json['id'] in sessions:
        return "Session already started", 409
    sessions[request.json['id']] = (Coq(), threading.Lock())
    return jsonify({"status": "Success", "session_id": request.json['id']}), 201

@app.route("/query", methods=["POST"])
def query():
    if 'id' not in request.json or 'cmd' not in request.json:
        return "Bad query format.", 400
    if request.json['id'] not in sessions:
        return "No such session.", 404
    with sessions[request.json['id']][1]:
        status, ret = sessions[request.json['id']][0].sendline(request.json['cmd'])
        return jsonify({"status": status, "content": ret})

@app.route("/release_session", methods=["POST"])
def release():
    if 'id' not in request.json:
        return "Bad query format.", 400
    if request.json['id'] not in sessions:
        return "No such session.", 404
    with sessions[request.json['id']][1]:
        sessions[request.json['id']][0].stop()
        del sessions[request.json['id']]
        return jsonify({"status": "Success"})

if __name__ == "__main__":
    app.run(port="9001")
