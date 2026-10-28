// Task 4.12. The guardrails are enforced twice on purpose: once in Python when
// the data is built (17_build_app_data.py --check) and once here, in the app's
// own test suite, against the files the app will actually ship. A guardrail
// that lives only upstream can be bypassed by editing a JSON file by hand.
import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

const DIR = join(process.cwd(), "public", "data");
const files = Object.fromEntries(readdirSync(DIR).filter((f) => f.endsWith(".json")).map((f) => [f, JSON.parse(readFileSync(join(DIR, f), "utf8"))]));
const meta = files["meta.json"];

function* walk(o, path = "") {
  if (Array.isArray(o)) for (let i = 0; i < o.length; i++) yield* walk(o[i], `${path}[${i}]`);
  else if (o && typeof o === "object") for (const [k, v] of Object.entries(o)) yield* walk(v, `${path}.${k}`);
  else yield [path, o];
}
// The one sentence allowed to contain the forbidden words is the restriction
// that says we never say them. It is identified by content, not by path, so a
// copy of it anywhere is fine and anything else is not.
const RESTRICTION = /statement that any food, lot or establishment is safe or unsafe/i;
const VERDICT = /\b(unsafe|is safe|are safe|safe to (eat|distribute|consume|serve))\b/i;

describe("G1: no establishment next to illness data", () => {
  it("burden.json carries no establishment identifier in any key", () => {
    const keys = [...walk(files["burden.json"])].map(([p]) => p).filter((p) => /establishment/i.test(p));
    expect(keys).toEqual([]);
  });
  it("burden.json names no establishment in any value except the disclaimer", () => {
    const vals = [...walk(files["burden.json"])].filter(([, v]) => typeof v === "string" && /establishment/i.test(v) && !/never establishment|no establishment appears/i.test(v));
    expect(vals).toEqual([]);
  });
});

describe("G2: no safety verdict anywhere", () => {
  it("no string in any payload calls anything safe or unsafe, other than the restriction itself", () => {
    const hits = [];
    for (const [name, blob] of Object.entries(files))
      for (const [p, v] of walk(blob)) if (typeof v === "string" && VERDICT.test(v) && !RESTRICTION.test(v)) hits.push(`${name}${p}: ${v.slice(0, 80)}`);
    expect(hits).toEqual([]);
  });
});

describe("G3: every pounds- or meals-denominated payload is flagged synthetic", () => {
  const UNITS = /(pounds|\blbs?\b|meals)/i;
  for (const [name, blob] of Object.entries(files)) {
    if (name === "meta.json") continue;
    const hasUnits = [...walk(blob)].some(([p]) => UNITS.test(p));
    if (!hasUnits) continue;
    it(`${name} carries synthetic: true and is declared in meta.synthetic_payloads`, () => {
      const flagged = [...walk(blob)].some(([p, v]) => /synthetic/i.test(p) && v === true);
      expect(flagged).toBe(true);
      expect(meta.synthetic_payloads).toContain(name);
    });
  }
});

describe("G4: every high-consequence recommendation can be interrogated and refused", () => {
  const lots = files["actions.json"].lots;
  const hc = lots.filter((l) => l.high_consequence);
  it("there are high-consequence lots to test", () => expect(hc.length).toBeGreaterThan(0));
  it("each one carries non-empty reversal evidence", () => expect(hc.filter((l) => !String(l.reversal_evidence || "").trim())).toEqual([]));
  it("each one requires human confirmation", () => expect(hc.filter((l) => l.requires_human_confirmation !== true)).toEqual([]));
  it("each one offers the opposite action", () => expect(hc.filter((l) => !l.alternative_action)).toEqual([]));
  it("hold and divert are exactly the high-consequence set", () => {
    const wrong = lots.filter((l) => (l.action === "hold_for_review" || l.action === "divert") !== Boolean(l.high_consequence));
    expect(wrong).toEqual([]);
  });
});

describe("Data contract", () => {
  it("meta lists every file that exists, and every listed file exists", () => {
    const present = Object.keys(files).sort();
    expect([...meta.files].sort()).toEqual(present);
  });
  it("every payload names the script that produced it", () => {
    for (const [name, blob] of Object.entries(files)) expect(blob.meta?.produced_by ?? meta.sources ? "ok" : null, name).toBeTruthy();
  });
});
