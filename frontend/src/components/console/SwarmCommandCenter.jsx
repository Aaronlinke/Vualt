import React, { useState } from "react";
import axios from "axios";
import { Terminal } from "lucide-react";
import { Panel } from "./Panel";
import { CONSOLE } from "@/constants/testIds";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const QUICK = ["revive all", "boost 20", "optimize", "cycle", "reset"];

export const SwarmCommandCenter = ({ log = [] }) => {
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [localLog, setLocalLog] = useState([]);

  const merged = [...localLog, ...log].slice(0, 60);

  const send = async (cmd) => {
    const command = (cmd ?? value).trim();
    if (!command || busy) return;
    setBusy(true);
    try {
      const { data } = await axios.post(`${API}/command`, { command });
      setLocalLog((prev) => [data.log_line, ...prev].slice(0, 20));
    } catch (e) {
      const detail = e?.response?.data?.detail || "command rejected";
      setLocalLog((prev) => [`[ERR] $ ${command} -> ${detail}`, ...prev].slice(0, 20));
    } finally {
      setValue("");
      setBusy(false);
    }
  };

  return (
    <Panel title="SWARM COMMAND CENTER" icon={Terminal} testId="swarm-command-center" className="h-full">
      <div className="flex flex-col h-full min-h-0">
        <div className="flex flex-wrap gap-1.5 mb-3">
          {QUICK.map((q) => (
            <button
              key={q}
              data-testid={CONSOLE.quickCmd(q.replace(/\s+/g, "-"))}
              onClick={() => send(q)}
              disabled={busy}
              className="text-[10px] tracking-wider uppercase px-2 py-1 border border-[#222222] text-[#8a8a8a] hover:border-[#00ff41] hover:text-[#00ff41] transition-colors duration-75 rounded-none disabled:opacity-40"
            >
              {q}
            </button>
          ))}
        </div>

        <div className="flex items-center border border-[#222222] focus-within:border-[#00ff41] bg-[#080808] px-2 transition-colors duration-75">
          <span className="text-[#00ff41] text-sm font-bold mr-2 select-none">$</span>
          <input
            data-testid={CONSOLE.commandInput}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="enter logic command… (type help)"
            spellCheck={false}
            className="flex-1 bg-transparent text-[13px] text-[#e0e0e0] placeholder:text-[#4a4a4a] py-2 outline-none"
          />
          <button
            data-testid={CONSOLE.commandSubmit}
            onClick={() => send()}
            disabled={busy}
            className="text-[10px] tracking-widest uppercase text-[#00ff41] hover:text-black hover:bg-[#00ff41] px-2 py-1 transition-colors duration-75 disabled:opacity-40"
          >
            EXEC
          </button>
        </div>

        <div
          data-testid={CONSOLE.commandLog}
          className="flex-1 min-h-0 overflow-y-auto mt-3 border border-[#141414] bg-[#060606] p-2 space-y-0.5"
        >
          {merged.length === 0 ? (
            <p className="text-[11px] text-[#4a4a4a]">
              &gt; awaiting operator input<span className="sultan-cursor">_</span>
            </p>
          ) : (
            merged.map((line, i) => (
              <p
                key={i}
                className={`text-[11px] leading-relaxed break-words ${
                  line.startsWith("[ERR]") ? "text-[#ff003c]" : "text-[#7fbf7f]"
                }`}
              >
                {line}
              </p>
            ))
          )}
        </div>
      </div>
    </Panel>
  );
};

export default SwarmCommandCenter;
