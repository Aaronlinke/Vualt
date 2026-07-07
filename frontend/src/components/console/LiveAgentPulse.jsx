import React from "react";
import { Activity } from "lucide-react";
import { Panel } from "./Panel";
import { CONSOLE } from "@/constants/testIds";

const AgentCell = ({ agent }) => {
  const alive = agent.alive;
  const energyPct = Math.max(0, Math.min(100, agent.energy));
  const color = alive ? "#00ff41" : "#404040";
  return (
    <div
      data-testid={CONSOLE.agentCell(agent.id)}
      className={`relative flex flex-col justify-between aspect-square p-1 border rounded-none overflow-hidden ${
        agent.flash ? "sultan-flash" : ""
      }`}
      style={{
        borderColor: alive ? "#00ff41" : "#1c1c1c",
        backgroundColor: alive ? "rgba(0,255,65,0.05)" : "#080808",
      }}
      title={`Agent #${agent.id} | ${alive ? "ALIVE" : "DEAD"} | E:${agent.energy} | S:${agent.score}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-[8px] leading-none tabular-nums" style={{ color }}>
          {String(agent.id).padStart(2, "0")}
        </span>
        <span
          className="inline-block h-1 w-1 rounded-none"
          style={{ background: alive ? "#00ff41" : "#2a2a2a" }}
        />
      </div>
      <span className="text-[7px] leading-none tabular-nums" style={{ color: alive ? "#7fbf7f" : "#2f2f2f" }}>
        {alive ? agent.score.toFixed(0) : "--"}
      </span>
      <div className="h-[3px] w-full bg-[#151515]">
        <div
          className="h-full transition-[width] duration-200"
          style={{ width: `${alive ? energyPct : 0}%`, background: alive ? "#00ff41" : "transparent" }}
        />
      </div>
    </div>
  );
};

export const LiveAgentPulse = ({ agents = [], stats }) => {
  const filled = agents.length
    ? agents
    : Array.from({ length: 64 }, (_, i) => ({ id: i, alive: false, energy: 0, score: 0, position: [0, 0, 0] }));

  return (
    <Panel
      title="LIVE AGENT PULSE"
      icon={Activity}
      testId="live-agent-pulse"
      className="h-full"
      right={<span>{stats ? `${stats.alive}/64 online` : "64 slots"}</span>}
    >
      <div className="flex flex-col h-full min-h-0">
        <div data-testid={CONSOLE.pulseGrid} className="grid grid-cols-8 gap-1 flex-1 min-h-0">
          {filled.map((a) => (
            <AgentCell key={a.id} agent={a} />
          ))}
        </div>
        {stats ? (
          <div className="grid grid-cols-4 gap-2 mt-3 pt-3 border-t border-[#141414] text-[9px] tracking-wider uppercase">
            <div className="flex flex-col">
              <span className="text-[#6a6a6a]">avg score</span>
              <span className="text-[#00e5ff] text-[13px] font-bold tabular-nums">{stats.avg_score}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[#6a6a6a]">top agent</span>
              <span className="text-[#00ff41] text-[13px] font-bold tabular-nums">#{stats.top_agent ?? "—"}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[#6a6a6a]">top score</span>
              <span className="text-[#ffb000] text-[13px] font-bold tabular-nums">{stats.top_score}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[#6a6a6a]">octree sig</span>
              <span className="text-[#7fbf7f] text-[11px] font-bold truncate font-tech">
                {stats.depth_signature?.slice(0, 8) ?? "—"}
              </span>
            </div>
          </div>
        ) : null}
      </div>
    </Panel>
  );
};

export default LiveAgentPulse;
