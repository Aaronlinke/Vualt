export const CONSOLE = {
  root: "sultan-console-root",
  liveDot: "connection-live-dot",
  connStatus: "connection-status",

  // Swarm Command Center
  commandInput: "swarm-command-input",
  commandSubmit: "swarm-command-submit",
  commandLog: "swarm-command-log",
  quickCmd: (name) => `quick-cmd-${name}`,

  // Live Agent Pulse
  pulseGrid: "live-agent-pulse-grid",
  agentCell: (id) => `agent-cell-${id}`,

  // KCU Validator
  kcuForm: "kcu-validator-form",
  kcuWif: "kcu-wif-input",
  kcuTarget: "kcu-target-input",
  kcuSubmit: "kcu-validate-submit",
  kcuResult: "kcu-validator-result",
  kcuResonance: "kcu-resonance-value",

  // Sultan-Coin Ledger
  ledgerTable: "sultan-coin-ledger-table",
  ledgerRow: (id) => `ledger-row-${id}`,
  ledgerSupply: "ledger-total-supply",

  // Status bar
  statusCycle: "status-cycle",
  statusAlive: "status-alive",
  statusEnergy: "status-energy",
  statusCoins: "status-coins",
};
