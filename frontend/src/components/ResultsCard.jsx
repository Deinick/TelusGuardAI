export default function ResultsCard({ result }) {
  return (
    <div className="card">
      <h2 className="cardTitle">Results</h2>

      {!result ? (
        <p className="muted">Run an analysis to see structured output here.</p>
      ) : (
        <>
          <p className="summary">{result.summary}</p>

          <div className="kv">
            {result.structured.map((item, idx) => (
              <div key={idx} className="kvRow">
                <div className="kvKey">{item.field}</div>
                <div className="kvVal">{item.value}</div>
              </div>
            ))}
          </div>

          <h3 className="subTitle">Next steps</h3>
          <ul className="list">
            {result.nextSteps.map((s, idx) => (
              <li key={idx}>{s}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
