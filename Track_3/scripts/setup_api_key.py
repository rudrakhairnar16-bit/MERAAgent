"""Create a SigNoz API key directly in the database for MCP access."""
import subprocess, json, uuid, time, os

DB_CONTAINER = "mera-metastore-postgres-0"
API_KEY = "mera-self-healing-key-2026"
SERVICE_ACCOUNT_ID = str(uuid.uuid4())
API_KEY_ID = str(uuid.uuid4())
ORG_ID = None

def psql(query):
    cmd = [
        "docker", "exec", DB_CONTAINER, "sh", "-c",
        f"PGPASSWORD=signoz psql -h localhost -U signoz -d signoz -t -A -F ',' -c \"{query}\""
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    return result.stdout.strip()

def exec_sql(sql):
    cmd = [
        "docker", "exec", DB_CONTAINER, "sh", "-c",
        f"PGPASSWORD=signoz psql -h localhost -U signoz -d signoz -c \"{sql}\""
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    return result.stdout

# Get org ID from existing user
print("[1/4] Checking existing users...")
users = psql("SELECT id, display_name, email FROM users")
org = psql("SELECT org_id FROM users LIMIT 1")
print(f"  Users: {users}")
print(f"  Org: {org}")
if org and org.strip():
    ORG_ID = org.strip()
    print(f"  Found org_id: {ORG_ID}")
else:
    print("  ERROR: Could not find org_id")
    exit(1)

# Create a service account
print(f"\n[2/4] Creating service account...")
sa_sql = f"""
INSERT INTO service_account (id, name, email, status, created_at, updated_at, org_id)
VALUES ('{SERVICE_ACCOUNT_ID}', 'mera-agent', 'mera-agent@mera.io', 'ACTIVE', NOW(), NOW(), '{ORG_ID}');
"""
print(f"  Service account ID: {SERVICE_ACCOUNT_ID}")
result = exec_sql(sa_sql)
print(f"  {result.strip()}")

# Create API key for the service account
print(f"\n[3/4] Creating API key...")
key_sql = f"""
INSERT INTO factor_api_key (id, name, key, created_at, updated_at, expires_at, last_observed_at, service_account_id)
VALUES ('{API_KEY_ID}', 'mera-agent-key', '{API_KEY}', NOW(), NOW(), 0, NOW(), '{SERVICE_ACCOUNT_ID}');
"""
result = exec_sql(key_sql)
print(f"  {result.strip()}")

# Verify
print(f"\n[4/4] Verifying...")
verify = psql("SELECT id, name, key FROM factor_api_key")
print(f"  API Keys: {verify}")

print(f"\n✅ API key created: {API_KEY}")
print(f"Add this to your Track_3/.env file:")
print(f"  SIGNOZ_API_KEY={API_KEY}")
