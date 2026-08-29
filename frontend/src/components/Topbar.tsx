import {
  Bell,
  ChevronDown,
  Search,
  ShieldCheck,
} from "lucide-react";

function Topbar() {
  return (
    <header className="topbar">
      <div className="topbar-search">
        <Search size={18} strokeWidth={2} />

        <input
          type="text"
          placeholder="Search ORVEX..."
          aria-label="Search ORVEX"
        />

        <span className="search-shortcut">⌘ K</span>
      </div>

      <div className="topbar-actions">
        <div className="security-status">
          <ShieldCheck size={17} strokeWidth={2} />
          <span>Secure</span>
        </div>

        <button
          className="icon-button"
          type="button"
          aria-label="Notifications"
        >
          <Bell size={19} strokeWidth={2} />
        </button>

        <button
          className="profile-button"
          type="button"
          aria-label="Open profile menu"
        >
          <div className="profile-avatar">S</div>

          <div className="profile-info">
            <strong>Shivanand</strong>
            <span>Administrator</span>
          </div>

          <ChevronDown size={16} strokeWidth={2} />
        </button>
      </div>
    </header>
  );
}

export default Topbar;