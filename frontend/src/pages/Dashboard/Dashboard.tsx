function Dashboard() {
  return (
    <div className="dashboard-page">
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p>Good morning, Shivanand. Here's what's happening in ORVEX.</p>
        </div>

        <button className="primary-button">
          + Create Workflow
        </button>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <span>Active Agents</span>
          <strong>12</strong>
          <small>+12.5% from last month</small>
        </div>

        <div className="stat-card">
          <span>Workflows</span>
          <strong>28</strong>
          <small>+8.2% from last month</small>
        </div>

        <div className="stat-card">
          <span>Knowledge Items</span>
          <strong>1,284</strong>
          <small>+18.4% from last month</small>
        </div>

        <div className="stat-card">
          <span>System Uptime</span>
          <strong>99.9%</strong>
          <small>All systems operational</small>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Intelligence Overview */}
        <section className="dashboard-card large-card">
          <div className="card-header">
            <div>
              <h2>Intelligence Overview</h2>
              <p>ORVEX activity across your workspace</p>
            </div>
          </div>

          <div className="analytics-chart">
            <div className="chart-y-axis">
              <span>100</span>
              <span>75</span>
              <span>50</span>
              <span>25</span>
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

              <svg
                className="chart-svg"
                viewBox="0 0 800 280"
                preserveAspectRatio="none"
              >
                <defs>
                  <linearGradient
                    id="chartGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop
                      offset="0%"
                      stopColor="#8b5cf6"
                      stopOpacity="0.3"
                    />
                    <stop
                      offset="100%"
                      stopColor="#8b5cf6"
                      stopOpacity="0"
                    />
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
                <span>Mon</span>
                <span>Tue</span>
                <span>Wed</span>
                <span>Thu</span>
                <span>Fri</span>
                <span>Sat</span>
                <span>Sun</span>
              </div>
            </div>
          </div>
        </section>

        {/* System Status */}
        <section className="dashboard-card">
          <div className="card-header">
            <div>
              <h2>System Status</h2>
              <p>Current platform health</p>
            </div>
          </div>

          <div className="status-list">
            <div>
              <span className="status-dot online"></span>
              <span>AI Services</span>
              <strong>Online</strong>
            </div>

            <div>
              <span className="status-dot online"></span>
              <span>Knowledge Engine</span>
              <strong>Online</strong>
            </div>

            <div>
              <span className="status-dot online"></span>
              <span>Workflow Engine</span>
              <strong>Online</strong>
            </div>

            <div>
              <span className="status-dot online"></span>
              <span>Database</span>
              <strong>Online</strong>
            </div>
          </div>
        </section>
      </div>

      {/* Recent Activity */}
      <section className="dashboard-card activity-card">
        <div className="card-header">
          <div>
            <h2>Recent Activity</h2>
            <p>Latest events in your workspace</p>
          </div>
        </div>

        <div className="activity-list">
          <div className="activity-item">
            <div className="activity-icon">AI</div>

            <div>
              <strong>AI Assistant processed a request</strong>
              <span>2 minutes ago</span>
            </div>
          </div>

          <div className="activity-item">
            <div className="activity-icon">WF</div>

            <div>
              <strong>Workflow "Data Sync" completed</strong>
              <span>18 minutes ago</span>
            </div>
          </div>

          <div className="activity-item">
            <div className="activity-icon">AG</div>

            <div>
              <strong>Agent "Research Bot" executed</strong>
              <span>42 minutes ago</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Dashboard;