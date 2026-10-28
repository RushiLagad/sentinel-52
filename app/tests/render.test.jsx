// Renders the real app against the real data files and checks the things the
// UI itself is responsible for: no verdict words in rendered text beyond the
// restriction, a SIMULATED badge beside every pounds or meals figure, and a
// confirmation step that never executes anything.
import { describe, it, expect, beforeAll } from "vitest";
import { render, screen, waitFor, fireEvent, within } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import App from "../src/App.jsx";

beforeAll(() => {
  global.fetch = async (url) => {
    const name = String(url).split("/").pop();
    const body = readFileSync(join(process.cwd(), "public", "data", name), "utf8");
    return { ok: true, json: async () => JSON.parse(body) };
  };
  window.scrollTo = () => {};
  Element.prototype.scrollIntoView = () => {};
});

const RESTRICTION = /statement that any food, lot or establishment is safe or unsafe/i;
const VERDICT = /\b(unsafe|is safe|are safe)\b/i;

describe("rendered app", () => {
  it("loads and renders every section", async () => {
    const { container } = render(<App />);
    await waitFor(() => expect(container.querySelector("#risk table tbody tr")).toBeTruthy(), { timeout: 10000 });
    for (const id of ["risk", "alerts", "scenarios", "actions", "equity", "evidence"]) expect(container.querySelector(`#${id}`), id).toBeTruthy();
  });

  it("never renders a safety verdict outside the restriction sentence", async () => {
    const { container } = render(<App />);
    await waitFor(() => expect(container.querySelector("#evidence")).toBeTruthy(), { timeout: 10000 });
    const sentences = container.textContent.split(/(?<=[.!?])\s+/);
    const bad = sentences.filter((s) => VERDICT.test(s) && !RESTRICTION.test(s));
    expect(bad).toEqual([]);
  });

  it("puts a SIMULATED badge in every card or row that shows pounds or meals", async () => {
    const { container } = render(<App />);
    await waitFor(() => expect(container.querySelector("#scenarios")).toBeTruthy(), { timeout: 10000 });
    // Every stat card, scenario card and equity section that mentions lb or meals must carry the badge.
    const holders = [...container.querySelectorAll("#scenarios .card, #equity, #actions .card")];
    const missing = holders.filter((el) => /\b(lb|meals)\b/.test(el.textContent) && !el.querySelector(".badge.synthetic"));
    expect(missing.map((e) => e.textContent.slice(0, 60))).toEqual([]);
  });

  it("blocks a high-consequence action behind a dialog and executes nothing", async () => {
    const { container } = render(<App />);
    await waitFor(() => expect(container.querySelector("#actions button.danger")).toBeTruthy(), { timeout: 10000 });
    fireEvent.click(container.querySelector("#actions button.danger"));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText(/would reverse it/i)).toBeTruthy();
    expect(within(dialog).getByText(/the opposite action/i)).toBeTruthy();
    expect(dialog.textContent).toMatch(/does not hold, divert, or move anything/i);
    expect(dialog.textContent).not.toMatch(/\bexecute\b(?! automatically)/i);
  });
});
