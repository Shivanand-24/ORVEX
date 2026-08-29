import {
  BarChart3,
  Bot,
  Database,
  LayoutDashboard,
  Network,
  Settings,
  Workflow,
} from "lucide-react";

const navigation = [
  {
    label: "Overview",
    icon: LayoutDashboard,
  },
  {
    label: "AI Assistant",
    icon: Bot,
  },
  {
    label: "Knowledge",
    icon: Database,
  },
  {
    label: "Agents",
    icon: Network,
  },
  {
    label: "Workflows",
    icon: Workflow,
  },
  {
    label: "Analytics",
    icon: BarChart3,
  },
];

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-mark">O</div>

        <div className="brand-content">
          <h1>ORVEX</h1>
          <span>Enterprise Intelligence</span>
        </div>
      </div>

      <nav className="sidebar-navigation">
        {navigation.map((item) => {
          const Icon = item.icon;

          return (
            <button
              className="navigation-item"
              key={item.label}
              type="button"
            >
              <Icon size={19} strokeWidth={1.8} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <button
          className="navigation-item settings-item"
          type="button"
        >
          <Settings size={19} strokeWidth={1.8} />
          <span>Settings</span>
        </button>

        <div className="workspace">
          <div className="workspace-avatar">S</div>

          <div className="workspace-info">
            <strong>Workspace</strong>
            <span>Enterprise</span>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;