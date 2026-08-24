import subprocess
import json
import re


def parse_iw_scan(interface):
    cmd = ["iw", "dev", interface, "scan"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)

    if proc.returncode != 0:
        raise RuntimeError(f"iw scan failed: {proc.returncode}: {proc.stderr.strip()}")  # in case of an error, an empty list may be returned or an exception may be thrown

    lines = proc.stdout.splitlines()

    results = []
    current = None

    # parse BSSID and SSID
    bss_re = re.compile(r"^BSS\s+([0-9A-Fa-f:]{17})")
    ssid_re = re.compile(r"^\s*SSID:\s*(.*)$")

    for line in lines:
        m = bss_re.match(line)
        if m:
            if current:
                results.append(current)
            current = {"bssid": m.group(1), "ssid": ""}  # if the SSID is empty, it may be private
            continue

        if current is None:  # there is no BSS block yet
            continue

        m2 = ssid_re.match(line)
        if m2:
            current["ssid"] = m2.group(1)
            continue

        # if re.match(r"^\s*signal:", line):
        #     current["signal"] = line.split(":",1)[1].strip()

    # add the last block
    if current:
        results.append(current)
    return results

