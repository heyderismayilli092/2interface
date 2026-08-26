import argparse
import utils
import json

# '2interface' software arguments
def main(interface):
    parser = argparse.ArgumentParser(description="2interface -- A Python-based Linux network manager for Wi-Fi discovery, connection management, policy-based routing, and per-application traffic routing")

    parser.add_argument('--scanwifi', action='store_true', help='Lists the wireless networks detected by the network interface')
    args = parser.parse_args()

    # '--scanwifi'
    if args.scanwifi:
        print("Scanning wireless networks...")
        output = utils.scan_wireless_iw(interface)
        for network in output:
            print(f"- {network}")
    else:
        parser.print_help()


if __name__ == '__main__':
    # reading configuration file
    with open("config.json", "r") as jsondata:
        data = json.load(jsondata)
        interface = data["interface"]

    main(interface)  # main function

