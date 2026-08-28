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
        <Search size={18} />

        <input
          type="text"
          placeholder="Search ORVEX..."
          aria-label="Search ORVEX"
        />

        <span className="search-shortcut">⌘ K</span>
      </div>

      <div className="topbar-actions">
        <div className="security-status">
          <ShieldCheck size={17} />
          <span>Secure</span>
        </div>

        <button
          className="icon-button"
          type="button"
          aria-label="Notifications"
        >
          <Bell size={19} />
        </button>

        <button className="profile-button" type="button">
          <div className="profile-avatar">S</div>

          <div className="profile-info">
            <strong>Shivanand</strong>
            <span>Administrator</span>
          </div>

          <ChevronDown size={16} />
        </button>
      </div>
    </header>
  );
}

export default Topbar;