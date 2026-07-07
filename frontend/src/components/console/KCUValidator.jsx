import React, { useState } from "react";
import axios from "axios";
import { KeyRound, Loader2 } from "lucide-react";
import { Panel } from "./Panel";
import { CONSOLE } from "@/constants/testIds";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Readout = ({ k, v, color = "#e0e0e0" }) => (
  <div className="flex items-baseline justify-between gap-3 border-b border-[#141414] py-1">
    <span className="text-[10px] tracking-wider uppercase text-[#6a6a6a] shrink-0">{k}</span>
    <span className="text-[11px] font-tech tabular-nums truncate text-right" style={{ color }}>
      {v}
    </span>
  </div>
);

export const KCUValidator = () => {
  const [wif, setWif] = useState("");
  const [target, setTarget] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [res, setRes] = useState(null);

  const validate = async () => {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      const { data } = await axios.post(`${API}/kcu/validate`, {
        wif_key: wif,
        target_address: target,
      });
      setRes(data);
    } catch (e) {
      setError(e?.response?.data?.detail || "validation failed");
      setRes(null);
    } finally {
      setBusy(false);
    }
  };

  const inputCls =
    "w-full bg-transparent border-0 border-b border-[#222222] focus:border-[#00ff41] text-[12px] text-[#e0e0e0] placeholder:text-[#4a4a4a] py-1.5 outline-none transition-colors duration-75 font-tech";

  return (
    <Panel title="KCU VALIDATOR" icon={KeyRound} testId="kcu-validator" className="h-full">
      <div className="flex flex-col h-full min-h-0">
        <div data-testid={CONSOLE.kcuForm} className="space-y-3">
          <div>
            <label className="text-[9px] tracking-[0.2em] uppercase text-[#6a6a6a]">WIF Private Key</label>
            <input
              data-testid={CONSOLE.kcuWif}
              value={wif}
              onChange={(e) => setWif(e.target.value)}
              placeholder="5J… / L… / K…"
              spellCheck={false}
              className={inputCls}
            />
          </div>
          <div>
            <label className="text-[9px] tracking-[0.2em] uppercase text-[#6a6a6a]">Target Address</label>
            <input
              data-testid={CONSOLE.kcuTarget}
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="1A1zP1… / bc1q…"
              spellCheck={false}
              className={inputCls}
            />
          </div>
          <button
            data-testid={CONSOLE.kcuSubmit}
            onClick={validate}
            disabled={busy}
            className="w-full flex items-center justify-center gap-2 text-[11px] tracking-[0.2em] uppercase font-bold py-2 border border-[#00ff41] text-[#00ff41] hover:bg-[#00ff41] hover:text-black transition-colors duration-75 disabled:opacity-40"
          >
            {busy ? <Loader2 size={13} className="animate-spin" /> : null}
            COMPUTE VACUUM RESONANCE
          </button>
        </div>

        {error ? <p className="text-[11px] text-[#ff003c] mt-3">&gt; {error}</p> : null}

        <div className="flex-1 min-h-0 overflow-y-auto mt-3">
          {res ? (
            <div data-testid={CONSOLE.kcuResult}>
              <div
                className={`flex items-center justify-between border p-2 mb-2 ${
                  res.locked ? "border-[#00ff41]" : "border-[#222222]"
                }`}
                style={{ background: res.locked ? "rgba(0,255,65,0.06)" : "transparent" }}
              >
                <span className="text-[10px] tracking-[0.2em] uppercase text-[#6a6a6a]">
                  Vacuum Resonance
                </span>
                <span
                  data-testid={CONSOLE.kcuResonance}
                  className="text-[22px] font-extrabold tabular-nums"
                  style={{ color: res.locked ? "#00ff41" : "#ffb000" }}
                >
                  {res.vacuum_resonance}
                  <span className="text-[11px] ml-1 text-[#6a6a6a]">{res.locked ? "LOCK" : "OPEN"}</span>
                </span>
              </div>
              <Readout k="magic const" v={res.magic_constant} color="#00e5ff" />
              <Readout k="T45 seed" v={res.t45_seed} />
              <Readout k="T45 twisted" v={res.t45_twisted} color="#00ff41" />
              <Readout k="fast inv√" v={res.fast_inverse_sqrt} color="#00e5ff" />
              <Readout k="true inv√" v={res.true_inverse_sqrt} />
              <Readout k="approx err" v={res.approximation_error} color="#ffb000" />
              <Readout k="hash energy" v={res.hash_energy} color="#ffb000" />
              <Readout k="phase°" v={res.phase_deg} />
              <Readout k="key fp" v={res.wif_key_fingerprint} />
              <Readout k="target fp" v={res.target_fingerprint} />
            </div>
          ) : (
            <p className="text-[11px] text-[#4a4a4a]">
              &gt; T45 logic + 0x5F3759DF fast inverse square root
              <br />
              &gt; awaiting key material<span className="sultan-cursor">_</span>
            </p>
          )}
        </div>
      </div>
    </Panel>
  );
};

export default KCUValidator;
