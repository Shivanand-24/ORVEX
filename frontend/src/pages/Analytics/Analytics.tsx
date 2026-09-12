import { useEffect, useState } from "react";
import {
  Activity,
  CheckCircle2,
  Clock,
  Database,
} from "lucide-react";
import StatusBadge from "../../components/common/StatusBadge";
import { agentRepository } from "../../services/agentRepository";
import { analyticsRepository, type TimeRange } from "../../services/analyticsRepository";

function Analytics() {
  const [timeRange, setTimeRange] = useState<TimeRange>("30d");

  const [summary, setSummary] = useState(() => analyticsRepository.getSummary(timeRange));
  const [trends, setTrends] = useState(() => analyticsRepository.getTrends(timeRange));
  const [agents, setAgents] = useState(() => agentRepository.list());

  useEffect(() => {
    return analyticsRepository.subscribe(() => {
      setSummary(analyticsRepository.getSummary(timeRange));
      setTrends(analyticsRepository.getTrends(timeRange));
      setAgents(agentRepository.list());
    });
  }, [timeRange]);

  const recentAuditLogs = [
    {
      id: "exec-101",
      name: "Research Agent",
      type: "Agent Run",
      target: "Employee Handbook 2026",
      status: "Completed",
      duration: "320ms",
      timestamp: "2 mins ago",
    },
    {
      id: "exec-102",
      name: "Employee Data Sync",
      type: "Workflow Run",
      target: "Directory DB",
      status: "Completed",
      duration: "1,240ms",
      timestamp: "18 mins ago",
    },
    {
      id: "exec-103",
      name: "HR Intelligence Agent",
      type: "Agent Run",
      target: "Remote Work Policy",
      status: "Completed",
      duration: "410ms",
      timestamp: "28 mins ago",
    },
    {
      id: "exec-104",
      name: "Operations Agent",
      type: "Agent Run",
      target: "System Diagnostics",
      status: "Completed",
      duration: "580ms",
      timestamp: "1 hour ago",
    },
    {
      id: "exec-105",
      name: "Security Review Agent",
      type: "Agent Run",
      target: "Compliance Scan",
      status: "Completed",
      duration: "890ms",
      timestamp: "3 hours ago",
    },
  ];

  return (
    <div className="analytics-page">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1>Analytics & Operations</h1>
          <p>Monitor platform performance metrics, execution trends, and system reliability.</p>
        </div>

        <div style={{ display: "flex", gap: "6px" }}>
          {(["7d", "30d", "90d"] as TimeRange[]).map((r) => (
            <button
              key={r}
              type="button"
              className={`secondary-button ${timeRange === r ? "active" : ""}`}
              onClick={() => setTimeRange(r)}
              style={{
                padding: "6px 12px",
                fontSize: "13px",
                background: timeRange === r ? "var(--orvex-surface-2)" : "transparent",
                borderColor: timeRange === r ? "var(--orvex-accent)" : "var(--orvex-border)",
              }}
            >
              {r.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span>Total AI Executions</span>
            <Activity size={18} style={{ color: "#3157d5" }} />
          </div>
          <strong>{summary.totalExecutions.toLocaleString()}</strong>
          <small>{summary.successRate} overall success rate</small>
        </div>

        <div className="stat-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span>Successful Runs</span>
            <CheckCircle2 size={18} style={{ color: "#16845b" }} />
          </div>
          <strong>{summary.successfulExecutions.toLocaleString()}</strong>
          <small>{summary.failedExecutions} failed executions</small>
        </div>

        <div className="stat-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span>Avg Response Latency</span>
            <Clock size={18} style={{ color: "#b7791f" }} />
          </div>
          <strong>{summary.avgLatencyMs} ms</strong>
          <small>Sub-second execution target</small>
        </div>

        <div className="stat-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span>RAG Knowledge Queries</span>
            <Database size={18} style={{ color: "#3157d5" }} />
          </div>
          <strong>{summary.ragReadyDocuments * 140}</strong>
          <small>Across {summary.ragReadyDocuments} indexed documents</small>
        </div>
      </div>

      {/* Charts Section */}
      <div className="dashboard-grid" style={{ marginTop: "24px" }}>
        {/* Execution Trend Line Chart */}
        <section className="dashboard-card large-card">
          <div className="card-header">
            <div>
              <h2>Execution Volume Trend</h2>
              <p>Automated execution volume over time ({timeRange.toUpperCase()})</p>
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
                  <linearGradient id="analyticsGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3157d5" stopOpacity="0.2" />
                    <stop offset="100%" stopColor="#3157d5" stopOpacity="0" />
                  </linearGradient>
                </defs>

                <path
                  className="chart-fill"
                  style={{ fill: "url(#analyticsGrad)" }}
                  d="
                    M0 200
                    C100 180, 150 140, 250 160
                    C350 180, 400 100, 500 120
                    C600 140, 650 70, 800 80
                    L800 280
                    L0 280
                    Z
                  "
                />

                <path
                  className="chart-line"
                  style={{ stroke: "#3157d5", strokeWidth: "2.5px" }}
                  d="
                    M0 200
                    C100 180, 150 140, 250 160
                    C350 180, 400 100, 500 120
                    C600 140, 650 70, 800 80
                  "
                />

                <circle cx="0" cy="200" r="5" fill="#3157d5" />
                <circle cx="250" cy="160" r="5" fill="#3157d5" />
                <circle cx="500" cy="120" r="5" fill="#3157d5" />
                <circle cx="800" cy="80" r="5" fill="#3157d5" />
              </svg>

              <div className="chart-labels">
                {trends.map((pt) => (
                  <span key={pt.date}>{pt.date}</span>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Agent Performance Breakdown */}
        <section className="dashboard-card">
          <div className="card-header">
            <div>
              <h2>Agent Execution Leaderboard</h2>
              <p>Top executing digital workers</p>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "14px", marginTop: "12px" }}>
            {agents.map((ag) => (
              <div key={ag.id} style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                  <span style={{ fontWeight: 600, color: "#111827" }}>{ag.name}</span>
                  <span style={{ color: "#596273" }}>{ag.executions} runs ({ag.successRate})</span>
                </div>
                <div style={{ width: "100%", height: "8px", borderRadius: "999px", background: "#f0f2f5", overflow: "hidden" }}>
                  <div
                    style={{
                      width: `${Math.min(100, (ag.executions / 250) * 100)}%`,
                      height: "100%",
                      background: "#3157d5",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Execution Audit Log Table */}
      <section className="dashboard-card" style={{ marginTop: "24px" }}>
        <div className="card-header">
          <div>
            <h2>Recent Execution Audit Logs</h2>
            <p>Detailed log records of recent agent and workflow execution runs.</p>
          </div>
        </div>

        <div className="knowledge-table-scroll">
          <table className="knowledge-table">
            <thead>
              <tr>
                <th scope="col">Execution ID</th>
                <th scope="col">Name</th>
                <th scope="col">Type</th>
                <th scope="col">Target Artifact</th>
                <th scope="col">Status</th>
                <th scope="col">Duration</th>
                <th scope="col">Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {recentAuditLogs.map((log) => (
                <tr key={log.id}>
                  <td>
                    <code style={{ fontSize: "12px", color: "#3157d5", fontWeight: 600 }}>{log.id}</code>
                  </td>
                  <td>
                    <strong>{log.name}</strong>
                  </td>
                  <td>{log.type}</td>
                  <td>{log.target}</td>
                  <td>
                    <StatusBadge status={log.status} />
                  </td>
                  <td>{log.duration}</td>
                  <td>{log.timestamp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default Analytics;