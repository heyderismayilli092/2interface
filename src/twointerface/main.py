import argparse
import twointerface.utils
import json
import os
import sys
import time

# '2interface' software arguments
def main(interface, proxy_port):
    parser = argparse.ArgumentParser(description="2interface -- A Python-based Linux network manager for Wi-Fi discovery, connection management, policy-based routing, and per-application traffic routing")

    # arguments
    parser.add_argument('--scanwifi', action='store_true', help='Lists the wireless networks detected by the network interface')
    parser.add_argument('--interface-address', action='store_true', help='Displays the interface\'s local IP address')
    parser.add_argument('--interface-gateway', action='store_true', help='Finds the IPv4 default gateway of the interface')
    parser.add_argument('--start-proxy', action='store_true', help='It opens a proxy service to route the traffic of any application to the wireless network that the interface is connected to')
    parser.add_argument('--scan-interface', action='store_true', help='It finds active devices by scanning the network interface')
    parser.add_argument('--interface-iplookup', action='store_true', help='External IP address of the wireless network to which the network interface is connected is obtained')
    parser.add_argument('--connect-wifi', action='store_true', help='Displays the interface\'s local IP address')
    parser.add_argument("--ssid", type=str, help="SSID value")
    parser.add_argument("--password", type=str, help="Password")
    args = parser.parse_args()

    # '--scanwifi'
    if args.scanwifi:
        # controls
        if os.getuid() != 0:
            parser.error("Run with root access !")
        if not utils.check_interface(interface):
            parser.error(f"The interface '{interface}' is not active or connected to any network !")
        # scan process
        print("Scanning wireless networks...")
        output = utils.scan_wireless_iw(interface)
        for network in output:
            print(f"- {network}")

    # '--interface-address'
    elif args.interface_address:
        # controls
        if not utils.check_interface(interface):
            parser.error(f"The interface '{interface}' is not active or connected to any network !")
        ip_address = utils.iface_ipaddr(interface)
        print(ip_address)

    # '--interface-gateway'
    elif args.interface_gateway:
        # controls
        if not utils.check_interface(interface):
            parser.error(f"The interface '{interface}' is not active or connected to any network !")
        ip_gateway = utils.iface_gateway(interface)
        print(ip_gateway)

    # '--start-proxy'
    elif args.start_proxy:
        # controls
        if os.getuid() != 0:
            parser.error("Run with root access !")
        if not utils.check_interface(interface):
            parser.error(f"The interface '{interface}' is not active or connected to any network !")
        # start proxy service
        print("To stop: CTRL+C")
        try:
            utils.start_proxy(interface, proxy_port)
        except KeyboardInterrupt:
            print("Stopped proxy service")

    # '--scan-interface'
    elif args.scan_interface:
        # controls
        if os.getuid() != 0:
            parser.error("Run with root access !")
        if not utils.check_interface(interface):
            parser.error(f"The interface '{interface}' is not active or connected to any network !")
        # scan interface
        ip_address = utils.iface_ipaddr(interface)
        scan_iface = utils.scan_interface(ip_address, "255.255.255.0", interface)
        print(scan_iface)

    elif args.connect_wifi:
        # controls
        if not args.ssid:
            parser.error("Enter the SSID !")
        if not args.password:
            parser.error("Enter the password !")
        output = utils.connect_wifi(args.ssid, args.password, interface)
        print(output.strip())

    else:
        parser.print_help()


if __name__ == '__main__':
    # reading configuration file
    config_file = "/usr/share/2interface/config.json"
    with open(config_file, "r") as jsondata:
        data = json.load(jsondata)
        interface = data["interface"]
        proxy_port = data["proxy_port"]
    if len(interface) == 0:
        print("Fill in the configuration file!")
        time.sleep(1)
        os.system("nano /usr/share/2interface/config.json")
        sys.exit(1)
    main(interface, proxy_port)  # main function

