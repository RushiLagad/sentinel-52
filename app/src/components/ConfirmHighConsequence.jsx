import { useEffect } from "react";
import { fmtLbs, actionLabel } from "../lib/format.js";
import SyntheticBadge from "./SyntheticBadge.jsx";

// R4.4 and R4.5. Hold and divert are high-consequence. This dialog blocks them
// until a human has read what the recommendation rests on, what would reverse
// it, and what the opposite action would cost. Confirming records an
// acknowledgement in the page only. Nothing is executed, here or anywhere.
export default function ConfirmHighConsequence({ lot, onClose, onAcknowledge }) {
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  if (!lot) return null;
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="hc-title" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2 id="hc-title"><span className="badge hc">HIGH-CONSEQUENCE</span> {actionLabel[lot.action]}</h2>
        <p className="ink2">Lot <code>{lot.lot_id}</code> · {lot.establishment_name} · {lot.product_class.replace(/_/g, " ")}</p>
        <dl className="kv">
          <dt>Driving signal</dt><dd>{lot.driver}</dd>
          <dt>What it costs</dt><dd>{fmtLbs(lot.pounds)} <SyntheticBadge /> destined for {lot.dest_county} ({lot.svi_quartile})</dd>
          <dt>Would reverse it</dt><dd>{lot.reversal_evidence || "—"}</dd>
          <dt>The opposite action</dt><dd>{actionLabel[lot.alternative_action]} — keeps {fmtLbs(lot.pounds)} <SyntheticBadge /> in direct distribution and accepts the signal above.</dd>
        </dl>
        <p className="notice">This confirms that a person has read the recommendation. It does not hold, divert, or move anything. No action in this tool is ever executed automatically.</p>
        <div className="actions">
          <button className="ghost" onClick={onClose}>Back</button>
          <button className="danger" onClick={() => { onAcknowledge(lot.lot_id); onClose(); }}>I have read this — record my acknowledgement</button>
        </div>
      </div>
    </div>
  );
}
