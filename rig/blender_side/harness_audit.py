"""Audit log for agent code in the sandbox (harness-sandbox only). Records, never blocks: the
container is the wall (no network, read-only root, one writable folder), and an attempt to reach past
it is a finding worth seeing even when the wall holds. Active only while the agent's code runs, so
Blender's and the server's own work isn't logged.

Recorded: writes outside /work and /tmp, sockets, starting processes, signals, and loading native
code through ctypes.
"""
import os
import sys

ALLOWED = ("/work", "/tmp")
WATCH = ("socket.connect", "socket.bind", "socket.getaddrinfo", "socket.sendto", "subprocess.Popen",
         "os.system", "os.exec", "os.spawn", "os.posix_spawn", "os.fork", "os.forkpty", "os.kill",
         "pty.spawn", "ctypes.dlopen", "ctypes.dlsym", "urllib.Request")
WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC
CAP = 50

active = False
events = []


def _record(event, detail):
    if len(events) < CAP:
        events.append(f"{event} {detail}"[:240])


def _writes(mode, flags):
    if isinstance(mode, str) and any(c in mode for c in "wax+"):
        return True
    return isinstance(flags, int) and bool(flags & WRITE_FLAGS)


def _hook(event, args):
    if not active:
        return
    try:
        if event == "open":
            path, mode, flags = (tuple(args) + (None, None, None))[:3]
            if isinstance(path, (str, bytes)) and _writes(mode, flags):
                p = os.path.abspath(os.fsdecode(path))
                if not any(p == a or p.startswith(a + "/") for a in ALLOWED):
                    _record("write", p)
        elif event in WATCH:
            _record(event, repr(args)[:200])
    except Exception:  # the log must never break the agent's call
        pass


def install():
    sys.addaudithook(_hook)


def take():
    """This call's events, cleared for the next."""
    out = list(events)
    events.clear()
    return out
