import argparse
import getpass
import os
import sys

import paramiko


HOST = "192.168.37.128"
USER = "IC"
PASSWORD_ENV = "LVBOBALUN_VM_PASSWORD"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--user", default=USER)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = " ".join(args.command).strip()
    if not command:
        print("usage: python ssh_vm.py <command>")
        return 1

    password = os.environ.get(PASSWORD_ENV)
    if not password:
        password = getpass.getpass(f"Password for {args.user}@{args.host}: ")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=args.host, username=args.user, password=password, timeout=10)
    try:
        _, stdout, stderr = client.exec_command(command)
        out = stdout.read().decode("utf-8", "ignore")
        err = stderr.read().decode("utf-8", "ignore")
    finally:
        client.close()

    if out:
        print(out, end="" if out.endswith("\n") else "\n")
    if err:
        print(err, end="" if err.endswith("\n") else "\n", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
