#!/usr/bin/env python3

import os
import sys
import requests
import subprocess
import time
from stem import Signal
from stem.control import Controller


BACKUP_DIR = "/usr/lib/tor-redirect"

TORRC = "/etc/tor/tor-redirect-rc"
TORRC_CFG = \
    """
VirtualAddrNetwork 10.0.0.0/10
AutomapHostsOnResolve 1
TransPort 9040
DNSPort 5353
ControlPort 9051
RunAsDaemon 1
"""

TOR_USER = "debian-tor"

RESOLV_CONF_PATH = "/etc/resolv.conf"
RESOLV_CONF = "nameserver 127.0.0.1"


#TOR_UID = subprocess.getoutput(f"id -ur {TOR_USER}")
IPTABLES_RULES = \
f"""
NON_TOR="192.168.1.0/24 192.168.0.0/24"
TOR_UID={subprocess.getoutput(f'id -ur {TOR_USER}')}
TRANS_PORT="9040"

iptables -F
iptables -t nat -F

iptables -t nat -A OUTPUT -m owner --uid-owner $TOR_UID -j RETURN
iptables -t nat -A OUTPUT -p udp --dport 53 -j REDIRECT --to-ports 5353
for NET in $NON_TOR 127.0.0.0/9 127.128.0.0/10; do
 iptables -t nat -A OUTPUT -d $NET -j RETURN
done
iptables -t nat -A OUTPUT -p tcp --syn -j REDIRECT --to-ports $TRANS_PORT

iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
for NET in $NON_TOR 127.0.0.0/8; do
 iptables -A OUTPUT -d $NET -j ACCEPT
done
iptables -A OUTPUT -m owner --uid-owner $TOR_UID -j ACCEPT
iptables -A OUTPUT -j REJECT
"""

IPTABLES_FLUSH = \
    """
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT
iptables -t nat -F
iptables -t mangle -F
iptables -F
iptables -X
"""



# https://en.wikipedia.org/wiki/ANSI_escape_code
class Color:
    # RESET
    RESET = "\033[0m"

    # FG
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    RED = "\033[31m"
    YELLOW = "\033[93m"
    FAIL = "\033[91m"
    WHITE = "\033[37m"

    # FORMATTING
    BOLD = "\033[1m"
    BLINK = "\033[5m"


def help():
    print(
    f"""
    {sys.argv[0]} [arg]

    arguments:

    status              Check if tor-redirect is running already
    start               Start redirecting traffic
    stop                Stop redirecting traffic
    switch              Switch exit node
    --help, -h          Print this message

    """)

    sys.exit()


def get_time():
    time_stamp = time.strftime("%H:%M:%S", time.localtime())
    return f"[{time_stamp}]"


def get_ip():
    try:
        res = requests.get("https://api.ipify.org/?format=json")
        ip = res.json()["ip"]
    except Exception as e:
        return "failed fetching ip: "# + str(e)
    return ip


def is_root():
    if os.geteuid() != 0:
        print("root privileges required!")
        sys.exit(0)


def config():
    if not os.path.isdir(BACKUP_DIR):
        os.mkdir(BACKUP_DIR)

    if not os.path.isfile(f"{BACKUP_DIR}/resolv.conf.bak"):
        os.system(f"sudo cp /etc/resolv.conf {BACKUP_DIR}/resolv.conf.bak")


def log(string, time=True):
    line = f"{Color.BOLD}{get_time() if time else ''}{Color.RESET}" + " " + string

    print(line)



def status():
    if os.path.isfile(f"{BACKUP_DIR}/running"):
        log(Color.GREEN + "tor-redirect is running" + Color.RESET, time=False)

    else:
        log(Color.RED + "tor-redirect is not running" + Color.RESET, time=False)

    log("Fetching current IP...")
    log("CURRENT IP: " + Color.GREEN + get_ip() + Color.RESET)


def start():
    if os.path.isfile(f"{BACKUP_DIR}/running"):
        log(Color.YELLOW + "tor-redirect seems to be running already, continuing anyway..." + Color.RESET)

    os.system(f"sudo cp /etc/resolv.conf {BACKUP_DIR}/resolv.conf")

    if os.path.isfile(TORRC) and TORRC_CFG in open(TORRC).read():
        log("torrc is already configured")

    else:
        log("Writing torcc")

        open(TORRC, "w").write(TORRC_CFG)

        log(Color.GREEN + "[done]" + Color.RESET, time=False)

            
    if RESOLV_CONF in open(RESOLV_CONF_PATH).read():
        log("DNS resolv.conf is already configured")

    else:
        open(RESOLV_CONF_PATH, "w").write(RESOLV_CONF)

        log("Configuring DNS resolv.conf...")
        log(Color.GREEN + "[done]" + Color.RESET, time=False)


    log("Stopping tor service...")
    os.system("sudo systemctl stop tor")
    os.system("sudo fuser -k 9051/tcp > /dev/null 2> /dev/null")
    log(Color.GREEN + "[done]" + Color.RESET, time=False)
    
    log("Starting new tor daemon... ")
    os.system(f"sudo -u {TOR_USER} tor -f /etc/tor/tor-redirect-rc > /dev/null")
    log(Color.GREEN + "[done]" + Color.RESET, time=False)

    log("Setting up iptables rules...")
    os.system(IPTABLES_RULES)
    log(Color.GREEN + "[done]" + Color.RESET, time=False)

    if not os.path.isfile(f"{BACKUP_DIR}/running"): os.system(f"sudo touch {BACKUP_DIR}/running")

    log("Fetching current IP...")
    log("CURRENT IP: " + Color.GREEN + get_ip() + Color.RESET)


def stop():
    if not os.path.isfile(f"{BACKUP_DIR}/running"):
        log(Color.YELLOW + "tor-redirect seems to not be running, continuing anyway..." + Color.RESET)

    log(Color.RED + "STOPPING tor-redirect" + Color.RESET)
    log("Flushing iptables, resetting to default")

    os.system(f"cp {BACKUP_DIR}/resolv.conf /etc/resolv.conf")
    os.system(IPTABLES_FLUSH)

    os.system("sudo systemctl stop tor")
    os.system("sudo fuser -k 9051/tcp > /dev/null 2> /dev/null")

    log(Color.GREEN + "[done]" + Color.RESET, time=False)

    log("Restarting network manager")
    os.system("sudo systemctl network-manager restart")
    log(Color.GREEN + "[done]" + Color.RESET, time=False)

    if os.path.isfile(f"{BACKUP_DIR}/running"): os.system(f"sudo rm -rf {BACKUP_DIR}/running")

    log("Fetching current IP...")
    time.sleep(4)
    log("CURRENT IP: " + Color.GREEN + get_ip() + Color.RESET)


def switch():
    if not os.path.isfile(f"{BACKUP_DIR}/running"):
        log(Color.YELLOW + "tor-redirect seems to not be running, please start first" + Color.RESET)

    log("Please wait...")
    time.sleep(8)
    log("Requesting new node...")

    if os.path.isfile(f"{BACKUP_DIR}/running"): os.system(f"sudo rm -rf {BACKUP_DIR}/running")

    with Controller.from_port(port=9051) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)
    
    if not os.path.isfile(f"{BACKUP_DIR}/running"): os.system(f"sudo touch {BACKUP_DIR}/running")

    log(Color.GREEN + "[done]" + Color.RESET, time=False)

    log("Fetching current IP...")
    log("CURRENT IP: " + Color.GREEN + get_ip() + Color.RESET)



def main():
    is_root()

    if len(sys.argv) <= 1:
        help()
        sys.exit()

    config()

    opts = sys.argv[1:]

    for opt in opts:
        if opt == "status":
            status()
        elif opt == "start":
            start()
        elif opt == "stop":
            stop()
        elif opt == "switch":
            switch()
        elif opt == "--help" or  opt == "-h":
            help()
        else:
            help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("user interrupt...")
        print("stopping...")
        os.system(f"cp {BACKUP_DIR}/resolv.conf /etc/resolv.conf.bak")
        stop()
    except Exception as e:
        print("error starting tor-redirect: " + str(e))

