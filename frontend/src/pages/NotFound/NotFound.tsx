import { Link } from "react-router-dom";
import { ArrowLeft, Bot, Database, LayoutDashboard, Workflow } from "lucide-react";

function NotFound() {
  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "70vh" }}>
      <section className="route-message" aria-labelledby="not-found-title" style={{ maxWidth: "580px", width: "100%" }}>
        <p className="route-message-eyebrow">404 ERROR</p>
        <h1 id="not-found-title">Page Not Found</h1>
        <p>The ORVEX resource or route you requested could not be located in this workspace.</p>

        <div style={{ marginTop: "24px", paddingTop: "20px", borderTop: "1px solid var(--orvex-border)" }}>
          <p style={{ fontSize: "12px", color: "var(--orvex-text-muted)", marginBottom: "12px" }}>Quick Navigation</p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "10px" }}>
            <Link to="/" className="secondary-button" style={{ justifyContent: "flex-start", fontSize: "13px" }}>
              <LayoutDashboard size={15} /> Dashboard
            </Link>
            <Link to="/assistant" className="secondary-button" style={{ justifyContent: "flex-start", fontSize: "13px" }}>
              <Bot size={15} /> AI Assistant
            </Link>
            <Link to="/knowledge" className="secondary-button" style={{ justifyContent: "flex-start", fontSize: "13px" }}>
              <Database size={15} /> Knowledge
            </Link>
            <Link to="/workflows" className="secondary-button" style={{ justifyContent: "flex-start", fontSize: "13px" }}>
              <Workflow size={15} /> Workflows
            </Link>
          </div>
        </div>

        <div style={{ marginTop: "24px" }}>
          <Link className="primary-button route-message-action" to="/">
            <ArrowLeft size={16} /> Return to Dashboard
          </Link>
        </div>
      </section>
    </div>
  );
}

export default NotFound;
