import { describe, expect, it } from "vitest";

import {
  buildGoalMessage,
  formatApplicationDate,
  getDailyQuote,
  motivationalQuotes,
} from "./dashboard";

describe("dashboard helpers", () => {
  it("returns a deterministic daily quote", () => {
    const date = new Date(Date.UTC(2026, 3, 2));

    const quote = getDailyQuote(date);

    expect(motivationalQuotes).toContain(quote);
    expect(getDailyQuote(date)).toBe(quote);
  });

  it("builds a progress message when there are applications remaining", () => {
    expect(buildGoalMessage(2, 5)).toBe(
      "Te faltan 3 postulaciones para cumplir tu objetivo de esta semana.",
    );
  });

  it("acknowledges when the weekly goal is already complete", () => {
    expect(buildGoalMessage(5, 5)).toContain("Meta cumplida");
  });

  it("formats missing dates gracefully", () => {
    expect(formatApplicationDate()).toBe("Sin fecha");
  });
});
