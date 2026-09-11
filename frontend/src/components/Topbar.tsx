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
      <div
        className="topbar-search"
        onClick={() => setIsSearchOpen(true)}
        role="button"
        tabIndex={0}
        aria-label="Open search dialog"
      >
        <Search size={18} strokeWidth={2} />

        <input
          type="text"
          placeholder="Search ORVEX across docs, agents, workflows..."
          aria-label="Search ORVEX"
          readOnly
        />

        <span className="search-shortcut">⌘ K</span>
      </div>

      <div className="topbar-actions" style={{ position: "relative" }}>
        <div className="security-status">
          <ShieldCheck size={17} strokeWidth={2} />
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
          <Bell size={19} strokeWidth={2} />
          {unreadCount > 0 && (
            <span
              style={{
                position: "absolute",
                top: "4px",
                right: "4px",
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                background: "var(--orvex-accent)",
              }}
            />
          )}
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

          <ChevronDown size={16} strokeWidth={2} />
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
