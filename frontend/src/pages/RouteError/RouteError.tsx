import { Link, isRouteErrorResponse, useRouteError } from "react-router-dom";

function RouteError() {
  const error = useRouteError();
  const message = isRouteErrorResponse(error)
    ? `${error.status} ${error.statusText}`
    : "An unexpected error occurred while loading ORVEX.";

  return (
    <main className="route-error" aria-labelledby="route-error-title">
      <section className="route-message">
        <p className="route-message-eyebrow">ORVEX</p>
        <h1 id="route-error-title">Unable to load this page</h1>
        <p>{message}</p>
        <Link className="primary-button route-message-action" to="/">
          Return to dashboard
        </Link>
      </section>
    </main>
  );
}

export default RouteError;
