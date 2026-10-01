import { ArrowLeft } from "lucide-react";
import { ButtonLink } from "@/components/ui/Button";
import { visuals } from "@/config/visuals";
import { useDocumentTitle } from "@/hooks/useAsync";

export default function NotFoundPage() {
  useDocumentTitle("Page not found");
  return (
    <main id="main" className="grid min-h-screen place-items-center px-4">
      <div className="text-center">
        <visuals.openBook className="mx-auto h-40 w-auto" />
        <p className="label-hand mt-6">This page isn't in the notebook</p>
        <h1 className="mt-1 text-4xl font-semibold">404 — page not found</h1>
        <p className="mt-3 text-muted">The page you're looking for was moved, deleted, or never written.</p>
        <ButtonLink to="/" className="mt-6" icon={<ArrowLeft className="h-4 w-4" />}>
          Back to the start
        </ButtonLink>
      </div>
    </main>
  );
}
