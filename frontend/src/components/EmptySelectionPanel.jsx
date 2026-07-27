export default function EmptySelectionPanel() {
  return (
    <div
      style={{
        minHeight: 420,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        padding: 24,
        color: "rgba(255,255,255,0.70)",
      }}
    >
      <div>
        <div style={{ fontSize: 34, marginBottom: 12, opacity: 0.9 }}>ⓘ</div>
        <div style={{ fontSize: 16, fontWeight: 800, color: "rgba(255,255,255,0.92)" }}>
          Select a tower or impact area
        </div>
        <div style={{ fontSize: 13, marginTop: 8, opacity: 0.85 }}>
          Click any station marker or impact area on the map to view details.
        </div>
      </div>
    </div>
  );
}
