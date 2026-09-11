import {
  BarChart3,
  Bot,
  Database,
  LayoutDashboard,
  Network,
  Settings,
  Workflow,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const navigation = [
  {
    label: "Overview",
    icon: LayoutDashboard,
    path: "/",
  },
  {
    label: "AI Assistant",
    icon: Bot,
    path: "/assistant",
  },
  {
    label: "Knowledge",
    icon: Database,
    path: "/knowledge",
  },
  {
    label: "Agents",
    icon: Network,
    path: "/agents",
  },
  {
    label: "Workflows",
    icon: Workflow,
    path: "/workflows",
  },
  {
    label: "Analytics",
    icon: BarChart3,
    path: "/analytics",
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
            <NavLink
              key={item.label}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                `navigation-item ${isActive ? "active" : ""}`
              }
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `navigation-item ${isActive ? "active" : ""}`
          }
        >
          <Settings size={18} />
          <span>Settings</span>
        </NavLink>

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
