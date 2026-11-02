// AI-assisted (Kiro). Renders CurrentRiskView against the real current_risk.json
// and checks the Export CSV button: the header line names every table column
// and the body holds one row per unit shown. The export writes through a Blob
// and an object URL, so both are stubbed here to capture the text the button
// would have downloaded.
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { createElement } from "react";
import { render, fireEvent } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import CurrentRiskView from "../src/components/CurrentRiskView.jsx";

// This file is plain .js, so JSX is off here. Build the element directly.
const view = () => createElement(CurrentRiskView, { risk, names: {}, onPick: () => {}, picked: null });

const risk = JSON.parse(readFileSync(join(process.cwd(), "public", "data", "current_risk.json"), "utf8"));

const EXPECTED_HEADER =
  "plant_name,establishment_id,product_class,fsis_category,score,observed_rate_52w," +
  "rate_interval_95_lo,rate_interval_95_hi,samples_52w,positives_52w," +
  "calibration_band_observed,calibration_band_mean_predicted,calibration_band_n";

// Capture whatever the component hands to Blob, since jsdom gives us no download.
let captured = "";
let origCreate, origRevoke, origBlob;

beforeEach(() => {
  captured = "";
  origBlob = global.Blob;
  origCreate = URL.createObjectURL;
  origRevoke = URL.revokeObjectURL;
  global.Blob = class {
    constructor(parts) { captured = parts.join(""); }
  };
  URL.createObjectURL = () => "blob:stub";
  URL.revokeObjectURL = () => {};
});

afterEach(() => {
  global.Blob = origBlob;
  URL.createObjectURL = origCreate;
  URL.revokeObjectURL = origRevoke;
});

function clickExport(container) {
  const btn = [...container.querySelectorAll("button")].find((b) => b.textContent === "Export CSV");
  expect(btn).toBeTruthy();
  fireEvent.click(btn);
  return captured.trimEnd().split("\n");
}

describe("Export CSV", () => {
  it("writes a header naming every column the table shows", () => {
    const { container } = render(view());
    const lines = clickExport(container);
    expect(lines[0]).toBe(EXPECTED_HEADER);
  });

  it("writes one data row per unit when the supplier filter is off", () => {
    const { container } = render(view());
    // The view defaults to suppliers only; turn it off to export the full set.
    const supplierBox = container.querySelector('input[type="checkbox"]');
    fireEvent.click(supplierBox);
    const lines = clickExport(container);
    expect(lines.length - 1).toBe(risk.units.length);
  });

  it("exports only the filtered rows when the supplier filter is on", () => {
    const { container } = render(view());
    const lines = clickExport(container);
    const suppliers = risk.units.filter((u) => u.is_supplier).length;
    expect(lines.length - 1).toBe(suppliers);
  });
});
