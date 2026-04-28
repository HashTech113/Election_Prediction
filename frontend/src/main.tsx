import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { App } from "./App";

const root = ReactDOM.createRoot(document.getElementById("root")!);
const tree = (
  <BrowserRouter>
    <App />
  </BrowserRouter>
);

if (import.meta.env.DEV) {
  root.render(tree);
} else {
  root.render(<React.StrictMode>{tree}</React.StrictMode>);
}
