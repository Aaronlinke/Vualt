import React from "react";

// Raw technical panel frame — no rounded corners, 1px borders, header rail.
export const Panel = ({ title, icon: Icon, accent = "#00ff41", right, children, className = "", bodyClassName = "", testId }) => {
  return (
    <section
      data-testid={testId}
      className={`flex flex-col bg-[#0a0a0a] border border-[#222222] rounded-none ${className}`}
    >
      <header className="flex items-center justify-between px-3 py-2 border-b border-[#222222] bg-[#0b0b0b]">
        <div className="flex items-center gap-2 min-w-0">
          {Icon ? <Icon size={13} style={{ color: accent }} strokeWidth={2} /> : null}
          <h2
            className="text-[11px] tracking-[0.22em] uppercase font-bold truncate"
            style={{ color: accent }}
          >
            {title}
          </h2>
        </div>
        {right ? <div className="text-[10px] text-[#8a8a8a] tracking-wider">{right}</div> : null}
      </header>
      <div className={`flex-1 min-h-0 p-3 ${bodyClassName}`}>{children}</div>
    </section>
  );
};

export default Panel;
