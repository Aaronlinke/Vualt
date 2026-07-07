import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { Database } from "lucide-react";
import { Panel } from "./Panel";
import { CONSOLE } from "@/constants/testIds";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const SultanCoinLedger = ({ mintFeed = [] }) => {
  const [coins, setCoins] = useState([]);
  const [supply, setSupply] = useState(0);
  const [count, setCount] = useState(0);
  const [freshIds, setFreshIds] = useState(new Set());

  const load = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/coins?limit=60`);
      setCoins(data.coins || []);
      setSupply(data.total_supply || 0);
      setCount(data.total_minted || 0);
    } catch (e) {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // When the socket reports new mints, refresh and flash the new rows.
  useEffect(() => {
    if (!mintFeed.length) return;
    const ids = new Set(mintFeed.map((c) => c.id));
    setFreshIds(ids);
    load();
    const t = setTimeout(() => setFreshIds(new Set()), 900);
    return () => clearTimeout(t);
  }, [mintFeed, load]);

  return (
    <Panel
      title="SULTAN-COIN LEDGER"
      icon={Database}
      accent="#ffb000"
      testId="sultan-coin-ledger"
      className="h-full"
      right={
        <span data-testid={CONSOLE.ledgerSupply}>
          Σ {supply.toFixed(4)} · {count} mints
        </span>
      }
    >
      <div className="flex flex-col h-full min-h-0">
        <div className="grid grid-cols-[3.5rem_1fr_5rem_4.5rem] gap-2 text-[9px] tracking-[0.15em] uppercase text-[#6a6a6a] pb-1 border-b border-[#222222]">
          <span>agent</span>
          <span>hash</span>
          <span className="text-right">amount</span>
          <span className="text-right">reso</span>
        </div>
        <div data-testid={CONSOLE.ledgerTable} className="flex-1 min-h-0 overflow-y-auto">
          {coins.length === 0 ? (
            <p className="text-[11px] text-[#4a4a4a] py-2">&gt; no coins minted yet — swarm must reach score gate 80.0</p>
          ) : (
            coins.map((c) => (
              <div
                key={c.id}
                data-testid={CONSOLE.ledgerRow(c.id)}
                className={`grid grid-cols-[3.5rem_1fr_5rem_4.5rem] gap-2 py-1 border-b border-[#141414] text-[11px] tabular-nums ${
                  freshIds.has(c.id) ? "sultan-flash-cyan" : ""
                }`}
              >
                <span className="text-[#00ff41]">#{String(c.agent_id).padStart(2, "0")}</span>
                <span className="text-[#8a8a8a] font-tech truncate">{c.hash}</span>
                <span className="text-right text-[#ffb000]">{c.amount.toFixed(4)}</span>
                <span className="text-right text-[#00e5ff]">{c.resonance}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </Panel>
  );
};

export default SultanCoinLedger;
