import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Landing } from "./routes/Landing";

// Lazy-load each state module so its CSS chunk only loads when the route
// is entered. The two modules share many class names (.app-shell, .container,
// etc.), so route-scoped chunks keep their styles isolated.
const KeralaApp = lazy(() => import("./modules/kerala/KeralaApp"));
const TamilNaduApp = lazy(() => import("./modules/tamilnadu/TamilNaduApp"));

function RouteFallback() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        fontFamily: '"Poppins", "Segoe UI", system-ui, sans-serif',
        color: "#1e2656",
      }}
    >
      Loading dashboard…
    </div>
  );
}

export function App() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/kerala/*" element={<KeralaApp />} />
        <Route path="/tamilnadu/*" element={<TamilNaduApp />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
