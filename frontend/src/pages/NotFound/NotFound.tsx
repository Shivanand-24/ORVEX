import { Link } from "react-router-dom";

function NotFound() {
  return (
    <section className="route-message" aria-labelledby="not-found-title">
      <p className="route-message-eyebrow">404</p>
      <h1 id="not-found-title">Page not found</h1>
      <p>The ORVEX page you requested does not exist.</p>
      <Link className="primary-button route-message-action" to="/">
        Return to dashboard
      </Link>
    </section>
  );
}

export default NotFound;
