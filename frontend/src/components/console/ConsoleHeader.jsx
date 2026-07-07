import React from "react";
import { CONSOLE } from "@/constants/testIds";

const Stat = ({ label, value, color = "#e0e0e0", testId }) => (
  <div className="flex flex-col leading-none">
    <span className="text-[9px] tracking-[0.2em] uppercase text-[#6a6a6a]">{label}</span>
    <span data-testid={testId} className="text-[15px] font-bold tabular-nums mt-1" style={{ color }}>
      {value}
    </span>
  </div>
);

export const ConsoleHeader = ({ connected, status }) => {
  const swarm = status?.swarm || {};
  return (
    <header className="flex items-center justify-between border border-[#222222] bg-[#0a0a0a] px-4 py-3">
      <div className="flex items-center gap-4 min-w-0">
        <div className="flex flex-col leading-none">
          <span className="text-[15px] font-extrabold tracking-[0.25em] uppercase text-[#e0e0e0]">
            OASIS<span className="text-[#00ff41]">·</span>SULTAN
          </span>
          <span className="text-[9px] tracking-[0.35em] uppercase text-[#00ff41] mt-1">
            CONSOLE v1 // SultanOSVanta
          </span>
        </div>
        <div className="hidden md:block h-8 w-px bg-[#222222]" />
        <div
          data-testid={CONSOLE.connStatus}
          className="hidden md:flex items-center gap-2 text-[10px] tracking-[0.2em] uppercase"
        >
          <span
            data-testid={CONSOLE.liveDot}
            className={`inline-block h-2 w-2 rounded-none ${connected ? "sultan-live-dot" : ""}`}
            style={{ background: connected ? "#00ff41" : "#ff003c" }}
          />
          <span style={{ color: connected ? "#00ff41" : "#ff003c" }}>
            {connected ? "LINK ACTIVE" : "LINK DOWN"}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <Stat label="CYCLE" value={status?.cycle ?? "—"} color="#00e5ff" testId={CONSOLE.statusCycle} />
        <Stat
          label="ALIVE"
          value={`${swarm.alive ?? "—"}/64`}
          color="#00ff41"
          testId={CONSOLE.statusAlive}
        />
        <Stat label="ENERGY" value={swarm.total_energy ?? "—"} color="#ffb000" testId={CONSOLE.statusEnergy} />
        <Stat label="COINS" value={status?.coins_minted ?? "—"} color="#e0e0e0" testId={CONSOLE.statusCoins} />
      </div>
    </header>
  );
};

export default ConsoleHeader;
