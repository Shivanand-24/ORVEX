import { createBrowserRouter } from "react-router-dom";

import AppLayout from "../layouts/AppLayout";

import Dashboard from "../pages/Dashboard/Dashboard";
import Assistant from "../pages/Assistant/Assistant";
import Agents from "../pages/Agents/Agents";
import Analytics from "../pages/Analytics/Analytics";
import Knowledge from "../pages/Knowledge/Knowledge";
import Workflows from "../pages/Workflows/Workflows";

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: "assistant",
        element: <Assistant />,
      },
      {
        path: "agents",
        element: <Agents />,
      },
      {
        path: "analytics",
        element: <Analytics />,
      },
      {
        path: "knowledge",
        element: <Knowledge />,
      },
      {
        path: "workflows",
        element: <Workflows />,
      },
    ],
  },
]);

export default router;