"""Free check that the sandbox's walls hold (no model calls). Agent-style code tries to get out; every
attempt must fail, and the audit log must record the ones it watches. Run from the repo root:

    python tests/sandbox_walls.py
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, ".")
from rig.blender import blender_path, make_starting_scene  # noqa: E402
from rig.setups.sandbox import SandboxHarnessSetup  # noqa: E402

PROBE = r'''
import json, os, socket, subprocess
r = {}
def attempt(key, fn):
    try:
        r[key] = "allowed: " + repr(fn())[:80]
    except Exception as e:
        r[key] = "blocked: " + type(e).__name__
attempt("dns", lambda: socket.getaddrinfo("api.anthropic.com", 443))
attempt("connect", lambda: socket.create_connection(("1.1.1.1", 443), timeout=3))
attempt("write_root", lambda: open("/opt/blender/x", "w"))
attempt("write_home", lambda: open("/home/agent/x", "w"))
attempt("write_harness", lambda: open("/side/harness_lib.py", "a"))
attempt("write_run", lambda: open("/work/ok.txt", "w").write("ok"))
attempt("subprocess", lambda: subprocess.run(["id", "-u"], capture_output=True, text=True).stdout.strip())
r["uid"] = os.getuid()
r["key_in_env"] = any("ANTHROPIC" in k or "sk-ant" in v for k, v in os.environ.items())
r["host_drives"] = [p for p in ("/mnt/c", "/run/desktop/mnt/host/c", "/host_mnt") if os.path.exists(p)]
r["mounts"] = sorted({l.split()[1] for l in open("/proc/mounts") if l.split()[1].startswith(("/work", "/side", "/mnt", "/host"))})
r["interfaces"] = sorted(os.listdir("/sys/class/net"))
t = bpy.data.texts.new("autorun.py"); t.write("print('pwned')"); t.use_module = True
print("WALLS", json.dumps(r))
'''

exe = blender_path()
work = Path("runs/_smoke/walls")
shutil.rmtree(work, ignore_errors=True)
work.mkdir(parents=True)
scene = work / "scene.blend"
make_starting_scene(exe, "empty", scene)
h = SandboxHarnessSetup(exe, timeout=30)
h.start(work, scene)
h.initial_context()
out = h.call("blender", {"code": PROBE, "done": False})
texts = h.call("blender", {"code": "print('TEXTS', [t.name for t in bpy.data.texts])", "done": False})
h.stop()
r = json.loads(out.text.split("WALLS ", 1)[1].splitlines()[0])
audit = (work / "sandbox_audit.log").read_text(encoding="utf-8")

fails = []


def expect(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  ({detail})" if detail else ""))
    if not cond:
        fails.append(name)


for k in ("dns", "connect", "write_root", "write_home", "write_harness"):
    expect(f"{k} blocked", r[k].startswith("blocked"), r[k])
expect("run folder writable", r["write_run"].startswith("allowed") and (work / "ok.txt").is_file(), r["write_run"])
expect("not root", r["uid"] == 1000, r["uid"])
expect("API key not in the environment", r["key_in_env"] is False)
expect("no host drives visible", not r["host_drives"], r["host_drives"])
expect("only the run folder and harness code mounted", r["mounts"] == ["/side", "/work"], r["mounts"])
expect("no network interface but loopback", r["interfaces"] == ["lo"], r["interfaces"])
expect("auto-run script stripped before save", "TEXTS []" in texts.text, texts.text[:200])
for ev in ("socket.getaddrinfo", "socket.connect", "write /opt/blender/x", "write /home/agent/x",
           "write /side/harness_lib.py", "subprocess.Popen"):
    expect(f"audit logged {ev}", ev in audit)
expect("audit did not log the run-folder write", "/work/ok.txt" not in audit)
print("\n%d failed" % len(fails) if fails else "\nall passed")
sys.exit(1 if fails else 0)
