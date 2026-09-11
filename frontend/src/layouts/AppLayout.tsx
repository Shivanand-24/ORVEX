import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";
import Toast from "../components/common/Toast";

function AppLayout() {
  return (
    <div className="app-shell">
      <Sidebar />

      <div className="app-content">
        <Topbar />

        <main className="page-content">
          <Outlet />
        </main>
      </div>

      <Toast />
    </div>
  );
}

export default AppLayout;