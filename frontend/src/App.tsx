import { Suspense, lazy } from "react";
import { Routes, Route, Navigate } from "react-router-dom";

import { AppLayout } from "./components/layout/AppLayout";
import { ErrorBoundary } from "./components/common/ErrorBoundary";
import { OfflineBanner } from "./components/common/OfflineBanner";
import { SkeletonPage } from "./components/common/SkeletonPage";

const HomePage = lazy(() => import("./pages/HomePage"));
const TriagePage = lazy(() => import("./pages/TriagePage"));
const FacilitiesPage = lazy(() => import("./pages/FacilitiesPage"));
const AdminPage = lazy(() => import("./pages/AdminPage"));
const NotFoundPage = lazy(() => import("./pages/NotFoundPage"));

function App() {
  return (
    <ErrorBoundary>
      <OfflineBanner />
      <Routes>
        <Route element={<AppLayout />}>
          <Route
            index
            element={
              <Suspense fallback={<SkeletonPage />}>
                <HomePage />
              </Suspense>
            }
          />
          <Route
            path="triage"
            element={
              <Suspense fallback={<SkeletonPage />}>
                <TriagePage />
              </Suspense>
            }
          />
          <Route
            path="facilities"
            element={
              <Suspense fallback={<SkeletonPage />}>
                <FacilitiesPage />
              </Suspense>
            }
          />
          <Route
            path="admin"
            element={
              <Suspense fallback={<SkeletonPage />}>
                <AdminPage />
              </Suspense>
            }
          />
          <Route path="404" element={<NotFoundPage />} />
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
}

export default App;
