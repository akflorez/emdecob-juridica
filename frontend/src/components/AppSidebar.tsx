import { Upload, Search, FolderOpen, Scale, Settings, AlertTriangle } from "lucide-react";
import { SidebarNavLink } from "./SidebarNavLink";
import { UserMenu } from "./UserMenu";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { Sun, Moon } from "lucide-react";
import { Switch } from "@/components/ui/switch";

export function AppSidebar() {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const isAdmin = user?.is_admin === true;

  return (
    <aside className="w-64 min-h-screen bg-sidebar border-r border-sidebar-border flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-sidebar-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
            <Scale className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-foreground">EMDECOB</h1>
            <p className="text-xs text-muted-foreground">Consultas</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        <p className="px-4 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Menú Principal
        </p>

        <SidebarNavLink to="/importar" icon={Upload}>
          Importar Excel
        </SidebarNavLink>

        <SidebarNavLink to="/consultar" icon={Search}>
          Consultar Caso
        </SidebarNavLink>

        <SidebarNavLink to="/consultar-nombre" icon={Search}>
          Consultar por Nombre
        </SidebarNavLink>

        <SidebarNavLink to="/casos" icon={FolderOpen}>
          Todos los Casos
        </SidebarNavLink>

        <SidebarNavLink to="/no-encontrados" icon={AlertTriangle}>
          No Encontrados
        </SidebarNavLink>

        {isAdmin && (
          <SidebarNavLink to="/configuracion" icon={Settings}>
            Configuración
          </SidebarNavLink>
        )}
      </nav>

      {/* Theme Toggle & User Menu */}
      <div className="p-4 border-t border-sidebar-border space-y-4">
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
        <UserMenu />
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-sidebar-border">
        <p className="text-xs text-muted-foreground text-center">© 2026 EMDECOB</p>
      </div>
    </aside>
  );
}
