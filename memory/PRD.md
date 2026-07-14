# PRD — Oasis Sultan Console v1

## Original Problem Statement
Build the 'Oasis Sultan Console v1':
- **Frontend (React, dark high-tech terminal theme)**:
  1. Swarm Command Center — manual logic commands
  2. Live Agent Pulse — 64 agent slots (alive/dead, energy, position, scores) as 8x8 grid/heatmap
  3. KCU Validator — 'Vacuum Resonance' (T45 logic + 0x5F3759DF fast inverse square root) from WIF keys + target addresses
  4. Sultan-Coin Ledger — minted coins in real-time
- **Backend**: SultanOSVanta logic (HOctreeSubstrat, KCUV4Core, SwarmManager, SultanCoinEngine, VantaCoreOptimizer) as FastAPI REST API: `/api/command`, `/api/agents`, `/api/kcu/validate`, `/api/coins`, `/api/status`, `/api/cycle`
- **Real-time**: WebSocket (`/api/ws`) live updates

## User Choices
- Coin ledger persistence: **MongoDB** (collection `sultan_coins`, also `kcu_validations`)
- Swarm auto-tick: **every 2s** (backend background loop broadcasts via WS)
- User language: German (chat); app content English
- Note: original referenced file `sultan_os_vanta_v1.py` did not exist — logic implemented from scratch in `/app/backend/sultan_core.py`

## Implemented (2026-07-07) — MVP COMPLETE ✅
- Backend: `sultan_core.py` (fast_inverse_sqrt 0x5F3759DF, t45_twist 45-bit rotation, HOctreeSubstrat octant occupancy + depth signature, KCUV4Core.validate, SwarmManager 64 agents step/revive/kill/boost/reset, SultanCoinEngine mint at score gate 80.0, VantaCoreOptimizer density-based energy reallocation)
- Backend: `server.py` — all 6 REST endpoints + WS `/api/ws` (snapshot on connect, tick broadcast every 2s), ConnectionManager, lifespan swarm loop, Mongo persistence
- Commands: `revive all | kill <id> | boost <n> | optimize | cycle | reset | status | help` (unknown → 400)
- Frontend: terminal theme per `/app/design_guidelines.json` (JetBrains Mono, #00FF41, rounded-none, scanlines/grain, flash animations)
  - `pages/SultanConsole.jsx`, `hooks/useSultanSocket.js` (auto-reconnect), `components/console/{Panel,ConsoleHeader,SwarmCommandCenter,LiveAgentPulse,KCUValidator,SultanCoinLedger}.jsx`
  - testids in `constants/testIds/console.js`
- Testing: backend 22/22 pytest (`/app/backend/tests/backend_test.py`), frontend 100% Playwright (`/app/test_reports/iteration_1.json`)

## Backlog / Next
- **P1 — User artifacts as enhancement tabs** (user uploaded 3 artifacts, explicitly deferred):
  - CodeLab micro-agent swarm code generator (needs LLM integration → integration_expert + Emergent LLM key)
  - "PowerShell KI-Debatte" (two AIs debate to build a script; Gemini; ZIP export)
  - SYNTH_PROJECT_TERMUX (Flask/SQLite deploy scripts — likely reference only)
  - Artifacts downloaded at /tmp/sultan_artifacts (re-download from customer-assets URLs if gone)
- P2: minor code-review notes from iteration_1.json (WS reconnect timer race, command log dedupe, ledger flash id collision) — all low priority, no functional impact
- P2: enhanced glow/typing animations per design guidelines

## Architecture
- FastAPI (port 8001, supervisor) + MongoDB (MONGO_URL/DB_NAME) + React CRA (port 3000)
- WS URL derived on frontend: `wss://<REACT_APP_BACKEND_URL host>/api/ws`
- No auth required.
