import { useMemo, useState } from "react";
import Header from "./components/Header";
import InputCard from "./components/InputCard";
import ResultsCard from "./components/ResultsCard";
import StatusBanner from "./components/StatusBanner";
import "./styles.css";

const SAMPLE_INPUT = `I did chest day: bench press 3x8, incline dumbbell press 3x10, push-ups 2 sets to near failure. Felt slight shoulder discomfort.`;

export default function App() {
  const [text, setText] = useState("");
  const [status, setStatus] = useState("idle"); // idle | loading | error | success
  const [errorMsg, setErrorMsg] = useState("");
  const [result, setResult] = useState(null);

  const mockResult = useMemo(
    () => ({
      summary:
        "Converted your workout notes into structured data and next steps.",
      structured: [
        { field: "Workout Type", value: "Upper (Chest)" },
        { field: "Exercises", value: "Bench, Incline DB Press, Push-ups" },
        { field: "Volume", value: "3 + 3 + 2 sets" },
        { field: "Flag", value: "Shoulder discomfort" },
      ],
      nextSteps: [
        "Warm up shoulders (band external rotations) before pressing",
        "Reduce bench load slightly if discomfort persists",
        "Track RPE for each set next session",
      ],
    }),
    []
  );

  function handleUseSample() {
    setText(SAMPLE_INPUT);
    setStatus("idle");
    setErrorMsg("");
    setResult(null);
  }

  async function handleAnalyze() {
    if (!text.trim()) return;

    // For now: mock analyze (no backend needed)
    setStatus("loading");
    setErrorMsg("");
    setResult(null);

    try {
      await new Promise((r) => setTimeout(r, 700)); // simulate latency
      setResult(mockResult);
      setStatus("success");
    } catch (e) {
      setErrorMsg("Something went wrong. Please try again.");
      setStatus("error");
    }
  }

  return (
    <div className="page">
      <Header
        title="AI at the Edge"
        tagline="Turn real-world inputs into structured insights in seconds."
      />

      <main className="grid">
        <section className="col">
          <InputCard
            value={text}
            onChange={setText}
            onAnalyze={handleAnalyze}
            onUseSample={handleUseSample}
            isLoading={status === "loading"}
          />
        </section>

        <section className="col">
          <StatusBanner status={status} errorMsg={errorMsg} />
          <ResultsCard result={result} />
        </section>
      </main>
    </div>
  );
}
