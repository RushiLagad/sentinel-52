import { useEffect, useState } from "react";

// Every number the app shows comes from these files, built by
// analysis/scripts/17_build_app_data.py. The app holds no opinions of its own.
const FILES = ["meta", "current_risk", "alerts", "scenarios", "actions", "evidence", "equity", "burden"];

export function useAppData() {
  const [state, setState] = useState({ status: "loading", data: null, error: null });
  useEffect(() => {
    let alive = true;
    const base = import.meta.env.BASE_URL || "/";
    Promise.all(FILES.map((f) => fetch(`${base}data/${f}.json`).then((r) => {
      if (!r.ok) throw new Error(`${f}.json: HTTP ${r.status}`);
      return r.json();
    })))
      .then((arr) => {
        if (!alive) return;
        const data = Object.fromEntries(FILES.map((f, i) => [f, arr[i]]));
        setState({ status: "ready", data, error: null });
      })
      .catch((e) => alive && setState({ status: "error", data: null, error: String(e) }));
    return () => { alive = false; };
  }, []);
  return state;
}

// Which payloads are simulated is declared by the build, not decided here.
export const isSyntheticPayload = (meta, name) => Array.isArray(meta?.synthetic_payloads) && meta.synthetic_payloads.includes(name);
