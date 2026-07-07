import React from "react";
import { useSultanSocket } from "@/hooks/useSultanSocket";
import { ConsoleHeader } from "@/components/console/ConsoleHeader";
import { SwarmCommandCenter } from "@/components/console/SwarmCommandCenter";
import { LiveAgentPulse } from "@/components/console/LiveAgentPulse";
import { KCUValidator } from "@/components/console/KCUValidator";
import { SultanCoinLedger } from "@/components/console/SultanCoinLedger";
import { CONSOLE } from "@/constants/testIds";

export default function SultanConsole() {
  const { connected, agents, status, mintFeed } = useSultanSocket();
  const stats = status?.swarm;

  return (
    <div
      data-testid={CONSOLE.root}
      className="sultan-scanlines sultan-grain min-h-screen bg-[#050505] text-[#e0e0e0] p-4"
    >
      <div className="max-w-[1600px] mx-auto flex flex-col gap-4">
        <ConsoleHeader connected={connected} status={status} />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Left column: command + KCU */}
          <div className="lg:col-span-4 flex flex-col gap-4 min-h-0">
            <div className="h-[340px]">
              <SwarmCommandCenter log={status?.log || []} />
            </div>
            <div className="h-[520px]">
              <KCUValidator />
            </div>
          </div>

          {/* Center column: agent pulse */}
          <div className="lg:col-span-5 min-h-0">
            <div className="h-[876px]">
              <LiveAgentPulse agents={agents} stats={stats} />
            </div>
          </div>

          {/* Right column: ledger */}
          <div className="lg:col-span-3 min-h-0">
            <div className="h-[876px]">
              <SultanCoinLedger mintFeed={mintFeed} />
            </div>
          </div>
        </div>

        <footer className="text-[9px] tracking-[0.25em] uppercase text-[#4a4a4a] text-center py-2">
          SultanOSVanta // HOctreeSubstrat · KCUV4Core · SwarmManager · SultanCoinEngine · VantaCoreOptimizer
        </footer>
      </div>
    </div>
  );
}
