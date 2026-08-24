import subprocess
import json
import re
import socket
import threading


# lists the wireless networks detected by the interface
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
        check_connect = subprocess.run(["nmcli", "-g", "GENERAL.CONNECTION", "device", "show", interface], capture_output=True, text=True, check=False)
        if check_connect.stdout:
            if ssid in check_connect.stdout:
                return f"'{check_connect.stdout.strip()}' connected"
        proc = subprocess.run(["nmcli", "device", "wifi", "connect", ssid, "password", passwrd, "ifname", interface], capture_output=True, text=True, check=False)
        return proc

    output = connproc(ssid, passwrd, interface)
    try:
      if output.stderr:
          if "Error: 802-11-wireless-security.key-mgmt" in output.stderr:  # if it returns an error message related to connection security, the old connection will be deleted
              del_oldconn = subprocess.run(["nmcli", "connection", "delete", ssid], capture_output=True, text=True, check=False)
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
    except AttributeError:
        return output


# it enables bidirectional data transfer between two sockets
def forward(src, dst):
    try:
        while True:
            data = src.recv(8192)
            if not data:
                break
            dst.sendall(data)
    except:
        pass
    finally:
        src.close()
        dst.close()


# function that redirects the connection to the relevant interface
def connbridge(client_socket, interface):
    try:
        # receive the first request from the client
        request = client_socket.recv(8192)
        if not request:
            return

        # first line is being analyzed (method, target, protocol)
        first_line = request.split(b'\r\n')[0]
        words = first_line.split(b' ')
        if len(words) < 2:
            client_socket.close()
            return

        method = words[0].decode(errors='ignore')
        target = words[1].decode(errors='ignore')

        # HTTPS CONNECT method check
        if method == 'CONNECT':
            # example: duckduckgo.com:443 -> host='duckduckgo.com', port=443
            host, port = target.split(':')
            port = int(port)
            is_https = True
        else:
            # parsing HTTP qequests
            is_https = False
            host = ""
            port = 80
            for line in request.split(b'\r\n'):
                if line.lower().startswith(b'host:'):
                    host_info = line.split(b': ')[1].decode(errors='ignore')
                    if ":" in host_info:
                        host, port = host_info.split(":")
                        port = int(port)
                    else:
                        host = host_info
                    break

        if not host:
            client_socket.close()
            return

        # create a socket to connect to the target server
        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, interface)  # socket is connecting to the WLAN1 interface
        target_socket.connect((host, port))  # connect to the target server via WLAN1

        if is_https:
            # client is returned a "Connection Successful" response to initiate the SSL handshake
            client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        else:
            # plain HTTP, on the other hand, forwards the initial request packet to the destination exactly as it is
            target_socket.sendall(request)

        # initiate bidirectional tunneling
        threading.Thread(target=forward, args=(client_socket, target_socket), daemon=True).start()
        threading.Thread(target=forward, args=(target_socket, client_socket), daemon=True).start()
    except Exception as e:
        client_socket.close()


# function that initiates the proxy structure
def start_proxy(proxy_host='127.0.0.1', proxy_port=4030, bind_interface):
    bind_interface = bind_interface.encode()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((proxy_host, proxy_port))
    server.listen(200)
    print(f"HTTPS Proxy {proxy_host}:{proxy_port} activated. Output: {bind_interface.decode()}")

    while True:
        client_sock, addr = server.accept()
        threading.Thread(target=connbridge, args=(client_sock, bind_interface), daemon=True).start()

