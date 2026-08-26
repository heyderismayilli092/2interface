import argparse
import utils
import json
import os
import sys

# '2interface' software arguments
def main(interface):
    parser = argparse.ArgumentParser(description="2interface -- A Python-based Linux network manager for Wi-Fi discovery, connection management, policy-based routing, and per-application traffic routing")

    parser.add_argument('--scanwifi', action='store_true', help='Lists the wireless networks detected by the network interface')
    parser.add_argument('--interface-address', action='store_true', help='Displays the interface\'s local IP address')
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
    else:
        parser.print_help()


if __name__ == '__main__':
    # reading configuration file
    with open("config.json", "r") as jsondata:
        data = json.load(jsondata)
        interface = data["interface"]
    if len(interface) == 0:
        print("Fill in the configuration file!")
        sys.exit(1)
    main(interface)  # main function

