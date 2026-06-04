#!/usr/bin/env python3
"""Enable RabbitMQ 4 compatibility for Celery on homelab server."""

import argparse

import paramiko


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="192.168.10.13")
    parser.add_argument("--user", default="paulo")
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(args.host, username=args.user, password=args.password, timeout=15)

    cmds = [
        # Allow Celery pidbox/mingle transient queues on RabbitMQ 4
        """docker exec stack_rabbitmq sh -c 'cat > /etc/rabbitmq/conf.d/99-celery-compat.conf <<EOF
deprecated_features.permit.transient_nonexcl_queues = true
EOF'""",
        "docker exec stack_rabbitmq cat /etc/rabbitmq/conf.d/99-celery-compat.conf",
        "docker restart stack_rabbitmq",
        "sleep 8",
        "docker exec stack_rabbitmq rabbitmq-diagnostics ping",
    ]

    for cmd in cmds:
        print(f"\n$ {cmd[:100]}...")
        _, o, e = client.exec_command(cmd, timeout=120)
        out = (o.read() + e.read()).decode()
        if out.strip():
            print(out.strip())

    client.close()
    print("\nRabbitMQ restarted with Celery compatibility flag.")


if __name__ == "__main__":
    main()
