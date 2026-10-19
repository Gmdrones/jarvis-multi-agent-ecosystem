"""JARVIS Community MVP. Local-only, standard-library dashboard."""
import argparse, hashlib, json, os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone

ROOT=Path.home()/"JarvisCommunity"
VAULT=ROOT/"ObsidianVault"
MISSIONS=ROOT/"missions.json"

def init():
    for name in ["Agents","Missions","Memory","Logs"]:
        (VAULT/name).mkdir(parents=True,exist_ok=True)
    agents={
      "Supervisor":"Plans and delegates missions; never executes without approval.",
      "Planner":"Breaks tasks into verifiable steps.",
      "Executor":"Executes approved local demo actions only.",
      "Memory":"Searches local mission history before planning.",
      "Auditor":"Reviews outputs, duplicates and evidence.",
      "Sentinel":"Checks safety, permissions and scope."
    }
    for name,desc in agents.items():
        p=VAULT/"Agents"/(name+".md")
        if not p.exists(): p.write_text("# "+name+"\n\n"+desc+"\n",encoding="utf-8")
    home=VAULT/"JARVIS.md"
    if not home.exists(): home.write_text("# JARVIS Community\n\n"+"\n".join("[["+n+"]]" for n in agents)+"\n",encoding="utf-8")
    if not MISSIONS.exists(): MISSIONS.write_text("[]",encoding="utf-8")
    print("Initialized",VAULT)

def missions():
    init()
    return json.loads(MISSIONS.read_text(encoding="utf-8"))

def add(task):
    task=task.strip()
    if not task: raise ValueError("Empty task")
    data=missions()
    digest=hashlib.sha256(task.casefold().encode()).hexdigest()
    for m in data:
        if m["hash"]==digest: return {"status":"duplicate","mission":m}
    record={"id":len(data)+1,"task":task,"hash":digest,"status":"pending_approval","created_at":datetime.now(timezone.utc).isoformat()}
    data.append(record)
    MISSIONS.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    (VAULT/"Missions"/("mission-"+str(record["id"])+".md")).write_text("# Mission "+str(record["id"])+"\n\n"+task+"\n\nStatus: pending approval\n",encoding="utf-8")
    return {"status":"created","mission":record}

PAGE="""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>JARVIS Command Center</title><style>body{font:16px system-ui;background:#07141c;color:#d7faff;max-width:900px;margin:6vh auto;padding:20px}h1{color:#39d8f2;letter-spacing:.15em}section{background:#102632;border:1px solid #27617a;border-radius:14px;padding:22px;margin:18px 0}input{padding:13px;width:65%;background:#061923;color:white;border:1px solid #3986a0}button{padding:13px;background:#19b6d1;color:#00131b;border:0;font-weight:bold;cursor:pointer}small{color:#9ac2cf}</style><h1>◉ JARVIS / COMMUNITY</h1><small>LOCAL MISSION CONTROL • DEMO MODE • APPROVAL REQUIRED</small><section><h2>Agents online (templates)</h2>Supervisor · Planner · Executor · Memory · Auditor · Sentinel</section><section><h2>Create a mission</h2><form id="f"><input id="task" placeholder="Describe a safe demo mission" required><button>Create</button></form><pre id="out"></pre></section><section><h2>Mission history</h2><pre id="history"></pre></section><script>async function refresh(){let r=await fetch('/api/missions');document.getElementById('history').textContent=JSON.stringify(await r.json(),null,2)}document.getElementById('f').onsubmit=async e=>{e.preventDefault();let r=await fetch('/api/missions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:document.getElementById('task').value})});document.getElementById('out').textContent=JSON.stringify(await r.json(),null,2);refresh()};refresh()</script></html>"""

class Handler(BaseHTTPRequestHandler):
    def respond(self,code,obj):
        payload=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(code);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(payload)));self.end_headers();self.wfile.write(payload)
    def do_GET(self):
        if self.path=="/api/missions":return self.respond(200,missions())
        if self.path!="/":return self.respond(404,{"error":"not found"})
        body=PAGE.encode();self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
    def do_POST(self):
        if self.path!="/api/missions":return self.respond(404,{"error":"not found"})
        try:
            length=int(self.headers.get("Content-Length","0"))
            if length>10000:raise ValueError("Too long")
            payload=json.loads(self.rfile.read(length))
            return self.respond(200,add(payload.get("task","")))
        except (ValueError,KeyError,json.JSONDecodeError) as exc:return self.respond(400,{"error":str(exc)})

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("command",choices=["init","serve","mission"]);parser.add_argument("text",nargs="?");args=parser.parse_args()
    if args.command=="init":init()
    elif args.command=="mission":print(json.dumps(add(args.text or ""),ensure_ascii=False))
    else:
        init();print("Open http://127.0.0.1:8765");HTTPServer(("127.0.0.1",8765),Handler).serve_forever()
