import { Sparkles } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Field";
import { useAuth } from "@/context/AuthContext";
import { useDocumentTitle } from "@/hooks/useAsync";
import { AuthLayout } from "@/layouts/AuthLayout";
import { ApiError, errorMessage } from "@/services/api";

function validate(name: string, email: string, password: string) {
  const errors: Record<string, string> = {};
  if (!name.trim()) errors.full_name = "Tell us your name";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) errors.email = "Enter a valid email address";
  if (password.length < 8) errors.password = "Use at least 8 characters";
  else if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) errors.password = "Include at least one letter and one number";
  return errors;
}

export default function SignupPage() {
  useDocumentTitle("Create your account");
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFormError(null);
    const v = validate(name, email, password);
    setErrors(v);
    if (Object.keys(v).length) return;
    setLoading(true);
    try {
      await signup(email.trim(), name.trim(), password);
      navigate("/onboarding", { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.fieldErrors.length) {
        setErrors(Object.fromEntries(err.fieldErrors.map((f) => [f.field, f.message])));
      }
      setFormError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Build your mentor" subtitle="Create an account — then we'll shape your twin's voice together.">
      <form onSubmit={onSubmit} className="space-y-5" noValidate>
        {formError && (
          <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {formError}
          </div>
        )}
        <Input
          label="Your name"
          autoComplete="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={errors.full_name}
          required
        />
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={errors.email}
          required
        />
        <Input
          label="Password"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={errors.password}
          hint="At least 8 characters, with a letter and a number."
          required
        />
        <Button type="submit" size="lg" className="w-full" loading={loading} icon={<Sparkles className="h-4 w-4" />}>
          Create account
        </Button>
        <p className="text-center text-sm text-muted">
          Already have a twin?{" "}
          <Link to="/login" className="font-semibold text-chocolate underline decoration-mustard underline-offset-4">
            Sign in
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}
