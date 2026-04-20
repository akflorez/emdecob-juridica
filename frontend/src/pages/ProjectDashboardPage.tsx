import { useState } from "react";
import { 
  LayoutDashboard, 
  FolderPlus, 
  ListPlus, 
  Plus, 
  RefreshCw, 
  Search, 
  Filter,
  MoreVertical,
  ChevronRight,
  MessageSquare,
  Paperclip,
  Calendar as CalendarIcon,
  User as UserIcon,
  CheckCircle2,
  Clock
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

export default function ProjectDashboardPage() {
  const [isSyncing, setIsSyncing] = useState(false);

  const handleSync = () => {
    setIsSyncing(true);
    // Simulación de sincronización
    setTimeout(() => {
      setIsSyncing(false);
      toast.success("Migración finalizada", {
        description: "Se han importado 142 tareas y 12 carpetas desde ClickUp.",
      });
    }, 3000);
  };

  return (
    <div className="flex flex-col h-full space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Gestión de Proyectos</h1>
          <p className="text-muted-foreground">Administra tus tareas y sincroniza con ClickUp en tiempo real.</p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleSync}
            disabled={isSyncing}
            className="group"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isSyncing ? "animate-spin" : "group-hover:rotate-180 transition-transform duration-500"}`} />
            {isSyncing ? "Sincronizando..." : "Sincronizar ClickUp"}
          </Button>
          <Button size="sm">
            <Plus className="mr-2 h-4 w-4" /> Nueva Tarea
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-250px)]">
        {/* Sidebar de Jerarquía */}
        <div className="lg:col-span-1 border rounded-xl bg-card/50 overflow-hidden flex flex-col">
          <div className="p-4 border-b bg-muted/30 flex items-center justify-between">
            <span className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Explorador</span>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <FolderPlus className="h-4 w-4" />
            </Button>
          </div>
          
          <div className="flex-1 overflow-auto p-2 space-y-1">
            {/* Ejemplo de estructura ClickUp */}
            <div className="space-y-1">
                <div className="flex items-center gap-2 p-2 rounded-lg hover:bg-muted/50 cursor-pointer text-sm font-medium">
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    <LayoutDashboard className="h-4 w-4 text-primary" />
                    <span>FNA Jurídica</span>
                </div>
                <div className="ml-4 space-y-1">
                    <div className="flex items-center justify-between p-2 rounded-lg bg-primary/10 text-primary cursor-pointer text-sm font-medium">
                        <div className="flex items-center gap-2">
                            <RefreshCw className="h-3 w-3" />
                            <span>Procesos Activos</span>
                        </div>
                        <Badge variant="outline" className="text-[10px] h-4 px-1 bg-primary text-primary-foreground border-none">24</Badge>
                    </div>
                    <div className="flex items-center gap-2 p-2 rounded-lg hover:bg-muted/50 cursor-pointer text-sm text-muted-foreground">
                        <RefreshCw className="h-3 w-3" />
                        <span>Saneamiento Paul</span>
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-2 p-2 rounded-lg hover:bg-muted/50 cursor-pointer text-sm font-medium text-muted-foreground">
                <ChevronRight className="h-4 w-4" />
                <LayoutDashboard className="h-4 w-4" />
                <span>Civil Gral</span>
            </div>
          </div>
        </div>

        {/* Content Area - Task List view */}
        <div className="lg:col-span-3 flex flex-col space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input placeholder="Buscar tareas..." className="pl-9 bg-muted/20" />
            </div>
            <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" className="text-muted-foreground">
                    <Filter className="mr-2 h-4 w-4" /> Filtrar
                </Button>
                <Button variant="ghost" size="sm" className="text-muted-foreground">
                    <MoreVertical className="h-4 w-4" />
                </Button>
            </div>
          </div>

          <div className="flex-1 overflow-auto space-y-4 rounded-xl border border-dashed p-4 bg-muted/10">
            {/* Task Row Example 1 */}
            <Card className="border-l-4 border-l-orange-500 hover:shadow-md transition-all cursor-pointer">
                <CardContent className="p-4">
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                            <CheckCircle2 className="h-5 w-5 text-muted-foreground hover:text-green-500 transition-colors" />
                            <div className="space-y-1">
                                <h3 className="font-semibold text-sm leading-none">REINOSO CORDOBA JUAN CARLOS - 73001400300420030041400</h3>
                                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                    <span className="flex items-center gap-1 font-medium bg-muted px-1.5 py-0.5 rounded text-orange-600">
                                        <Clock className="h-3 w-3" /> Pendiente Actuación
                                    </span>
                                    <span className="flex items-center gap-1">
                                        <CalendarIcon className="h-3 w-3" /> Hoy 4:00 PM
                                    </span>
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="flex -space-x-2">
                                <div className="h-7 w-7 rounded-full border-2 border-background bg-primary flex items-center justify-center text-[10px] text-white" title="Santiago">S</div>
                                <div className="h-7 w-7 rounded-full border-2 border-background bg-orange-500 flex items-center justify-center text-[10px] text-white" title="Paul">P</div>
                            </div>
                            <div className="flex items-center gap-2 text-muted-foreground">
                                <div className="flex items-center gap-1 text-[11px]">
                                    <MessageSquare className="h-3.5 w-3.5" /> 3
                                </div>
                                <div className="flex items-center gap-1 text-[11px]">
                                    <Paperclip className="h-3.5 w-3.5" /> 1
                                </div>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Task Row Example 2 */}
            <Card className="border-l-4 border-l-blue-500 hover:shadow-md transition-all cursor-pointer">
                <CardContent className="p-4">
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                            <CheckCircle2 className="h-5 w-5 text-muted-foreground hover:text-green-500 transition-colors" />
                            <div className="space-y-1">
                                <h3 className="font-semibold text-sm leading-none">WILLIAM POLANIA ROJAS - Envío Memorial Poder</h3>
                                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                    <span className="flex items-center gap-1 font-medium bg-muted px-1.5 py-0.5 rounded text-blue-600">
                                        En Proceso
                                    </span>
                                    <span className="flex items-center gap-1">
                                        Mañana
                                    </span>
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="h-7 w-7 rounded-full border-2 border-background bg-blue-500 flex items-center justify-center text-[10px] text-white" title="Ana">A</div>
                            <div className="flex items-center gap-2 text-muted-foreground">
                                <div className="flex items-center gap-1 text-[11px]">
                                    <MessageSquare className="h-3.5 w-3.5" /> 0
                                </div>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Button variant="ghost" className="w-full text-muted-foreground border-dashed border h-10 hover:bg-muted/50">
                <Plus className="h-4 w-4 mr-2" /> Agregar Tarea
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
