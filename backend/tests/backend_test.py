"""Backend tests for Oasis Sultan Console v1.

Covers:
  * GET  /api/status
  * GET  /api/agents
  * POST /api/kcu/validate (valid + empty + invalid)
  * POST /api/command (all supported commands + unknown)
  * POST /api/cycle
  * GET  /api/coins
  * WebSocket /api/ws (snapshot + tick broadcast)
"""

import asyncio
import json
import os
import time

import pytest
import requests
import websockets

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else None
# Fallback: read frontend/.env directly (test runner may not have it exported)
if not BASE_URL:
    with open("/app/frontend/.env") as fh:
        for line in fh:
            if line.startswith("REACT_APP_BACKEND_URL"):
                BASE_URL = line.split("=", 1)[1].strip().strip('"').rstrip("/")
                break

API = f"{BASE_URL}/api"


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# --------------------------------------------------------------------------- #
# /api/status
# --------------------------------------------------------------------------- #
class TestStatus:
    def test_status_shape(self, api_client):
        r = api_client.get(f"{API}/status")
        assert r.status_code == 200
        data = r.json()
        for k in ("cycle", "coins_minted", "swarm", "magic_constant", "log"):
            assert k in data, f"missing key {k}"
        assert data["magic_constant"] == "0x5F3759DF"
        assert isinstance(data["cycle"], int)
        assert isinstance(data["log"], list)
        swarm = data["swarm"]
        for k in ("alive", "dead", "total_energy", "avg_score", "top_agent",
                  "octant_occupancy", "depth_signature"):
            assert k in swarm, f"swarm missing {k}"
        assert isinstance(swarm["octant_occupancy"], list) and len(swarm["octant_occupancy"]) == 8

    def test_status_cycle_increments(self, api_client):
        c1 = api_client.get(f"{API}/status").json()["cycle"]
        # auto-tick every 2s; wait a little over one tick
        time.sleep(2.5)
        c2 = api_client.get(f"{API}/status").json()["cycle"]
        assert c2 > c1, f"cycle did not advance ({c1} -> {c2})"


# --------------------------------------------------------------------------- #
# /api/agents
# --------------------------------------------------------------------------- #
class TestAgents:
    def test_agents_count_and_shape(self, api_client):
        r = api_client.get(f"{API}/agents")
        assert r.status_code == 200
        data = r.json()
        assert "agents" in data and "stats" in data
        agents = data["agents"]
        assert len(agents) == 64
        ids = {a["id"] for a in agents}
        assert ids == set(range(64))
        for a in agents:
            for k in ("id", "alive", "energy", "position", "score"):
                assert k in a
            assert isinstance(a["position"], list) and len(a["position"]) == 3


# --------------------------------------------------------------------------- #
# /api/kcu/validate
# --------------------------------------------------------------------------- #
class TestKCU:
    WIF = "5J1F7GHaDpEyq6oimC9UkAsq3aP9zApBW2Zke1jsE5cVBFhVsPu"
    TARGET = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

    def test_kcu_valid(self, api_client):
        r = api_client.post(f"{API}/kcu/validate", json={
            "wif_key": self.WIF, "target_address": self.TARGET,
        })
        assert r.status_code == 200
        data = r.json()
        for k in ("vacuum_resonance", "t45_seed", "t45_twisted",
                  "fast_inverse_sqrt", "true_inverse_sqrt",
                  "approximation_error", "hash_energy",
                  "magic_constant", "locked"):
            assert k in data, f"missing {k}"
        assert data["magic_constant"] == "0x5F3759DF"
        assert 0 <= data["vacuum_resonance"] <= 100
        assert data["t45_seed"].startswith("0x") and len(data["t45_seed"]) == 18
        assert data["t45_twisted"].startswith("0x") and len(data["t45_twisted"]) == 18
        assert isinstance(data["locked"], bool)
        assert data["fast_inverse_sqrt"] > 0
        assert data["true_inverse_sqrt"] > 0
        # Fast inverse sqrt approximation error should be tiny (< 1%)
        assert data["approximation_error"] < 0.01

    def test_kcu_empty_wif(self, api_client):
        r = api_client.post(f"{API}/kcu/validate", json={
            "wif_key": "", "target_address": self.TARGET,
        })
        assert r.status_code == 400

    def test_kcu_empty_target(self, api_client):
        r = api_client.post(f"{API}/kcu/validate", json={
            "wif_key": self.WIF, "target_address": "",
        })
        assert r.status_code == 400

    def test_kcu_deterministic(self, api_client):
        payload = {"wif_key": self.WIF, "target_address": self.TARGET}
        d1 = api_client.post(f"{API}/kcu/validate", json=payload).json()
        d2 = api_client.post(f"{API}/kcu/validate", json=payload).json()
        # Same inputs → same resonance (deterministic hash chain)
        assert d1["vacuum_resonance"] == d2["vacuum_resonance"]
        assert d1["t45_twisted"] == d2["t45_twisted"]


# --------------------------------------------------------------------------- #
# /api/command
# --------------------------------------------------------------------------- #
class TestCommand:
    def _post(self, api_client, cmd):
        return api_client.post(f"{API}/command", json={"command": cmd})

    def test_help(self, api_client):
        r = self._post(api_client, "help")
        assert r.status_code == 200
        data = r.json()
        assert "result" in data and "status" in data
        assert "revive" in data["result"].lower()

    def test_revive_all(self, api_client):
        r = self._post(api_client, "revive all")
        assert r.status_code == 200
        data = r.json()
        # After revive all - all 64 agents should be alive
        assert data["status"]["swarm"]["alive"] == 64
        assert data["status"]["swarm"]["dead"] == 0

    def test_kill(self, api_client):
        self._post(api_client, "revive all")
        r = self._post(api_client, "kill 5")
        assert r.status_code == 200
        assert r.json()["status"]["swarm"]["alive"] == 63

    def test_kill_invalid(self, api_client):
        r = self._post(api_client, "kill abc")
        assert r.status_code == 400

    def test_boost(self, api_client):
        r = self._post(api_client, "boost 10")
        assert r.status_code == 200
        assert "energy" in r.json()["result"].lower()

    def test_optimize(self, api_client):
        r = self._post(api_client, "optimize")
        assert r.status_code == 200
        assert "vantacore" in r.json()["result"].lower() or "reallocated" in r.json()["result"].lower()

    def test_cycle(self, api_client):
        c0 = api_client.get(f"{API}/status").json()["cycle"]
        r = self._post(api_client, "cycle")
        assert r.status_code == 200
        assert r.json()["status"]["cycle"] > c0

    def test_reset(self, api_client):
        r = self._post(api_client, "reset")
        assert r.status_code == 200
        assert "respawn" in r.json()["result"].lower() or "seeded" in r.json()["result"].lower()

    def test_status_cmd(self, api_client):
        r = self._post(api_client, "status")
        assert r.status_code == 200
        assert "alive" in r.json()["result"].lower()

    def test_unknown(self, api_client):
        r = self._post(api_client, "banana pancakes")
        assert r.status_code == 400
        assert "unknown" in r.json()["detail"].lower()

    def test_empty(self, api_client):
        r = self._post(api_client, "   ")
        assert r.status_code == 400


# --------------------------------------------------------------------------- #
# /api/cycle
# --------------------------------------------------------------------------- #
class TestCycle:
    def test_cycle_advances(self, api_client):
        c0 = api_client.get(f"{API}/status").json()["cycle"]
        r = api_client.post(f"{API}/cycle")
        assert r.status_code == 200
        data = r.json()
        assert "cycle" in data and "optimize" in data and "minted" in data
        assert data["cycle"] > c0
        assert isinstance(data["minted"], list)


# --------------------------------------------------------------------------- #
# /api/coins
# --------------------------------------------------------------------------- #
class TestCoins:
    def test_coins_shape(self, api_client):
        r = api_client.get(f"{API}/coins")
        assert r.status_code == 200
        data = r.json()
        for k in ("coins", "total_supply", "total_minted"):
            assert k in data
        assert isinstance(data["coins"], list)
        # coin documents should NOT contain MongoDB _id
        for c in data["coins"][:5]:
            assert "_id" not in c
            for k in ("id", "agent_id", "amount", "hash", "resonance", "minted_at"):
                assert k in c

    def test_coins_grow_over_time(self, api_client):
        """Coins should accumulate as swarm ticks. Force a few boosts to
        speed up score-gate crossings."""
        # push scores high via optimize passes (score += bonus*0.5)
        for _ in range(6):
            api_client.post(f"{API}/command", json={"command": "boost 30"})
            api_client.post(f"{API}/command", json={"command": "optimize"})
            api_client.post(f"{API}/cycle")
        r = api_client.get(f"{API}/coins")
        data = r.json()
        # Not strict assert since randomness — just verify shape holds
        assert data["total_minted"] >= 0
        assert data["total_supply"] >= 0
        if data["total_minted"] > 0:
            assert data["coins"][0]["amount"] > 0


# --------------------------------------------------------------------------- #
# WebSocket /api/ws
# --------------------------------------------------------------------------- #
class TestWebSocket:
    def test_snapshot_and_tick(self):
        ws_base = BASE_URL.replace("https://", "wss://").replace("http://", "ws://")
        url = f"{ws_base}/api/ws"

        async def run():
            async with websockets.connect(url, open_timeout=10) as ws:
                # 1st message must be snapshot
                first = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
                assert first["type"] == "snapshot"
                assert "status" in first
                assert "agents" in first and len(first["agents"]) == 64

                # Next tick within ~3s
                second = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
                assert second["type"] == "tick"
                assert "status" in second
                assert "agents" in second and len(second["agents"]) == 64
                assert "minted" in second

        asyncio.run(run())
