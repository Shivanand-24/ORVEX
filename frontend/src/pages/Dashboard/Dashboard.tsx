import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Bot,
  CheckCircle2,
  Database,
  Plus,
  Sparkles,
  Workflow,
  TrendingUp,
} from "lucide-react";
import { agentRepository } from "../../services/agentRepository";
import { knowledgeRepository } from "../../services/knowledgeRepository";
import { workflowRepository } from "../../services/workflowRepository";
import { analyticsRepository, type TimeRange } from "../../services/analyticsRepository";

function Dashboard() {
  const navigate = useNavigate();
  const [timeRange, setTimeRange] = useState<TimeRange>("30d");

  const [agents, setAgents] = useState(() => agentRepository.list());
  const [workflows, setWorkflows] = useState(() => workflowRepository.list());
  const [documents, setDocuments] = useState(() => knowledgeRepository.listDocuments());
  const [summary, setSummary] = useState(() => analyticsRepository.getSummary(timeRange));
  const [trends, setTrends] = useState(() => analyticsRepository.getTrends(timeRange));

  useEffect(() => {
    const unsubAgent = agentRepository.subscribe(() => setAgents(agentRepository.list()));
    const unsubWf = workflowRepository.subscribe(() => setWorkflows(workflowRepository.list()));
    const unsubKb = knowledgeRepository.subscribe(() => setDocuments(knowledgeRepository.listDocuments()));
    const unsubAnalytics = analyticsRepository.subscribe(() => {
      setSummary(analyticsRepository.getSummary(timeRange));
      setTrends(analyticsRepository.getTrends(timeRange));
    });

    return () => {
      unsubAgent();
      unsubWf();
      unsubKb();
      unsubAnalytics();
    };
  }, [timeRange]);

  const activeAgentsCount = agents.filter((a) => a.status === "Active").length;
  const activeWorkflowsCount = workflows.filter((w) => w.status === "Active").length;
  const indexedDocsCount = documents.filter((d) => d.readiness === "Indexed").length;



  const systemStatus = [
    { name: "AI Router & Assistant", status: "Operational", lat: "14ms" },
    { name: "Knowledge Ingestion Engine", status: "Operational", lat: "28ms" },
    { name: "Agent Execution Worker", status: "Operational", lat: "19ms" },
    { name: "Workflow Orchestrator", status: "Operational", lat: "22ms" },
  ];

  const recentActivity = [
    {
      type: "AI",
      message: 'Research Agent finished analyzing "Employee Handbook 2026"',
      time: "2 minutes ago",
      icon: Bot,
      link: "/agents",
    },
    {
      type: "WF",
      message: 'Workflow "Employee Data Sync" executed 14 steps successfully',
      time: "18 minutes ago",
      icon: Workflow,
      link: "/workflows",
    },
    {
      type: "KB",
      message: 'Document "Remote Work Policy" is now RAG-indexed',
      time: "1 hour ago",
      icon: Database,
      link: "/knowledge",
    },
    {
      type: "SEC",
      message: "Automated compliance audit scan passed with 0 issues",
      time: "3 hours ago",
      icon: CheckCircle2,
      link: "/settings",
    },
  ];

  return (
    <div className="dashboard-page">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p>Good morning, Shivanand. Welcome to ORVEX Enterprise Intelligence Control.</p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <button
            className="secondary-button"
            type="button"
            onClick={() => navigate("/assistant")}
          >
            <Sparkles size={15} style={{ color: "#0E6B63" }} /> Ask Assistant
          </button>
          <button
            className="primary-button"
            type="button"
            onClick={() => navigate("/create-workflow")}
          >
            <Plus size={15} /> Create Workflow
          </button>
        </div>
      </div>

      {/* Executive Metric Strip */}
      <div className="executive-metric-strip">
        <div className="metric-strip-item">
          <span className="metric-strip-label">Active Agents</span>
          <div className="metric-strip-value">{activeAgentsCount}</div>
          <div className="metric-strip-sub" style={{ color: "#16745B", display: "flex", alignItems: "center", gap: "4px" }}>
            <TrendingUp size={12} /> +12.4% vs last period
          </div>
        </div>

        <div className="metric-strip-item">
          <span className="metric-strip-label">Active Workflows</span>
          <div className="metric-strip-value">{activeWorkflowsCount}</div>
          <div className="metric-strip-sub" style={{ color: "#16745B", display: "flex", alignItems: "center", gap: "4px" }}>
            <TrendingUp size={12} /> +8.2% vs last period
          </div>
        </div>

        <div className="metric-strip-item">
          <span className="metric-strip-label">RAG-Ready Knowledge</span>
          <div className="metric-strip-value">{indexedDocsCount}</div>
          <div className="metric-strip-sub">{documents.length} workspace documents</div>
        </div>

        <div className="metric-strip-item">
          <span className="metric-strip-label">System Uptime</span>
          <div className="metric-strip-value">99.99%</div>
          <div className="metric-strip-sub" style={{ color: "#16745B" }}>All core engines operational</div>
        </div>
      </div>

      {/* Intelligence Overview Chart + Platform Health */}
      <div className="dashboard-grid" style={{ marginTop: "24px" }}>
        {/* Intelligence Overview */}
        <section className="dashboard-card large-card" style={{ padding: "24px" }}>
          <div className="card-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
            <div className="orvex-rail-header">
              <div>
                <h2 style={{ fontSize: "18px", fontWeight: 700, margin: 0, color: "#171A19" }}>INTELLIGENCE & EXECUTION</h2>
                <p style={{ fontSize: "13px", color: "#59615D", margin: "4px 0 0 0" }}>
                  Automated operations across agents, workflows and knowledge.
                </p>
              </div>
            </div>

            <div style={{ display: "flex", gap: "6px" }}>
              {(["7d", "30d", "90d"] as TimeRange[]).map((r) => (
                <button
                  key={r}
                  type="button"
                  className={`secondary-button ${timeRange === r ? "active" : ""}`}
                  onClick={() => setTimeRange(r)}
                  style={{
                    padding: "4px 10px",
                    fontSize: "12px",
                    height: "30px",
                  }}
                >
                  {r.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "baseline", gap: "10px", marginBottom: "16px", paddingLeft: "15px" }}>
            <span style={{ fontSize: "32px", fontWeight: 700, color: "#171A19", letterSpacing: "-0.6px" }}>{summary.totalExecutions.toLocaleString()}</span>
            <span style={{ fontSize: "13px", fontWeight: 500, color: "#59615D" }}>Total automated operations</span>
          </div>

          <div className="analytics-chart">
            <div className="chart-y-axis">
              <span>{summary.totalExecutions.toLocaleString()}</span>
              <span>{Math.round(summary.totalExecutions * 0.75).toLocaleString()}</span>
              <span>{Math.round(summary.totalExecutions * 0.5).toLocaleString()}</span>
              <span>{Math.round(summary.totalExecutions * 0.25).toLocaleString()}</span>
              <span>0</span>
            </div>

            <div className="chart-area">
              <div className="chart-grid-lines">
                <span></span>
                <span></span>
                <span></span>
                <span></span>
                <span></span>
              </div>

              <svg className="chart-svg" viewBox="0 0 800 280" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="dashboardChartGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#0E6B63" stopOpacity="0.12" />
                    <stop offset="100%" stopColor="#0E6B63" stopOpacity="0" />
                  </linearGradient>
                </defs>

                <path
                  className="chart-fill"
                  style={{ fill: "url(#dashboardChartGrad)" }}
                  d="
                    M0 220
                    C70 205, 90 180, 140 190
                    C190 200, 220 150, 270 165
                    C320 180, 350 120, 400 135
                    C450 150, 480 95, 530 110
                    C580 125, 610 75, 660 95
                    C710 115, 750 60, 800 70
                    L800 280
                    L0 280
                    Z
                  "
                />

                <path
                  className="chart-line"
                  style={{ stroke: "#0E6B63", strokeWidth: "2.5px" }}
                  d="
                    M0 220
                    C70 205, 90 180, 140 190
                    C190 200, 220 150, 270 165
                    C320 180, 350 120, 400 135
                    C450 150, 480 95, 530 110
                    C580 125, 610 75, 660 95
                    C710 115, 750 60, 800 70
                  "
                />

                <circle cx="0" cy="220" r="4" fill="#0E6B63" />
                <circle cx="140" cy="190" r="4" fill="#0E6B63" />
                <circle cx="270" cy="165" r="4" fill="#0E6B63" />
                <circle cx="400" cy="135" r="4" fill="#0E6B63" />
                <circle cx="530" cy="110" r="4" fill="#0E6B63" />
                <circle cx="660" cy="95" r="4" fill="#0E6B63" />
                <circle cx="800" cy="70" r="4" fill="#0E6B63" />
              </svg>

              <div className="chart-labels">
                {trends.map((pt) => (
                  <span key={pt.date}>{pt.date}</span>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Platform Health Status Panel */}
        <section className="dashboard-card" style={{ padding: "24px", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div>
            <div className="card-header" style={{ marginBottom: "16px" }}>
              <div className="orvex-rail-header">
                <div>
                  <h2 style={{ fontSize: "18px", fontWeight: 700, margin: 0, color: "#171A19" }}>PLATFORM HEALTH</h2>
                  <p style={{ fontSize: "12px", color: "#59615D", margin: "4px 0 0 0", textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 600 }}>
                    CORE ENGINES
                  </p>
                </div>
              </div>
            </div>

            <div className="status-list" style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {systemStatus.map((service) => (
                <div
                  key={service.name}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "10px 14px",
                    borderRadius: "6px",
                    background: "#F5F3EE",
                    border: "1px solid #D9D7D0",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <span className="status-badge-dot" style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#16745B" }} />
                    <span style={{ fontSize: "13px", fontWeight: 600, color: "#171A19" }}>{service.name}</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ fontSize: "11px", color: "#8A918D" }}>{service.lat}</span>
                    <span style={{ fontSize: "11px", fontWeight: 600, color: "#16745B", padding: "2px 8px", borderRadius: "4px", background: "#E4F1EF" }}>
                      {service.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginTop: "16px", paddingTop: "12px", borderTop: "1px solid #D9D7D0", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: "11px", fontWeight: 700, color: "#16745B", letterSpacing: "0.06em" }}>● ALL SYSTEMS OPERATIONAL</span>
            <span style={{ fontSize: "11px", color: "#59615D" }}>99.99% platform availability</span>
          </div>
        </section>
      </div>

      {/* Recent Workspace Activity */}
      <section className="dashboard-card activity-card" style={{ marginTop: "24px", padding: "24px" }}>
        <div className="card-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
          <div className="orvex-rail-header">
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: 700, margin: 0, color: "#171A19" }}>RECENT WORKSPACE ACTIVITY</h2>
              <p style={{ fontSize: "13px", color: "#59615D", margin: "4px 0 0 0" }}>
                Live audit events across AI agents, workflows, and document ingestion.
              </p>
            </div>
          </div>

          <button
            className="secondary-button"
            type="button"
            onClick={() => navigate("/analytics")}
            style={{ fontSize: "12px", padding: "4px 10px", height: "32px" }}
          >
            View Full Audit Logs <ArrowRight size={14} />
          </button>
        </div>

        <div className="activity-list" style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {recentActivity.map((activity, idx) => {
            const ActivityIcon = activity.icon;
            return (
              <div
                className="activity-item"
                key={idx}
                onClick={() => navigate(activity.link)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "14px",
                  padding: "12px 14px",
                  borderRadius: "6px",
                  background: "#FFFFFF",
                  border: "1px solid #D9D7D0",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                <div style={{ width: "32px", height: "32px", borderRadius: "6px", background: "#E4F1EF", color: "#0E6B63", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <ActivityIcon size={16} />
                </div>

                <div style={{ flex: 1 }}>
                  <strong style={{ fontSize: "13px", color: "#171A19", display: "block" }}>{activity.message}</strong>
                  <span style={{ fontSize: "11px", color: "#8A918D" }}>{activity.time}</span>
                </div>

                <ArrowRight size={14} style={{ color: "#8A918D" }} />
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

export default Dashboard;
