import { useState } from "react";
import { Upload, Search, FolderOpen, Scale, Settings, AlertTriangle, ChevronLeft, ChevronRight, LayoutDashboard, Calendar, UserCheck, Clock, type LucideIcon } from "lucide-react";
import { SidebarNavLink } from "./SidebarNavLink";
import { UserMenu } from "./UserMenu";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { Sun, Moon } from "lucide-react";
import { Switch } from "@/components/ui/switch";

export function AppSidebar() {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [collapsed, setCollapsed] = useState(false);

  const isAdmin = user?.is_admin === true;

  return (
    <aside
      className={`${collapsed ? "w-16" : "w-64"} min-h-screen bg-sidebar border-r border-sidebar-border flex flex-col transition-all duration-300 ease-in-out relative`}
    >
      {/* Toggle Button */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-6 z-50 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center shadow-md hover:scale-110 transition-transform"
        title={collapsed ? "Expandir menú" : "Colapsar menú"}
      >
        {collapsed ? <ChevronRight className="h-3.5 w-3.5" /> : <ChevronLeft className="h-3.5 w-3.5" />}
      </button>

      {/* Logo */}
      <div className={`border-b border-sidebar-border ${collapsed ? "p-3" : "p-6"} transition-all duration-300`}>
        <div className={`flex items-center ${collapsed ? "justify-center" : "gap-3"}`}>
          <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
            <Scale className="h-6 w-6 text-primary" />
          </div>
          {!collapsed && (
            <div>
              <h1 className="text-lg font-bold text-foreground">EMDECOB</h1>
              <p className="text-xs text-muted-foreground">Consultas</p>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className={`flex-1 ${collapsed ? "p-2" : "p-4"} space-y-2 transition-all duration-300`}>
        {!collapsed && (
          <p className="px-4 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Experiencia de Usuario
          </p>
        )}

        <SidebarNavLink to="/mis-tareas" icon={UserCheck} collapsed={collapsed} title="Mis Tareas">
          {!collapsed && "Mis Tareas"}
        </SidebarNavLink>

        {!collapsed && (
          <p className="px-4 py-2 mt-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Menú Principal
          </p>
        )}

        <SidebarNavLink to="/importar" icon={Upload} collapsed={collapsed} title="Importar Excel">
          {!collapsed && "Importar Excel"}
        </SidebarNavLink>

        <SidebarNavLink to="/consultar" icon={Search} collapsed={collapsed} title="Consultar Caso">
          {!collapsed && "Consultar Caso"}
        </SidebarNavLink>

        <SidebarNavLink to="/consultar-nombre" icon={Search} collapsed={collapsed} title="Consultar por Nombre">
          {!collapsed && "Consultar por Nombre"}
        </SidebarNavLink>

        <SidebarNavLink to="/casos" icon={FolderOpen} collapsed={collapsed} title="Todos los Casos">
          {!collapsed && "Todos los Casos"}
        </SidebarNavLink>

        <SidebarNavLink to="/no-encontrados" icon={AlertTriangle} collapsed={collapsed} title="No Encontrados">
          {!collapsed && "No Encontrados"}
        </SidebarNavLink>

        {!collapsed && (
          <p className="px-4 py-2 mt-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Gestión (ClickUp)
          </p>
        )}

        <SidebarNavLink to="/proyectos" icon={LayoutDashboard} collapsed={collapsed} title="Mis Proyectos">
          {!collapsed && "Mis Proyectos"}
        </SidebarNavLink>

        <SidebarNavLink to="/agenda" icon={Calendar} collapsed={collapsed} title="Agenda / Calendario">
          {!collapsed && "Agenda / Calendario"}
        </SidebarNavLink>

        {isAdmin && (
          <SidebarNavLink to="/configuracion" icon={Settings} collapsed={collapsed} title="Configuración">
            {!collapsed && "Configuración"}
          </SidebarNavLink>
        )}
      </nav>

      {/* Theme Toggle & User Menu */}
      <div className={`${collapsed ? "p-2" : "p-4"} border-t border-sidebar-border space-y-4 transition-all duration-300`}>
        {collapsed ? (
          <div className="flex justify-center py-1" title={`Modo ${theme === "dark" ? "Oscuro" : "Claro"}`}>
            <button onClick={toggleTheme} className="p-2 rounded-lg hover:bg-sidebar-accent transition-colors">
              {theme === "dark" ? (
                <Moon className="h-5 w-5 text-primary" />
              ) : (
                <Sun className="h-5 w-5 text-warning" />
              )}
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-between px-4 py-2 bg-sidebar-accent/50 rounded-lg border border-sidebar-border/50">
            <div className="flex items-center gap-2">
              {theme === "dark" ? (
                <Moon className="h-4 w-4 text-primary" />
              ) : (
                <Sun className="h-4 w-4 text-warning" />
              )}
              <span className="text-xs font-medium text-foreground">
                Modo {theme === "dark" ? "Oscuro" : "Claro"}
              </span>
            </div>
            <Switch
              checked={theme === "light"}
              onCheckedChange={toggleTheme}
              className="data-[state=checked]:bg-primary"
            />
          </div>
        )}
        <UserMenu collapsed={collapsed} />
      </div>

      {/* Footer */}
      {!collapsed && (
        <div className="p-3 border-t border-sidebar-border">
          <p className="text-xs text-muted-foreground text-center">© 2026 EMDECOB</p>
        </div>
      )}
    </aside>
  );
}
