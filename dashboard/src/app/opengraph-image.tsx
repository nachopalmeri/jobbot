import { ImageResponse } from "next/og";

export const size = {
  width: 1200,
  height: 630,
};

export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          display: "flex",
          height: "100%",
          width: "100%",
          background:
            "radial-gradient(circle at top left, rgba(99,102,241,0.45), transparent 28%), radial-gradient(circle at bottom right, rgba(245,158,11,0.35), transparent 26%), linear-gradient(180deg, #0f172a, #111827 42%, #1c1917)",
          color: "white",
          fontFamily: "sans-serif",
          padding: "64px",
          flexDirection: "column",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <div style={{ fontSize: 24, letterSpacing: 6, textTransform: "uppercase", color: "#c7d2fe" }}>
            JobBot
          </div>
          <div style={{ fontSize: 70, fontWeight: 700, lineHeight: 1.05, maxWidth: 900 }}>
            Búsqueda laboral tech con dashboard, CV intelligence y bot conectados al sistema real.
          </div>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 28, color: "#e5e7eb" }}>
          <div>LATAM-focused job search platform</div>
          <div>jobbot.ar</div>
        </div>
      </div>
    ),
    size,
  );
}
