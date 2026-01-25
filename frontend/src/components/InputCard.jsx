export default function InputCard({
  value,
  onChange,
  onAnalyze,
  onUseSample,
  isLoading,
}) {
  const MAX_LENGTH = 2000;
  const charCount = value.length;

  const handleClear = () => {
    if (!isLoading) {
      onChange("");
    }
  };

  return (
    <div className="card">
      <h2 className="cardTitle">Input</h2>
      <p className="muted">Paste your notes, a report, or any unstructured text below.</p>

      <div style={{ position: "relative" }}>
        <textarea
          className="textarea"
          rows={10}
          value={value}
          maxLength={MAX_LENGTH}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Example: I checked the equipment logs and noticed spikes in vibration around 2pm…"
          disabled={isLoading}
          style={{ width: "100%" }}
        />
        <div
          style={{
            position: "absolute",
            bottom: "8px",
            right: "12px",
            fontSize: "0.95em",
            color: "#999",
            pointerEvents: "none",
            userSelect: "none"
          }}
        >
          {charCount}/{MAX_LENGTH}
        </div>
      </div>

      <div className="row" style={{ marginTop: 10, gap: 8 }}>
        <button
          className="btn"
          onClick={onAnalyze}
          disabled={isLoading || !value.trim()}
        >
          {isLoading ? "Analyzing..." : "Analyze"}
        </button>
        <button
          className="btn secondary"
          onClick={onUseSample}
          disabled={isLoading}
        >
          Use sample input
        </button>
        <button
          className="btn secondary"
          onClick={handleClear}
          disabled={isLoading || !value}
        >
          Clear
        </button>
      </div>
    </div>
  );
}
