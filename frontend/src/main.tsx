import { MotionConfig } from "framer-motion";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./context/AuthContext";
import { OptionsProvider } from "./context/OptionsContext";
import { ToastProvider } from "./context/ToastContext";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <MotionConfig reducedMotion="user">
      <ToastProvider>
        <AuthProvider>
          <OptionsProvider>
            <App />
          </OptionsProvider>
        </AuthProvider>
      </ToastProvider>
      </MotionConfig>
    </BrowserRouter>
  </StrictMode>,
);
