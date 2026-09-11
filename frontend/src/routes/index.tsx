import { createBrowserRouter } from "react-router-dom";

import AppLayout from "../layouts/AppLayout";

import Dashboard from "../pages/Dashboard/Dashboard";
import Assistant from "../pages/Assistant/Assistant";
import Agents from "../pages/Agents/Agents";
import Analytics from "../pages/Analytics/Analytics";
import Knowledge from "../pages/Knowledge/Knowledge";
import Workflows from "../pages/Workflows/Workflows";
import CreateWorkflow from "../pages/Workflows/CreateWorkflow";
import Settings from "../pages/Settings/Settings";
import NotFound from "../pages/NotFound/NotFound";
import RouteError from "../pages/RouteError/RouteError";

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    errorElement: <RouteError />,
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
      {
        path: "create-workflow",
        element: <CreateWorkflow />,
      },
      {
        path: "settings",
        element: <Settings />,
      },
      {
        path: "*",
        element: <NotFound />,
      },
    ],
  },
]);

export default router;
