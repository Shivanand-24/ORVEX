import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { LogOut, Settings, Shield, User, Building2 } from "lucide-react";
import { toastService } from "../../services/toastService";

type ProfileMenuProps = {
  isOpen: boolean;
  onClose: () => void;
};

function ProfileMenu({ isOpen, onClose }: ProfileMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleNavigateSettings = () => {
    navigate("/settings");
    onClose();
  };

  const handleSignOut = () => {
    toastService.show("Sign Out Executed", "Frontend demonstration mode (no active session).", "info");
    onClose();
  };

  return (
    <div className="profile-dropdown-menu" ref={menuRef} aria-label="Profile Menu">
      <div className="profile-menu-header">
        <div className="profile-menu-avatar">S</div>
        <div>
          <strong>Shivanand</strong>
          <span>shivanand@orvex.ai</span>
          <span className="profile-menu-badge">Administrator</span>
        </div>
      </div>

      <div className="profile-menu-section">
        <button className="profile-menu-item" type="button" onClick={handleNavigateSettings}>
          <User size={15} />
          <span>Account Profile</span>
        </button>

        <button className="profile-menu-item" type="button" onClick={handleNavigateSettings}>
          <Building2 size={15} />
          <span>Workspace Info</span>
        </button>

        <button className="profile-menu-item" type="button" onClick={handleNavigateSettings}>
          <Settings size={15} />
          <span>Platform Settings</span>
        </button>

        <button className="profile-menu-item" type="button" onClick={handleNavigateSettings}>
          <Shield size={15} />
          <span>Security & Compliance</span>
        </button>
      </div>

      <div className="profile-menu-footer">
        <button className="profile-menu-item sign-out" type="button" onClick={handleSignOut}>
          <LogOut size={15} />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  );
}

export default ProfileMenu;
