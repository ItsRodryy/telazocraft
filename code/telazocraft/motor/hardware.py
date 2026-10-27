import ctypes
import os
import time
from ctypes import wintypes


class MemoriaProceso(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]


class Monitor:
    def __init__(self):
        self.anterior = None

    def medir(self, pid):
        if os.name != "nt" or not pid:
            return {"ram_mb": None, "cpu_pct": None}
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.restype = wintypes.HANDLE
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        k.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        p = ctypes.WinDLL("psapi", use_last_error=True)
        p.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(MemoriaProceso), wintypes.DWORD]
        handle = k.OpenProcess(0x0400 | 0x0010, False, pid)
        if not handle:
            return {"ram_mb": None, "cpu_pct": None}
        try:
            memoria = MemoriaProceso()
            memoria.cb = ctypes.sizeof(memoria)
            ok = p.GetProcessMemoryInfo(handle, ctypes.byref(memoria), memoria.cb)
            tiempos = [wintypes.FILETIME() for _ in range(4)]
            valido = k.GetProcessTimes(handle, *(ctypes.byref(t) for t in tiempos))
            cpu = None
            if valido:
                segundos = sum((t.dwHighDateTime << 32) + t.dwLowDateTime for t in tiempos[2:]) / 1e7
                ahora = time.monotonic()
                if self.anterior and self.anterior[0] == pid:
                    cpu = max(0, (segundos - self.anterior[2]) / (ahora - self.anterior[1]) / (os.cpu_count() or 1) * 100)
                self.anterior = (pid, ahora, segundos)
            return {"ram_mb": memoria.WorkingSetSize / 2**20 if ok else None, "cpu_pct": cpu}
        finally:
            k.CloseHandle(handle)
