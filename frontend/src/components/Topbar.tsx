import { useEffect, useState } from "react";
import { Bell, ChevronDown, Search, ShieldCheck } from "lucide-react";
import GlobalSearchModal from "./common/GlobalSearchModal";
import NotificationPanel from "./common/NotificationPanel";
import ProfileMenu from "./common/ProfileMenu";
import { notificationService } from "../services/notificationService";

function Topbar() {
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(() =>
    notificationService.getUnreadCount()
  );

  useEffect(() => {
    return notificationService.subscribe(() => {
      setUnreadCount(notificationService.getUnreadCount());
    });
  }, []);

  return (
    <header className="topbar">
      {/* Global Command Search Bar */}
      <div
        className="topbar-search"
        onClick={() => setIsSearchOpen(true)}
        role="button"
        tabIndex={0}
        aria-label="Open command palette search dialog"
      >
        <Search size={16} className="topbar-search-icon" />

        <input
          type="text"
          placeholder="Search ORVEX across docs, agents, workflows..."
          aria-label="Search ORVEX"
          readOnly
        />

        <span className="search-shortcut">⌘ K</span>
      </div>

      {/* Topbar Right Actions */}
      <div className="topbar-actions" style={{ position: "relative" }}>
        {/* Security Indicator Pill */}
        <div
          className="security-status"
          title="Workspace security status: Encrypted & compliant"
        >
          <ShieldCheck size={15} strokeWidth={2} />
          <span>Secure Workspace</span>
        </div>

        {/* Notifications Button */}
        <button
          className="icon-button"
          type="button"
          aria-label="Notifications"
          onClick={() => {
            setIsNotificationsOpen((prev) => !prev);
            setIsProfileOpen(false);
          }}
          title="Toggle Notifications"
          style={{ position: "relative" }}
        >
          <Bell size={18} strokeWidth={2} />
          {unreadCount > 0 && <span className="notification-dot-badge" />}
        </button>

        {/* Profile Button */}
        <button
          className="profile-button"
          type="button"
          aria-label="Open profile menu"
          onClick={() => {
            setIsProfileOpen((prev) => !prev);
            setIsNotificationsOpen(false);
          }}
        >
          <div className="profile-avatar">S</div>

          <div className="profile-info">
            <strong>Shivanand</strong>
            <span>Administrator</span>
          </div>

          <ChevronDown size={14} strokeWidth={2} className="profile-chevron" />
        </button>

        {/* Popovers */}
        <NotificationPanel
          isOpen={isNotificationsOpen}
          onClose={() => setIsNotificationsOpen(false)}
        />
        <ProfileMenu
          isOpen={isProfileOpen}
          onClose={() => setIsProfileOpen(false)}
        />
      </div>

      {/* Global Search Modal */}
      <GlobalSearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
      />
    </header>
  );
}

export default Topbar;
