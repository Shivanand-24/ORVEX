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

        <div>
          <h1>ORVEX</h1>
          <span>Enterprise Intelligence</span>
        </div>
      </div>

      <nav className="sidebar-navigation">
        {navigation.map((item) => {
          const Icon = item.icon;

          return (
            <button className="navigation-item" key={item.label}>
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <button className="navigation-item">
          <Settings size={18} />
          <span>Settings</span>
        </button>

        <div className="workspace">
          <div className="workspace-avatar">S</div>

          <div>
            <strong>Workspace</strong>
            <span>Enterprise</span>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;