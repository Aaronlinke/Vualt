"""
SultanOSVanta core logic.

Implements the mathematical / programmatic substrate for the Oasis Sultan
Console:
    - HOctreeSubstrat      : hierarchical octree spatial index for 64 agents
    - KCUV4Core            : Vacuum Resonance validator (T45 twist + 0x5F3759DF)
    - SwarmManager         : lifecycle + physics for the 64 agent slots
    - SultanCoinEngine     : mints Sultan-Coins from swarm events
    - VantaCoreOptimizer   : energy reallocation / score optimization pass

All state here is in-memory & pure python; persistence is layered on top in
server.py (MongoDB for the Sultan-Coin ledger).
"""

import hashlib
import math
import random
import struct
import time
import uuid
from datetime import datetime, timezone

# The Quake III fast inverse square root magic constant.
MAGIC_CONSTANT = 0x5F3759DF
AGENT_COUNT = 64
GRID_SIDE = 8  # 8x8 = 64 slots


# --------------------------------------------------------------------------- #
# Low level math primitives
# --------------------------------------------------------------------------- #
def fast_inverse_sqrt(number: float) -> float:
    """Quake III fast inverse square root using the 0x5F3759DF bit hack."""
    if number <= 0:
        return 0.0
    threehalfs = 1.5
    x2 = number * 0.5
    packed = struct.pack("f", number)
    i = struct.unpack("i", packed)[0]
    i = MAGIC_CONSTANT - (i >> 1)
    y = struct.unpack("f", struct.pack("i", i))[0]
    # One Newton-Raphson iteration
    y = y * (threehalfs - (x2 * y * y))
    return y


def t45_twist(n: int) -> int:
    """T45 logic: a 45-bit left rotation over a 64-bit word."""
    n &= 0xFFFFFFFFFFFFFFFF
    return ((n << 45) | (n >> (64 - 45))) & 0xFFFFFFFFFFFFFFFF


# --------------------------------------------------------------------------- #
# HOctreeSubstrat
# --------------------------------------------------------------------------- #
class HOctreeSubstrat:
    """Hierarchical octree over the [0,1]^3 unit cube.

    Provides octant occupancy (density) used by the optimizer to bias energy
    toward crowded / high-activity regions of the substrate.
    """

    def __init__(self, size: float = 1.0):
        self.size = size

    @staticmethod
    def _octant(pos):
        x, y, z = pos
        return (1 if x >= 0.5 else 0) | (2 if y >= 0.5 else 0) | (4 if z >= 0.5 else 0)

    def occupancy(self, agents):
        """Return a list of 8 densities (0..1) per octant for alive agents."""
        counts = [0] * 8
        alive = [a for a in agents if a["alive"]]
        for a in alive:
            counts[self._octant(a["position"])] += 1
        total = max(1, len(alive))
        return [round(c / total, 4) for c in counts]

    def depth_signature(self, agents):
        """A compact hex signature of the current spatial distribution."""
        occ = self.occupancy(agents)
        raw = "".join(f"{int(o * 255):02x}" for o in occ)
        return raw


# --------------------------------------------------------------------------- #
# KCUV4Core - Vacuum Resonance validator
# --------------------------------------------------------------------------- #
class KCUV4Core:
    """Computes Vacuum Resonance from a WIF private key and a target address."""

    MAGIC = MAGIC_CONSTANT

    def validate(self, wif_key: str, target_address: str) -> dict:
        wif_key = (wif_key or "").strip()
        target_address = (target_address or "").strip()

        if not wif_key or not target_address:
            raise ValueError("Both WIF key and target address are required.")

        # 1. Deterministic entropy from both inputs.
        key_hash = hashlib.sha256(wif_key.encode()).hexdigest()
        target_hash = hashlib.sha256(target_address.encode()).hexdigest()
        combined = hashlib.sha256((key_hash + target_hash).encode()).hexdigest()

        # 2. T45 twist over the first 64 bits of the combined digest.
        seed64 = int(combined[:16], 16)
        twisted = t45_twist(seed64)

        # 3. Derive a positive float and run the fast inverse square root.
        magnitude = (twisted % 1_000_000) / 1000.0 + 1.0  # keep it > 0
        inv_sqrt = fast_inverse_sqrt(magnitude)
        true_inv_sqrt = 1.0 / math.sqrt(magnitude)
        # Relative error of the fast approximation (a signature of the hack).
        error = abs(inv_sqrt - true_inv_sqrt) / true_inv_sqrt if true_inv_sqrt else 0.0

        # 4. Resonance score in [0, 100].
        phase = (twisted % 360)
        resonance = round(abs(math.sin(math.radians(phase)) * inv_sqrt) * 100.0, 6)
        resonance = round(min(100.0, resonance % 100.0), 6)

        # 5. Hash energy: population count of the twisted word, normalized.
        hash_energy = round(bin(twisted).count("1") / 64.0 * 100.0, 4)

        # Locked = resonance crosses the vacuum threshold.
        locked = resonance >= 61.8  # golden-ratio gate

        return {
            "wif_key_fingerprint": key_hash[:16],
            "target_fingerprint": target_hash[:16],
            "combined_hash": combined,
            "magic_constant": f"0x{self.MAGIC:X}",
            "t45_seed": f"0x{seed64:016X}",
            "t45_twisted": f"0x{twisted:016X}",
            "magnitude": round(magnitude, 6),
            "fast_inverse_sqrt": round(inv_sqrt, 10),
            "true_inverse_sqrt": round(true_inv_sqrt, 10),
            "approximation_error": round(error, 10),
            "phase_deg": phase,
            "hash_energy": hash_energy,
            "vacuum_resonance": resonance,
            "locked": locked,
            "validated_at": datetime.now(timezone.utc).isoformat(),
        }


# --------------------------------------------------------------------------- #
# SwarmManager
# --------------------------------------------------------------------------- #
class SwarmManager:
    """Owns the 64 agent slots and advances their physics each cycle."""

    def __init__(self, count: int = AGENT_COUNT):
        self.count = count
        self.octree = HOctreeSubstrat()
        self.agents = self._spawn()

    def _spawn(self):
        agents = []
        for i in range(self.count):
            alive = random.random() > 0.25
            agents.append(
                {
                    "id": i,
                    "alive": alive,
                    "energy": round(random.uniform(40, 100), 2) if alive else 0.0,
                    "position": [round(random.random(), 4) for _ in range(3)],
                    "score": round(random.uniform(0, 50), 2) if alive else 0.0,
                    "flash": False,
                }
            )
        return agents

    def step(self):
        """Advance one cycle: move, decay, die, revive, score."""
        for a in self.agents:
            a["flash"] = False
            if a["alive"]:
                # drift
                a["position"] = [
                    round(min(1.0, max(0.0, p + random.uniform(-0.06, 0.06))), 4)
                    for p in a["position"]
                ]
                # energy decay + occasional harvest
                a["energy"] = round(a["energy"] - random.uniform(0.5, 4.0), 2)
                if random.random() < 0.15:
                    a["energy"] = round(min(100.0, a["energy"] + random.uniform(2, 12)), 2)
                a["score"] = round(a["score"] + random.uniform(0, 3.5), 2)
                if a["energy"] <= 0:
                    a["alive"] = False
                    a["energy"] = 0.0
                    a["flash"] = True
            else:
                # small chance to revive
                if random.random() < 0.05:
                    a["alive"] = True
                    a["energy"] = round(random.uniform(30, 70), 2)
                    a["flash"] = True
        return self.snapshot()

    def revive_all(self):
        for a in self.agents:
            if not a["alive"]:
                a["alive"] = True
                a["energy"] = round(random.uniform(40, 80), 2)
                a["flash"] = True

    def kill(self, agent_id: int):
        if 0 <= agent_id < self.count:
            a = self.agents[agent_id]
            a["alive"] = False
            a["energy"] = 0.0
            a["score"] = 0.0
            a["flash"] = True

    def boost(self, amount: float = 20.0):
        for a in self.agents:
            if a["alive"]:
                a["energy"] = round(min(100.0, a["energy"] + amount), 2)
                a["flash"] = True

    def reset(self):
        self.agents = self._spawn()

    def snapshot(self):
        return [dict(a) for a in self.agents]

    def stats(self):
        alive = [a for a in self.agents if a["alive"]]
        total_energy = round(sum(a["energy"] for a in alive), 2)
        avg_score = round(sum(a["score"] for a in alive) / len(alive), 2) if alive else 0.0
        top = max(self.agents, key=lambda a: a["score"], default=None)
        return {
            "alive": len(alive),
            "dead": self.count - len(alive),
            "total_energy": total_energy,
            "avg_score": avg_score,
            "top_agent": top["id"] if top else None,
            "top_score": top["score"] if top else 0.0,
            "octant_occupancy": self.octree.occupancy(self.agents),
            "depth_signature": self.octree.depth_signature(self.agents),
        }


# --------------------------------------------------------------------------- #
# SultanCoinEngine
# --------------------------------------------------------------------------- #
class SultanCoinEngine:
    """Mints Sultan-Coins from qualifying swarm events."""

    MINT_THRESHOLD = 80.0  # agent score gate

    def evaluate(self, agents) -> list:
        """Return a list of newly minted coin documents (not yet persisted)."""
        minted = []
        for a in agents:
            if a["alive"] and a["score"] >= self.MINT_THRESHOLD:
                minted.append(self._mint(a))
                # reset scored value so the same agent doesn't spam mint
                a["score"] = round(a["score"] - self.MINT_THRESHOLD, 2)
                a["flash"] = True
        return minted

    def _mint(self, agent) -> dict:
        seed = f"{agent['id']}:{agent['score']}:{time.time_ns()}"
        digest = hashlib.sha256(seed.encode()).hexdigest()
        twisted = t45_twist(int(digest[:16], 16))
        amount = round(1.0 + (twisted % 1000) / 1000.0, 6)
        return {
            "id": str(uuid.uuid4()),
            "agent_id": agent["id"],
            "amount": amount,
            "hash": f"SLTN-{digest[:12].upper()}",
            "resonance": round((twisted % 10000) / 100.0, 4),
            "minted_at": datetime.now(timezone.utc).isoformat(),
        }


# --------------------------------------------------------------------------- #
# VantaCoreOptimizer
# --------------------------------------------------------------------------- #
class VantaCoreOptimizer:
    """Reallocates energy toward dense, high-activity octants each pass."""

    def optimize(self, swarm: SwarmManager) -> dict:
        occ = swarm.octree.occupancy(swarm.agents)
        moved = 0.0
        touched = 0
        for a in swarm.agents:
            if not a["alive"]:
                continue
            oct_idx = HOctreeSubstrat._octant(a["position"])
            density = occ[oct_idx]
            # denser octants get an energy + score bias
            bonus = round(density * random.uniform(2, 8), 2)
            if bonus > 0:
                a["energy"] = round(min(100.0, a["energy"] + bonus), 2)
                a["score"] = round(a["score"] + bonus * 0.5, 2)
                a["flash"] = True
                moved += bonus
                touched += 1
        return {
            "octant_occupancy": occ,
            "energy_reallocated": round(moved, 2),
            "agents_optimized": touched,
        }
