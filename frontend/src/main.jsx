import React from "react";
import ReactDOM from "react-dom/client";
import "leaflet/dist/leaflet.css";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import CoverageMapPage from "./pages/CoverageMapPage.jsx";
import { fixLeafletIcons } from "./lib/leafletIcons";
fixLeafletIcons();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <HashRouter>
      <Routes>
        <Route path="/" element={<CoverageMapPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  </React.StrictMode>
);
