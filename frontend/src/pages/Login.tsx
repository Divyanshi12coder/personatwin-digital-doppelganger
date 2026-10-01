import { LogIn } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Field";
import { useAuth } from "@/context/AuthContext";
import { useDocumentTitle } from "@/hooks/useAsync";
import { AuthLayout } from "@/layouts/AuthLayout";
import { errorMessage } from "@/services/api";

export default function LoginPage() {
  useDocumentTitle("Sign in");
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from;
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await login(email.trim(), password);
      navigate(user.onboarding_completed ? (from && from.startsWith("/app") ? from : "/app") : "/onboarding", {
        replace: true,
      });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Welcome back" subtitle="Open your study and pick up where you left off.">
      <form onSubmit={onSubmit} className="space-y-5" noValidate>
        {error && (
          <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </div>
        )}
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <Button type="submit" size="lg" className="w-full" loading={loading} icon={<LogIn className="h-4 w-4" />}>
          Sign in
        </Button>
        <p className="text-center text-sm text-muted">
          New to PersonaTwin?{" "}
          <Link to="/signup" className="font-semibold text-chocolate underline decoration-mustard underline-offset-4">
            Build your mentor
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}
