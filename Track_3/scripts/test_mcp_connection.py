"""
Test MCP server connectivity and authentication.
Usage: python scripts/test_mcp_connection.py
"""
import sys, os, json, requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

MCP_URLS = [
    os.getenv("SIGNOZ_MCP_URL", ""),
    "http://localhost:8000/mcp",
    "http://localhost:8080/mcp",
    "http://signoz-mcp:8000/mcp",
]
API_KEY = os.getenv("SIGNOZ_API_KEY", "")
AUTH_HEADERS = ["SIGNOZ-API-KEY", "Authorization", "X-SigNoz-API-Key"]

print("=" * 55)
print("  MCP Connection Test")
print("=" * 55)
print(f"  API Key: {'SET' if API_KEY else 'NOT SET'}")
print()

for url in MCP_URLS:
    if not url:
        continue
    for auth_header in AUTH_HEADERS:
        headers = {"Content-Type": "application/json"}
        if API_KEY:
            headers[auth_header] = API_KEY
        try:
            payload = {"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}
            resp = requests.post(url, json=payload, headers=headers, timeout=5)
            status = resp.status_code
            if status == 200:
                data = resp.json()
                tools = data.get("result", {}).get("tools", [])
                print(f"  {url}")
                print(f"    Auth: {auth_header}")
                print(f"    Status: {status} OK")
                print(f"    Tools: {len(tools)}")
                for t in tools[:5]:
                    print(f"      - {t.get('name', '?')}")
                if len(tools) > 5:
                    print(f"      ... and {len(tools)-5} more")
                print()
                print("  MCP is WORKING.")
                sys.exit(0)
            else:
                print(f"  {url}")
                print(f"    Auth: {auth_header}")
                print(f"    Status: {status}")
                try:
                    detail = resp.json()
                    print(f"    Response: {json.dumps(detail, indent=4)[:200]}")
                except Exception:
                    print(f"    Response: {resp.text[:200]}")
                print()
        except requests.ConnectionError:
            pass
        except Exception as e:
            print(f"  {url}")
            print(f"    Auth: {auth_header}")
            print(f"    Error: {e}")
            print()

print("  Could not reach MCP server on any URL.")
print()
print("  To start SigNoz + MCP:")
print("    foundryctl cast -f casting.yaml")
print("  OR")
print("    docker compose up -d")
print()
print("  Then generate an API key:")
print("    python scripts/setup_api_key.py")
print("  OR via UI: http://localhost:8080 → Settings → API Keys")
sys.exit(1)
