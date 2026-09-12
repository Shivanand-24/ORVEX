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

  const stats = [
    {
      label: "Active Agents",
      value: activeAgentsCount.toString(),
      change: "+12.4% vs last period",
      icon: Bot,
      trend: "up",
    },
    {
      label: "Active Workflows",
      value: activeWorkflowsCount.toString(),
      change: "+8.2% vs last period",
      icon: Workflow,
      trend: "up",
    },
    {
      label: "RAG-Ready Knowledge",
      value: indexedDocsCount.toString(),
      change: `${documents.length} workspace documents`,
      icon: Database,
      trend: "neutral",
    },
    {
      label: "System Uptime",
      value: "99.99%",
      change: "All core engines operational",
      icon: CheckCircle2,
      trend: "good",
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
          <p>Good morning, Shivanand. Welcome to ORVEX Enterprise Intelligence Control.</p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <button
            className="secondary-button"
            type="button"
            onClick={() => navigate("/assistant")}
          >
            <Sparkles size={15} style={{ color: "#3157d5" }} /> Ask Assistant
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

      {/* KPI Stat Cards */}
      <div className="stats-grid">
        {stats.map((stat) => {
          const StatIcon = stat.icon;
          return (
            <div className="stat-card" key={stat.label}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span>{stat.label}</span>
                <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "#e8edff", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <StatIcon size={16} style={{ color: "#3157d5" }} />
                </div>
              </div>
              <strong>{stat.value}</strong>
              <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                {stat.trend === "up" && <TrendingUp size={12} style={{ color: "#16845b" }} />}
                <small>{stat.change}</small>
              </div>
            </div>
          );
        })}
      </div>

      {/* Intelligence Overview Chart + System Status */}
      <div className="dashboard-grid" style={{ marginTop: "24px" }}>
        {/* Intelligence Overview */}
        <section className="dashboard-card large-card" style={{ padding: "24px" }}>
          <div className="card-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: 700, margin: 0 }}>Intelligence & Execution Overview</h2>
              <p style={{ fontSize: "13px", color: "#596273", margin: "4px 0 0 0" }}>
                Total automated operations across Agents, Workflows, and Knowledge queries.
              </p>
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
                    <stop offset="0%" stopColor="#3157d5" stopOpacity="0.18" />
                    <stop offset="100%" stopColor="#3157d5" stopOpacity="0" />
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
                  style={{ stroke: "#3157d5", strokeWidth: "2.5px" }}
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

                <circle cx="0" cy="220" r="4" fill="#3157d5" />
                <circle cx="140" cy="190" r="4" fill="#3157d5" />
                <circle cx="270" cy="165" r="4" fill="#3157d5" />
                <circle cx="400" cy="135" r="4" fill="#3157d5" />
                <circle cx="530" cy="110" r="4" fill="#3157d5" />
                <circle cx="660" cy="95" r="4" fill="#3157d5" />
                <circle cx="800" cy="70" r="4" fill="#3157d5" />
              </svg>

              <div className="chart-labels">
                {trends.map((pt) => (
                  <span key={pt.date}>{pt.date}</span>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* System Engine Status */}
        <section className="dashboard-card" style={{ padding: "24px" }}>
          <div className="card-header" style={{ marginBottom: "16px" }}>
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: 700, margin: 0 }}>System Engine Status</h2>
              <p style={{ fontSize: "13px", color: "#596273", margin: "4px 0 0 0" }}>
                Real-time health of core platform microservices
              </p>
            </div>
          </div>

          <div className="status-list" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {systemStatus.map((service) => (
              <div
                key={service.name}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "12px",
                  borderRadius: "8px",
                  background: "#f6f7f9",
                  border: "1px solid #dde1e7",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span className="status-badge-dot" style={{ background: "#16845b" }} />
                  <span style={{ fontSize: "13px", fontWeight: 600, color: "#111827" }}>{service.name}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "11px", color: "#8992a3" }}>{service.lat}</span>
                  <span style={{ fontSize: "11px", fontWeight: 600, color: "#16845b", padding: "2px 8px", borderRadius: "4px", background: "#e8f5ef" }}>
                    {service.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Recent Workspace Activity */}
      <section className="dashboard-card activity-card" style={{ marginTop: "24px", padding: "24px" }}>
        <div className="card-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
          <div>
            <h2 style={{ fontSize: "18px", fontWeight: 700, margin: 0 }}>Recent Workspace Activity</h2>
            <p style={{ fontSize: "13px", color: "#596273", margin: "4px 0 0 0" }}>
              Live audit events across AI agents, workflows, and document ingestion.
            </p>
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
                  borderRadius: "8px",
                  background: "#f6f7f9",
                  border: "1px solid #dde1e7",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "#e8edff", color: "#3157d5", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <ActivityIcon size={16} />
                </div>

                <div style={{ flex: 1 }}>
                  <strong style={{ fontSize: "13px", color: "#111827", display: "block" }}>{activity.message}</strong>
                  <span style={{ fontSize: "11px", color: "#8992a3" }}>{activity.time}</span>
                </div>

                <ArrowRight size={14} style={{ color: "#8992a3" }} />
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

export default Dashboard;
