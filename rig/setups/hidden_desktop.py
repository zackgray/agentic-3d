"""Launches GUI Blender on a hidden Windows desktop, so a batch never shows a window on the workstation.

A Windows session can hold several desktops; only the input desktop is ever displayed. Blender
started on a second desktop ("agentic3d-rig") runs with a real GPU context and a real window, so
the MCP servers and their screenshot tools work as on screen, but nothing ever appears. On the workstation it
opens maximized at the same 3840 x 2054 client size as on the visible desktop (checked 2026-11-17),
so the window screenshots the model receives keep their size. Moving a window off-screen after
launch was tried first and fails: Blender shows its window before it handles any outside request.

The returned object has the subset of subprocess.Popen the setups use: pid, returncode, poll(),
wait(), kill(). Elsewhere than Windows it is a plain Popen.
"""
import os
import subprocess
import sys

DESKTOP = "agentic3d-rig"

if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes as w
    import msvcrt

    _k32, _u32 = ctypes.windll.kernel32, ctypes.windll.user32
    _u32.CreateDesktopW.restype = w.HANDLE
    _k32.WaitForSingleObject.restype = w.DWORD
    _desktop = None

    class _StartupInfo(ctypes.Structure):
        _fields_ = [("cb", w.DWORD), ("lpReserved", w.LPWSTR), ("lpDesktop", w.LPWSTR), ("lpTitle", w.LPWSTR),
                    ("dwX", w.DWORD), ("dwY", w.DWORD), ("dwXSize", w.DWORD), ("dwYSize", w.DWORD),
                    ("dwXCountChars", w.DWORD), ("dwYCountChars", w.DWORD), ("dwFillAttribute", w.DWORD),
                    ("dwFlags", w.DWORD), ("wShowWindow", w.WORD), ("cbReserved2", w.WORD),
                    ("lpReserved2", ctypes.c_void_p), ("hStdInput", w.HANDLE), ("hStdOutput", w.HANDLE),
                    ("hStdError", w.HANDLE)]

    class _ProcessInfo(ctypes.Structure):
        _fields_ = [("hProcess", w.HANDLE), ("hThread", w.HANDLE), ("dwProcessId", w.DWORD),
                    ("dwThreadId", w.DWORD)]


class HiddenProcess:
    def __init__(self, cmd: list[str], env: dict, log_file):
        global _desktop
        if _desktop is None:  # opens the desktop if it already exists; kept open for the process's life
            _desktop = _u32.CreateDesktopW(DESKTOP, None, None, 0, 0x10000000, None)  # GENERIC_ALL
            if not _desktop:
                raise OSError(f"CreateDesktop failed: {ctypes.GetLastError()}")
        out = msvcrt.get_osfhandle(log_file.fileno())
        os.set_handle_inheritable(out, True)
        si = _StartupInfo(cb=ctypes.sizeof(_StartupInfo), lpDesktop=DESKTOP, dwFlags=0x100,  # USESTDHANDLES
                          hStdInput=None, hStdOutput=out, hStdError=out)
        block = "".join(f"{k}={v}\0" for k, v in env.items()) + "\0"
        self._pi = _ProcessInfo()
        ok = _k32.CreateProcessW(None, ctypes.create_unicode_buffer(subprocess.list2cmdline(cmd)), None, None,
                                 True, 0x400, ctypes.create_unicode_buffer(block), None,  # UNICODE_ENVIRONMENT
                                 ctypes.byref(si), ctypes.byref(self._pi))
        if not ok:
            raise OSError(f"CreateProcess failed: {ctypes.GetLastError()}")
        _k32.CloseHandle(self._pi.hThread)
        self.pid = self._pi.dwProcessId
        self.returncode = None

    def poll(self):
        if self.returncode is None and _k32.WaitForSingleObject(self._pi.hProcess, 0) == 0:
            code = w.DWORD()
            _k32.GetExitCodeProcess(self._pi.hProcess, ctypes.byref(code))
            self.returncode = code.value
        return self.returncode

    def wait(self, timeout: float | None = None):
        ms = 0xFFFFFFFF if timeout is None else int(timeout * 1000)
        if _k32.WaitForSingleObject(self._pi.hProcess, ms) != 0:
            raise subprocess.TimeoutExpired("blender", timeout)
        return self.poll()

    def kill(self):
        if self.poll() is None:
            _k32.TerminateProcess(self._pi.hProcess, 1)


def launch(cmd: list[str], env: dict, log_file):
    if sys.platform != "win32":
        return subprocess.Popen(cmd, env=env, stdout=log_file, stderr=subprocess.STDOUT)
    return HiddenProcess(cmd, env, log_file)
