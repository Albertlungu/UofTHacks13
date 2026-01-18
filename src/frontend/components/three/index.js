import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import BlockBuilder3D from "./BlockBuilder3D";
import "./App.css"; // Keep App.css for the companion app

const root = ReactDOM.createRoot(document.getElementById("root"));

const urlParams = new URLSearchParams(window.location.search);
const appParam = urlParams.get("app");

let componentToRender;
if (appParam === "hand_tracking") {
    componentToRender = <BlockBuilder3D />;
} else {
    // Default to App (AI Companion)
    componentToRender = <App />;
}

root.render(<React.StrictMode>{componentToRender}</React.StrictMode>);
