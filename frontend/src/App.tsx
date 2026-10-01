import { AnimatePresence } from "framer-motion";
import { lazy, Suspense, type ReactNode } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { LoadingState } from "@/components/ui/Feedback";
import { useAuth } from "@/context/AuthContext";
import AppLayout from "@/layouts/AppLayout";
import LandingPage from "@/pages/Landing";

const LoginPage = lazy(() => import("@/pages/Login"));
const SignupPage = lazy(() => import("@/pages/Signup"));
const OnboardingPage = lazy(() => import("@/pages/Onboarding"));
const NotFoundPage = lazy(() => import("@/pages/NotFound"));
const DashboardPage = lazy(() => import("@/pages/app/Dashboard"));
const ChatPage = lazy(() => import("@/pages/app/Chat"));
const KnowledgePage = lazy(() => import("@/pages/app/Knowledge"));
const ExperiencesPage = lazy(() => import("@/pages/app/Experiences"));
const PersonalityPage = lazy(() => import("@/pages/app/Personality"));
const MemoryInspectorPage = lazy(() => import("@/pages/app/MemoryInspector"));
const InsightsPage = lazy(() => import("@/pages/app/Insights"));
const SettingsPage = lazy(() => import("@/pages/app/Settings"));

function FullPageLoader() {
  return (
    <div className="grid min-h-screen place-items-center">
      <LoadingState label="Opening your study…" />
    </div>
  );
}

/** Requires a valid session; sends un-onboarded users to onboarding first. */
function RequireAuth({ children, allowIncompleteOnboarding = false }: { children: ReactNode; allowIncompleteOnboarding?: boolean }) {
  const { status, user } = useAuth();
  const location = useLocation();
  if (status === "loading") return <FullPageLoader />;
  if (status === "anonymous" || !user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (!allowIncompleteOnboarding && !user.onboarding_completed) return <Navigate to="/onboarding" replace />;
  return <>{children}</>;
}

function GuestOnly({ children }: { children: ReactNode }) {
  const { status, user } = useAuth();
  if (status === "loading") return <FullPageLoader />;
  if (user) return <Navigate to={user.onboarding_completed ? "/app" : "/onboarding"} replace />;
  return <>{children}</>;
}

export default function App() {
  const location = useLocation();
  return (
    <Suspense fallback={<FullPageLoader />}>
      <AnimatePresence mode="wait" initial={false}>
        <Routes location={location} key={location.pathname.startsWith("/app") ? "app" : location.pathname}>
          <Route path="/" element={<LandingPage />} />
          <Route
            path="/login"
            element={
              <GuestOnly>
                <LoginPage />
              </GuestOnly>
            }
          />
          <Route
            path="/signup"
            element={
              <GuestOnly>
                <SignupPage />
              </GuestOnly>
            }
          />
          <Route
            path="/onboarding"
            element={
              <RequireAuth allowIncompleteOnboarding>
                <OnboardingPage />
              </RequireAuth>
            }
          />
          <Route
            path="/app"
            element={
              <RequireAuth>
                <AppLayout />
              </RequireAuth>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="chat" element={<ChatPage />} />
            <Route path="chat/:conversationId" element={<ChatPage />} />
            <Route path="knowledge" element={<KnowledgePage />} />
            <Route path="experiences" element={<ExperiencesPage />} />
            <Route path="personality" element={<PersonalityPage />} />
            <Route path="memory" element={<MemoryInspectorPage />} />
            <Route path="insights" element={<InsightsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AnimatePresence>
    </Suspense>
  );
}
