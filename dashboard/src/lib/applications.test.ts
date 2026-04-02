import { describe, expect, it } from "vitest";

import {
  formatApplicationDate,
  getApplicationStatusMeta,
  groupApplications,
  normalizeApplicationStatus,
} from "./applications";

describe("application helpers", () => {
  it("normalizes unknown statuses back to aplicado", () => {
    expect(normalizeApplicationStatus("pending-review")).toBe("aplicado");
    expect(getApplicationStatusMeta("pending-review").label).toBe("Aplicado");
  });

  it("groups applications by kanban status", () => {
    const grouped = groupApplications([
      { id: 1, job_title: "Backend", company: "A", status: "aplicado" },
      { id: 2, job_title: "Frontend", company: "B", status: "entrevista" },
      { id: 3, job_title: "Data", company: "C", status: "entrevista" },
    ]);

    expect(grouped.find((column) => column.status === "aplicado")?.items).toHaveLength(1);
    expect(grouped.find((column) => column.status === "entrevista")?.items).toHaveLength(2);
  });

  it("returns Sin fecha for invalid application dates", () => {
    expect(formatApplicationDate("not-a-date")).toBe("Sin fecha");
    expect(formatApplicationDate(null)).toBe("Sin fecha");
  });
});
