"""Verify the seeded Pi configuration can load in RPC mode without provider credentials."""
import json
import subprocess
import sys

image = sys.argv[1]
result = subprocess.run(
    ["docker", "run", "--rm", "-i", "--tmpfs", "/home/paseo:uid=1000,gid=1000",
     image, "pi", "--mode", "rpc"],
    input=json.dumps({"id": "smoke", "type": "get_state"}) + "\n",
    text=True, capture_output=True, timeout=60,
)
responses = []
for line in result.stdout.splitlines():
    try:
        responses.append(json.loads(line))
    except json.JSONDecodeError:
        continue
if result.returncode or not any(r.get("id") == "smoke" and r.get("success") for r in responses):
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    raise SystemExit("Pi RPC configuration smoke test failed")
print("Pi RPC loaded seeded settings and answered get_state.")
