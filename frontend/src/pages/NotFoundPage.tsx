import { Link } from "react-router-dom";
import { Button } from "@/components/ui/Button";

export default function NotFoundPage() {
  return (
    <section className="mx-auto flex max-w-md flex-col items-start gap-2 px-3 py-12">
      <span className="label-uppercase text-accent-600">404</span>
      <h1 className="text-3xl font-semibold tracking-tight text-neutral-900">
        Page not found
      </h1>
      <p className="text-sm text-neutral-600">
        The page you requested does not exist. If this is a medical emergency,
        please call your local emergency number or visit the nearest hospital
        immediately.
      </p>
      <Button asChild>
        <Link to="/">Return home</Link>
      </Button>
    </section>
  );
}
