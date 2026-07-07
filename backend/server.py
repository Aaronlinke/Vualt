import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

from sultan_core import (
    KCUV4Core,
    SultanCoinEngine,
    SwarmManager,
    VantaCoreOptimizer,
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("sultan")

# MongoDB
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

# Core engines (in-memory swarm state)
swarm = SwarmManager()
kcu = KCUV4Core()
coin_engine = SultanCoinEngine()
optimizer = VantaCoreOptimizer()

TICK_INTERVAL = 2.0  # seconds

STATE = {
    "cycle": 0,
    "coins_minted": 0,
    "boot_time": datetime.now(timezone.utc),
    "log": [],  # rolling command log
}


def push_log(entry: str):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {entry}"
    STATE["log"].insert(0, line)
    STATE["log"] = STATE["log"][:50]
    return line


# --------------------------------------------------------------------------- #
# WebSocket connection manager
# --------------------------------------------------------------------------- #
class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


async def persist_coins(coins: list):
    if coins:
        await db.sultan_coins.insert_many([dict(c) for c in coins])
        STATE["coins_minted"] += len(coins)


def build_status() -> dict:
    uptime = (datetime.now(timezone.utc) - STATE["boot_time"]).total_seconds()
    return {
        "cycle": STATE["cycle"],
        "coins_minted": STATE["coins_minted"],
        "uptime_seconds": round(uptime, 1),
        "tick_interval": TICK_INTERVAL,
        "swarm": swarm.stats(),
        "magic_constant": "0x5F3759DF",
    }


async def run_cycle() -> dict:
    """Advance swarm, run optimizer, mint + persist coins, bump cycle."""
    STATE["cycle"] += 1
    swarm.step()
    opt = optimizer.optimize(swarm)
    minted = coin_engine.evaluate(swarm.agents)
    await persist_coins(minted)
    return {"optimize": opt, "minted": minted}


# --------------------------------------------------------------------------- #
# Background auto-tick
# --------------------------------------------------------------------------- #
async def swarm_loop():
    while True:
        try:
            result = await run_cycle()
            payload = {
                "type": "tick",
                "status": build_status(),
                "agents": swarm.snapshot(),
                "minted": result["minted"],
            }
            await manager.broadcast(payload)
        except Exception as e:  # keep the loop alive
            logger.exception("swarm_loop error: %s", e)
        await asyncio.sleep(TICK_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(swarm_loop())
    push_log("SultanOSVanta substrate online. Swarm auto-tick engaged.")
    logger.info("Swarm loop started.")
    yield
    task.cancel()
    client.close()


app = FastAPI(title="Oasis Sultan Console v1", lifespan=lifespan)
api_router = APIRouter(prefix="/api")


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
class CommandRequest(BaseModel):
    command: str


class KCURequest(BaseModel):
    wif_key: str = Field(..., description="WIF private key")
    target_address: str = Field(..., description="Target address")


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
@api_router.get("/")
async def root():
    return {"message": "Oasis Sultan Console v1 :: SultanOSVanta online"}


@api_router.get("/status")
async def get_status():
    return {**build_status(), "log": STATE["log"][:20]}


@api_router.get("/agents")
async def get_agents():
    return {"agents": swarm.snapshot(), "stats": swarm.stats()}


@api_router.post("/cycle")
async def post_cycle():
    result = await run_cycle()
    payload = {
        "type": "tick",
        "status": build_status(),
        "agents": swarm.snapshot(),
        "minted": result["minted"],
    }
    await manager.broadcast(payload)
    return {
        "cycle": STATE["cycle"],
        "optimize": result["optimize"],
        "minted": result["minted"],
    }


@api_router.post("/command")
async def post_command(req: CommandRequest):
    raw = (req.command or "").strip()
    cmd = raw.lower()
    if not cmd:
        raise HTTPException(status_code=400, detail="Empty command.")

    result_msg = ""
    if cmd in ("revive all", "revive", "resurrect"):
        swarm.revive_all()
        result_msg = "Revived all dormant agent slots."
    elif cmd.startswith("kill"):
        parts = cmd.split()
        if len(parts) == 2 and parts[1].isdigit():
            swarm.kill(int(parts[1]))
            result_msg = f"Terminated agent #{parts[1]}."
        else:
            raise HTTPException(status_code=400, detail="Usage: kill <agent_id>")
    elif cmd.startswith("boost"):
        parts = cmd.split()
        amt = float(parts[1]) if len(parts) == 2 and parts[1].replace(".", "").isdigit() else 20.0
        swarm.boost(amt)
        result_msg = f"Injected +{amt} energy across the swarm."
    elif cmd in ("optimize", "vanta", "optimize swarm"):
        opt = optimizer.optimize(swarm)
        result_msg = (
            f"VantaCore pass: reallocated {opt['energy_reallocated']} energy "
            f"across {opt['agents_optimized']} agents."
        )
    elif cmd in ("cycle", "step", "tick"):
        await run_cycle()
        result_msg = f"Manual cycle executed. Now at cycle {STATE['cycle']}."
    elif cmd in ("reset", "reboot"):
        swarm.reset()
        result_msg = "Swarm substrate re-seeded (64 slots respawned)."
    elif cmd in ("status", "stat"):
        s = swarm.stats()
        result_msg = f"Alive {s['alive']}/64 | energy {s['total_energy']} | top #{s['top_agent']}"
    elif cmd in ("help", "?"):
        result_msg = "Commands: revive all | kill <id> | boost <n> | optimize | cycle | reset | status"
    else:
        raise HTTPException(status_code=400, detail=f"Unknown command: {raw}")

    line = push_log(f"$ {raw} -> {result_msg}")
    payload = {"type": "tick", "status": build_status(), "agents": swarm.snapshot(), "minted": []}
    await manager.broadcast(payload)
    return {"command": raw, "result": result_msg, "log_line": line, "status": build_status()}


@api_router.post("/kcu/validate")
async def kcu_validate(req: KCURequest):
    try:
        result = kcu.validate(req.wif_key, req.target_address)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await db.kcu_validations.insert_one(dict(result))
    push_log(
        f"KCU validate -> resonance {result['vacuum_resonance']} "
        f"({'LOCKED' if result['locked'] else 'open'})"
    )
    return result


@api_router.get("/coins")
async def get_coins(limit: int = 50):
    coins = (
        await db.sultan_coins.find({}, {"_id": 0})
        .sort("minted_at", -1)
        .to_list(limit)
    )
    total_agg = await db.sultan_coins.aggregate(
        [{"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}]
    ).to_list(1)
    total = total_agg[0] if total_agg else {"total": 0, "count": 0}
    return {
        "coins": coins,
        "total_supply": round(total.get("total", 0), 6),
        "total_minted": total.get("count", 0),
    }


@app.websocket("/api/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    # send an immediate snapshot on connect
    await ws.send_json(
        {
            "type": "snapshot",
            "status": build_status(),
            "agents": swarm.snapshot(),
            "minted": [],
        }
    )
    try:
        while True:
            await ws.receive_text()  # keepalive / ignore inbound
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
