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


# function to connect the network interface to the selected network
def connect_wifi(ssid, passwrd, interface):
    # connection function
    def connproc(ssid, passwrd, interface):
        cmd = ["nmcli", "device", "wifi", "connect", ssid, "password", passwrd, "ifname", interface]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        return proc

    output = connproc(ssid, passwrd, interface)
    if output.stderr:
        if "Error: 802-11-wireless-security.key-mgmt" in output.stderr:  # if it returns an error message related to connection security, the old connection will be deleted
            del_oldconn = subprocess.run(["nmcli", "connection", "delete", ssid], text=True, check=False)
            if del_oldconn.stderr:
                if "Error: unknown connection" in del_oldconn.stderr:  # link to be deleted may not be found with its full name. Alternatively, that link may still be present in the interface
                    # SSIDs of previously connected devices are listed
                    iface_connlist = subprocess.run(["nmcli", "-t", "-f", "NAME,DEVICE", "connection", "show"], capture_output=True, text=True, check=True)
                    connections = []
                    for line in result.stdout.splitlines():
                        name, iface = line.split(":", 1)
                        if iface == interface:
                            connections.append(name)
                    # devices connected to the interface are being deleted
                    for connection in connections:
                        del_oldconn = subprocess.run(["nmcli", "connection", "delete", connection], text=True, check=False)
            else:
                output = connproc(ssid, passwrd, interface)
                if output.stdout:
                    return output.stdout
        else:
            raise RuntimeError(f"nmcli connection failed: {output.stderr.strip()}")
    else:
        return output.stdout


