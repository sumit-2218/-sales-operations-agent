import { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Spinner } from "./components/ui";
import { useAuth } from "./hooks/useAuth";
import AppLayout from "./layouts/AppLayout";
import AdminOverview from "./pages/AdminOverview";
import AdminSystem from "./pages/AdminSystem";
import AdminUsers from "./pages/AdminUsers";
import DashboardPage from "./pages/DashboardPage";
import FollowUpsPage from "./pages/FollowUpsPage";
import IcpPage from "./pages/IcpPage";
import ImportPage from "./pages/ImportPage";
import LeadDetailPage from "./pages/LeadDetailPage";
import LeadFormPage from "./pages/LeadFormPage";
import LeadsPage from "./pages/LeadsPage";
import LoginPage from "./pages/LoginPage";
import ProfilePage from "./pages/ProfilePage";
import RegisterPage from "./pages/RegisterPage";
import type { Role } from "./types";

function Protected({ roles, children }: { roles?: Role[]; children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <Spinner />;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<Protected><AppLayout /></Protected>}>
        <Route index element={<DashboardPage />} />
        <Route path="leads" element={<LeadsPage />} />
        <Route path="leads/new" element={<LeadFormPage />} />
        <Route path="leads/:id" element={<LeadDetailPage />} />
        <Route path="leads/:id/edit" element={<LeadFormPage />} />
        <Route path="import" element={<ImportPage />} />
        <Route path="icp" element={<IcpPage />} />
        <Route path="follow-ups" element={<FollowUpsPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="admin" element={<Protected roles={["admin"]}><AdminOverview /></Protected>} />
        <Route path="admin/users" element={<Protected roles={["admin"]}><AdminUsers /></Protected>} />
        <Route path="admin/system" element={<Protected roles={["admin"]}><AdminSystem /></Protected>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
