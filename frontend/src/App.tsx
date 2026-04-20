import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AppLayout } from "./components/AppLayout";
import LoginPage from "./pages/LoginPage";
import AccesoDenegadoPage from "./pages/AccesoDenegadoPage";
import ImportarPage from "./pages/ImportarPage";
import ConsultarPage from "./pages/ConsultarPage";
import BulkSearchPage from "./pages/BulkSearchPage";
import CasosPage from "./pages/CasosPage";
import CasoDetailPage from "./pages/CasoDetailPage";
import ConfiguracionPage from "./pages/ConfiguracionPage";
import NoEncontradosPage from "./pages/NoEncontradosPage";
import ProjectDashboardPage from "./pages/ProjectDashboardPage";
import AgendaView from "./pages/AgendaView";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <ThemeProvider>
        <Sonner />
        <Toaster />
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              {/* Rutas públicas */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/acceso-denegado" element={<AccesoDenegadoPage />} />
              
              {/* Rutas protegidas */}
              <Route element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }>
                <Route path="/" element={<Navigate to="/consultar" replace />} />
                <Route path="/importar" element={<ImportarPage />} />
                <Route path="/consultar" element={<ConsultarPage />} />
                <Route path="/consultar-nombre" element={<BulkSearchPage />} />
                <Route path="/casos" element={<CasosPage />} />
                <Route path="/casos/:radicado" element={<CasoDetailPage />} />
                <Route path="/casos/id/:id" element={<CasoDetailPage />} />
                <Route path="/proyectos" element={<ProjectDashboardPage />} />
                <Route path="/agenda" element={<AgendaView />} />
                <Route path="/no-encontrados" element={<NoEncontradosPage />} />
                <Route path="/configuracion" element={
                  <ProtectedRoute requiredPermission="importar">
                    <ConfiguracionPage />
                  </ProtectedRoute>
                } />
              </Route>
              
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
