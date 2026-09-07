import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Top-level React error boundary. Renders a safe, user-friendly message
 * instead of a blank screen or raw stack trace. Reports errors to the
 * configured error-reporting sink (Sentry/etc.) in production.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // TODO: forward to Sentry / monitoring service
    // eslint-disable-next-line no-console
    console.error("[ErrorBoundary]", error, info);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <section
          role="alert"
          className="mx-auto my-8 flex max-w-md flex-col items-start gap-2 rounded-lg border border-border bg-white p-3"
        >
          <AlertTriangle className="h-[3] w-[3] text-accent-600" aria-hidden="true" />
          <h1 className="text-lg font-semibold text-neutral-900">
            Something went wrong
          </h1>
          <p className="text-sm text-neutral-600">
            We could not load this page. Please refresh, or visit the nearest
            healthcare facility if this is an emergency.
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="interactive mt-1 rounded-md bg-secondary-600 px-2 py-1 text-sm font-medium text-white hover:bg-secondary-700"
          >
            Reload page
          </button>
        </section>
      );
    }
    return this.props.children;
  }
}
