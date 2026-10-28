// Calibration (R5.3): of units scored at this level, the share that went on to
// elevated risk. The diagonal is perfect calibration. Deciles are plotted on a
// log scale because nine of ten bins sit below 0.1 and would otherwise stack.
export default function Reliability({ bins, highlightBin }) {
  const W = 420, H = 300, m = { t: 14, r: 14, b: 40, l: 52 };
  const lo = 1e-4, hi = 1;
  const s = (v) => Math.log10(Math.max(v, lo));
  const sx = (v) => m.l + ((s(v) - s(lo)) / (s(hi) - s(lo))) * (W - m.l - m.r);
  const sy = (v) => H - m.b - ((s(v) - s(lo)) / (s(hi) - s(lo))) * (H - m.t - m.b);
  const ticks = [1e-4, 1e-3, 1e-2, 1e-1, 1];
  const lbl = (v) => (v >= 0.1 ? `${Math.round(v * 100)}%` : v >= 0.01 ? "1%" : v >= 0.001 ? "0.1%" : "0.01%");
  return (
    <svg className="chart small" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Reliability diagram: observed rate against predicted probability by decile">
      {ticks.map((v) => <line key={"g" + v} x1={m.l} x2={W - m.r} y1={sy(v)} y2={sy(v)} stroke="var(--line)" />)}
      {ticks.map((v) => <text key={"y" + v} x={m.l - 6} y={sy(v) + 4} fontSize="11" fill="var(--muted)" textAnchor="end">{lbl(v)}</text>)}
      {ticks.map((v) => <text key={"x" + v} x={sx(v)} y={H - m.b + 16} fontSize="11" fill="var(--muted)" textAnchor="middle">{lbl(v)}</text>)}
      <line x1={sx(lo)} y1={sy(lo)} x2={sx(hi)} y2={sy(hi)} stroke="var(--axis)" strokeDasharray="4 4" />
      <text x={(m.l + W - m.r) / 2} y={H - 6} fontSize="11" fill="var(--ink-2)" textAnchor="middle">predicted probability (decile mean)</text>
      <text transform={`translate(12 ${(m.t + H - m.b) / 2}) rotate(-90)`} fontSize="11" fill="var(--ink-2)" textAnchor="middle">observed rate</text>
      {bins.map((b) => (
        <g key={b.bin}>
          <circle cx={sx(b.mean_pred)} cy={sy(b.observed)} r={b.bin === highlightBin ? 7 : 5}
            fill={b.bin === highlightBin ? "var(--c2)" : "var(--c1)"} stroke="var(--surface)" strokeWidth="2" />
          <title>{`decile ${b.bin}: predicted ${(100 * b.mean_pred).toFixed(2)}%, observed ${(100 * b.observed).toFixed(2)}%, n=${b.n}`}</title>
        </g>
      ))}
    </svg>
  );
}
