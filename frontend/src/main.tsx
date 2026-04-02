/**
 * Frontend entry point.
 *
 * This file mounts the React application into the root element defined in
 * index.html.
 */

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);