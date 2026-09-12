import {
  BarChart3,
  Bot,
  ChevronDown,
  Database,
  LayoutDashboard,
  Network,
  Settings,
  Sparkles,
  Workflow,
} from "lucide-react";
import { NavLink } from "react-router-dom";

type NavItem = {
  label: string;
  icon: typeof LayoutDashboard;
  path: string;
  badge?: string;
};

type NavGroup = {
  title: string;
  items: NavItem[];
};

const navigationGroups: NavGroup[] = [
  {
    title: "WORKSPACE",
    items: [
      {
        label: "Overview",
        icon: LayoutDashboard,
        path: "/",
      },
      {
        label: "AI Assistant",
        icon: Bot,
        path: "/assistant",
        badge: "Copilot",
      },
      {
        label: "Knowledge",
        icon: Database,
        path: "/knowledge",
      },
    ],
  },
  {
    title: "AUTOMATION",
    items: [
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
    ],
  },
  {
    title: "INSIGHTS",
    items: [
      {
        label: "Analytics",
        icon: BarChart3,
        path: "/analytics",
      },
    ],
  },
  {
    title: "SYSTEM",
    items: [
      {
        label: "Settings",
        icon: Settings,
        path: "/settings",
      },
    ],
  },
];

function Sidebar() {
  return (
    <aside className="sidebar">
      {/* Premium Brand Area */}
      <div className="sidebar-brand">
        <div className="brand-mark">
          <Sparkles size={20} />
        </div>

        <div className="brand-content">
          <h1>ORVEX</h1>
          <span>Enterprise Intelligence</span>
        </div>
      </div>

      {/* Grouped Navigation */}
      <nav className="sidebar-navigation">
        {navigationGroups.map((group) => (
          <div key={group.title} className="navigation-group">
            <span className="group-title">{group.title}</span>

            <div className="group-items">
              {group.items.map((item) => {
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
                    <span className="active-indicator" />
                    <Icon size={18} className="item-icon" />
                    <span className="item-label">{item.label}</span>
                    {item.badge && <span className="item-badge">{item.badge}</span>}
                  </NavLink>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Sidebar Footer — Workspace Switcher */}
      <div className="sidebar-footer">
        <div className="workspace" role="button" tabIndex={0}>
          <div className="workspace-avatar">E</div>

          <div className="workspace-info">
            <strong>Enterprise Workspace</strong>
            <span>Production Tier</span>
          </div>

          <ChevronDown size={14} className="workspace-chevron" />
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
