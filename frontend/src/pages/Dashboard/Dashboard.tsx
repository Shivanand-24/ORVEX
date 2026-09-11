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

  const stats = [
    {
      label: "Active Agents",
      value: activeAgentsCount.toString(),
      change: `${agents.length} total in roster`,
      icon: Bot,
    },
    {
      label: "Active Workflows",
      value: activeWorkflowsCount.toString(),
      change: `${workflows.length} total configured`,
      icon: Workflow,
    },
    {
      label: "RAG-Ready Knowledge",
      value: indexedDocsCount.toString(),
      change: `${documents.length} workspace documents`,
      icon: Database,
    },
    {
      label: "System Uptime",
      value: "99.99%",
      change: "All core engines online",
      icon: CheckCircle2,
    },
  ];

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
          <p>Good morning, Shivanand. Here's what's happening across ORVEX.</p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <button
            className="secondary-button"
            type="button"
            onClick={() => navigate("/assistant")}
          >
            <Sparkles size={16} /> Ask Assistant
          </button>
          <button
            className="primary-button"
            type="button"
            onClick={() => navigate("/create-workflow")}
          >
            <Plus size={16} /> Create Workflow
          </button>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="stats-grid">
        {stats.map((stat) => {
          const StatIcon = stat.icon;
          return (
            <div className="stat-card" key={stat.label}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span>{stat.label}</span>
                <StatIcon size={18} style={{ color: "var(--orvex-accent-hover)" }} />
              </div>
              <strong>{stat.value}</strong>
              <small>{stat.change}</small>
            </div>
          );
        })}
      </div>

      {/* Intelligence Overview Chart + System Status */}
      <div className="dashboard-grid">
        {/* Intelligence Overview */}
        <section className="dashboard-card large-card">
          <div className="card-header">
            <div>
              <h2>Intelligence & Execution Overview</h2>
              <p>Total automated operations across Agents, Workflows, and Knowledge queries.</p>
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
                    background: timeRange === r ? "var(--orvex-surface-2)" : "transparent",
                    borderColor: timeRange === r ? "var(--orvex-accent)" : "transparent",
                  }}
                >
                  {r.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div className="analytics-chart">
            <div className="chart-y-axis">
              <span>{summary.totalExecutions}</span>
              <span>{Math.round(summary.totalExecutions * 0.75)}</span>
              <span>{Math.round(summary.totalExecutions * 0.5)}</span>
              <span>{Math.round(summary.totalExecutions * 0.25)}</span>
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
                  <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.35" />
                    <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0" />
                  </linearGradient>
                </defs>

                <path
                  className="chart-fill"
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

                <circle cx="0" cy="220" r="5" />
                <circle cx="140" cy="190" r="5" />
                <circle cx="270" cy="165" r="5" />
                <circle cx="400" cy="135" r="5" />
                <circle cx="530" cy="110" r="5" />
                <circle cx="660" cy="95" r="5" />
                <circle cx="800" cy="70" r="5" />
              </svg>

              <div className="chart-labels">
                {trends.map((pt) => (
                  <span key={pt.date}>{pt.date}</span>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* System Status */}
        <section className="dashboard-card">
          <div className="card-header">
            <div>
              <h2>System Status</h2>
              <p>Real-time platform engine health</p>
            </div>
          </div>

          <div className="status-list">
            {systemStatus.map((service) => (
              <div key={service.name} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 0", borderBottom: "1px solid var(--orvex-border)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span className="status-dot online"></span>
                  <span style={{ fontSize: "13px", fontWeight: 500 }}>{service.name}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "11px", color: "var(--orvex-text-muted)" }}>{service.lat}</span>
                  <strong style={{ fontSize: "12px", color: "#22c55e" }}>{service.status}</strong>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Recent Activity */}
      <section className="dashboard-card activity-card" style={{ marginTop: "24px" }}>
        <div className="card-header">
          <div>
            <h2>Recent Workspace Activity</h2>
            <p>Live events across AI agents, workflows, and document ingestion.</p>
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

        <div className="activity-list">
          {recentActivity.map((activity, idx) => {
            const ActivityIcon = activity.icon;
            return (
              <div
                className="activity-item"
                key={idx}
                onClick={() => navigate(activity.link)}
                style={{ cursor: "pointer" }}
              >
                <div className="activity-icon">
                  <ActivityIcon size={16} />
                </div>

                <div style={{ flex: 1 }}>
                  <strong>{activity.message}</strong>
                  <span>{activity.time}</span>
                </div>

                <ArrowRight size={14} style={{ color: "var(--orvex-text-muted)" }} />
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

export default Dashboard;
