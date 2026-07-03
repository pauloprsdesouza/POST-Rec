#!/usr/bin/env python3
"""Seed Qualis journal data on Hostinger production."""
import os
import re
import paramiko
from pathlib import Path

HOST = os.environ.get("HOSTINGER_HOST", "187.127.39.214")
PASSWORD = os.environ.get("HOSTINGER_SSH_PASSWORD", "")
REMOTE = "/opt/post-rec"
ROOT = Path(__file__).resolve().parents[1]

QUALIS_ENV = """QUALIS_ENABLED=true
QUALIS_CSV_PATH=qualis_avaliacoes-2021-2024.csv
QUALIS_BOOST_WEIGHT=0.10
QUALIS_USE_REDIS_CACHE=true
QUALIS_CACHE_TTL=2592000
"""


def upsert_env_lines(text: str, block: str) -> str:
    for line in block.strip().splitlines():
        key = line.split("=", 1)[0]
        pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
        if pattern.search(text):
            text = pattern.sub(line, text)
        else:
            if text and not text.endswith("\n"):
                text += "\n"
            text += line + "\n"
    return text


def run(client, cmd, timeout=900):
    _, o, e = client.exec_command(cmd, timeout=timeout)
    out = (o.read() + e.read()).decode("utf-8", errors="replace")
    return o.channel.recv_exit_status(), out


def main() -> int:
    if not PASSWORD:
        print("Set HOSTINGER_SSH_PASSWORD", file=__import__("sys").stderr)
        return 1

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username="root", password=PASSWORD, timeout=30, look_for_keys=False, allow_agent=False)

    sftp = client.open_sftp()
    with sftp.open(f"{REMOTE}/.env", "r") as f:
        env = f.read().decode("utf-8", errors="replace")
    with sftp.open(f"{REMOTE}/.env", "w") as f:
        f.write(upsert_env_lines(env, QUALIS_ENV))

    sftp.put(str(ROOT / "scripts" / "seed_qualis.py"), f"{REMOTE}/scripts/seed_qualis.py")

    for name in ("qualis_avaliacoes-2021-2024.csv", "qualis_avaliacoes-2017-2020.csv"):
        local = ROOT / name
        if local.is_file():
            print(f"Uploading {name}...")
            sftp.put(str(local), f"{REMOTE}/{name}")
    sftp.close()

    print("Copying Qualis CSVs and seed script into api container...")
    run(client, f"docker cp {REMOTE}/scripts/seed_qualis.py post-rec-api-1:/app/scripts/seed_qualis.py")
    run(client, f"docker cp {REMOTE}/qualis_avaliacoes-2021-2024.csv post-rec-api-1:/app/qualis_avaliacoes-2021-2024.csv")
    run(client, f"docker cp {REMOTE}/qualis_avaliacoes-2017-2020.csv post-rec-api-1:/app/qualis_avaliacoes-2017-2020.csv")

    seed_cmd = (
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.prod.yml "
        "exec -T api python scripts/seed_qualis.py --all-periods --warm-cache"
    )
    print("Seeding qualis_journal (may take a few minutes)...")
    code, out = run(client, seed_cmd, timeout=900)
    print(out[-5000:])
    if code != 0:
        client.close()
        return code

    verify_cmd = (
        "docker exec post-rec-api-1 python -c \""
        "from apps.api.features.qualis.service import qualis_service; "
        "print('loaded', qualis_service.loaded); "
        "print('rows', qualis_service.row_count); "
        "print('lookup', qualis_service.lookup_estrato(issn='0001-4273'))\""
    )
    _, verify = run(client, verify_cmd, timeout=60)
    print("Verify:", verify.strip())

    run(client, "cd /opt/post-rec && docker compose -f docker-compose.yml -f docker-compose.prod.yml restart worker api")
    client.close()
    print("\nQualis seeded. Create a NEW recommendation run to see badges on ranked papers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
