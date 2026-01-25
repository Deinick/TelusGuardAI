export default function StatusBanner({ status, errorMsg }) {
  if (status === "loading") {
    return <div className="banner info">Processing…</div>;
  }
  if (status === "error") {
    return <div className="banner error">{errorMsg || "Error"}</div>;
  }
  if (status === "success") {
    return <div className="banner success">Done ✅</div>;
  }
  return <div className="banner idle">Ready.</div>;
}
