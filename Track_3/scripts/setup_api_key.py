"""
Create a SigNoz API key for MCP access.
Tries multiple strategies to create and verify the key.

Usage: python scripts/setup_api_key.py
"""
import subprocess, json, uuid, time, os, sys

API_KEY = "mera-self-healing-key-2026"
SERVICE_ACCOUNT_ID = str(uuid.uuid4())
API_KEY_ID = str(uuid.uuid4())

POSSIBLE_DB_CONTAINERS = [
    "mera-metastore-postgres-0",
    "signoz-metastore-postgres-0",
    "signoz-postgres-0",
    "signoz-clickhouse-0",
]

POSSIBLE_MCP_PORTS = [8000, 8080]


def find_container(pattern: str) -> str | None:
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=10
        )
        for name in result.stdout.strip().split("\n"):
            if pattern in name:
                return name.strip()
    except Exception:
        pass
    return None


def psql(container: str, query: str) -> str:
    cmd = [
        "docker", "exec", container, "sh", "-c",
        f"PGPASSWORD=signoz psql -h localhost -U signoz -d signoz -t -A -F ',' -c \"{query}\""
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    return result.stdout.strip()


def exec_sql(container: str, sql: str) -> str:
    cmd = [
        "docker", "exec", container, "sh", "-c",
        f"PGPASSWORD=signoz psql -h localhost -U signoz -d signoz -c \"{sql}\""
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    return result.stdout


def test_mcp_with_key(key: str) -> bool:
    import requests
    for port in POSSIBLE_MCP_PORTS:
        for url in [f"http://localhost:{port}/mcp"]:
            for header_name in ["SIGNOZ-API-KEY", "Authorization", "X-SigNoz-API-Key"]:
                try:
                    resp = requests.post(url, json={
                        "jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1
                    }, headers={
                        "Content-Type": "application/json",
                        header_name: key
                    }, timeout=5)
                    if resp.status_code == 200:
                        tools = resp.json().get("result", {}).get("tools", [])
                        print(f"  Verified! MCP responded with {len(tools)} tools")
                        return True
                except Exception:
                    continue
    return False


def main():
    print("=" * 55)
    print("  SigNoz API Key Setup")
    print("=" * 55)

    if len(sys.argv) > 1:
        custom_key = sys.argv[1]
        print(f"\n  Using custom key from argument: {custom_key}")
        print(f"  Testing against MCP...")
        if test_mcp_with_key(custom_key):
            print(f"\n  Key {custom_key} WORKS with MCP.")
            print(f"  Add to .env: SIGNOZ_API_KEY={custom_key}")
            return
        else:
            print(f"  Could not verify. The key may still work — try running:")
            print(f"  python scripts/test_mcp_connection.py")
            print(f"  Add to .env: SIGNOZ_API_KEY={custom_key}")
            return

    print("\n[1/5] Finding database container...")
    db_container = None
    for pattern in POSSIBLE_DB_CONTAINERS:
        found = find_container(pattern)
        if found:
            db_container = found
            print(f"  Found: {found}")
            break
    if not db_container:
        print("  No SigNoz database container found. Is SigNoz running?")
        print("  Start it with: foundryctl cast -f casting.yaml")
        print("\n  Alternatively, create a PAT manually:")
        print("  1. Open http://localhost:8080")
        print("  2. Settings → API Keys")
        print("  3. Create a Personal Access Token")
        print(f"  4. Add to .env: SIGNOZ_API_KEY=<your-token>")
        sys.exit(1)

    print(f"\n[2/5] Checking users in {db_container}...")
    users = psql(db_container, "SELECT id, display_name, email FROM users LIMIT 5")
    org = psql(db_container, "SELECT org_id FROM users LIMIT 1")
    print(f"  Users: {users[:200]}")
    if not org or not org.strip():
        print("  No org found. SigNoz may not be fully initialized.")
        print("  Open http://localhost:8080 and complete setup first.")
        sys.exit(1)
    ORG_ID = org.strip()
    print(f"  Org ID: {ORG_ID}")

    print(f"\n[3/5] Creating service account...")
    sa_sql = f"""
    INSERT INTO service_account (id, name, email, status, created_at, updated_at, org_id)
    VALUES ('{SERVICE_ACCOUNT_ID}', 'mera-agent', 'mera-agent@mera.io', 'ACTIVE', NOW(), NOW(), '{ORG_ID}')
    ON CONFLICT (id) DO NOTHING;
    """
    result = exec_sql(db_container, sa_sql)
    print(f"  {result.strip() or 'OK (or already exists)'}")

    print(f"\n[4/5] Creating API key...")
    key_sql = f"""
    INSERT INTO apiserver_factor_api_key (id, name, key, created_at, updated_at, expires_at, last_observed_at, service_account_id)
    VALUES ('{API_KEY_ID}', 'mera-agent-key', '{API_KEY}', NOW(), NOW(), 0, NOW(), '{SERVICE_ACCOUNT_ID}')
    ON CONFLICT (id) DO NOTHING;
    """
    result = exec_sql(db_container, key_sql)
    print(f"  {result.strip() or 'OK (or already exists)'}")

    print(f"\n[5/5] Verifying and testing MCP...")
    verify = psql(db_container, "SELECT id, name, key FROM apiserver_factor_api_key")
    print(f"  Keys in DB: {verify[:200]}")

    print(f"\n  Testing key against MCP server...")
    if test_mcp_with_key(API_KEY):
        print(f"\n  API key WORKS with MCP!")
    else:
        print(f"  MCP not reachable, but key was created in DB.")
        print(f"  Test manually later: python scripts/test_mcp_connection.py")

    print(f"\n{'='*55}")
    print(f"  Add this to your Track_3/.env file:")
    print(f"  SIGNOZ_API_KEY={API_KEY}")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
