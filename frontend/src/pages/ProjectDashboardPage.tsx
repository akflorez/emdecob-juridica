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
import { 
  getWorkspaces, 
  getTasks, 
  importClickUp, 
  createTask, 
  updateTask,
  type Workspace,
  type Task 
} from "@/services/api";
import { useEffect } from "react";

export default function ProjectDashboardPage() {
  const [isSyncing, setIsSyncing] = useState(false);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedListId, setSelectedListId] = useState<number | null>(null);
  const [expandedWorkspaces, setExpandedWorkspaces] = useState<Set<number>>(new Set());
  const [expandedFolders, setExpandedFolders] = useState<Set<number>>(new Set());

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (selectedListId) {
      fetchTasks(selectedListId);
    }
  }, [selectedListId]);

  const fetchInitialData = async () => {
    setIsLoading(true);
    try {
      const wsData = await getWorkspaces();
      setWorkspaces(wsData);
      if (wsData.length > 0 && wsData[0].folders.length > 0 && wsData[0].folders[0].lists.length > 0) {
        const firstList = wsData[0].folders[0].lists[0];
        setSelectedListId(firstList.id);
        setExpandedWorkspaces(new Set([wsData[0].id]));
        setExpandedFolders(new Set([wsData[0].folders[0].id]));
      }
    } catch (error) {
      toast.error("Error al cargar proyectos");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchTasks = async (listId: number) => {
    try {
      const taskData = await getTasks({ list_id: listId });
      setTasks(taskData);
    } catch (error) {
      toast.error("Error al cargar tareas");
    }
  };

  const handleSync = async () => {
    const token = prompt("Ingresa tu ClickUp API Token:");
    if (!token) return;

    setIsSyncing(true);
    try {
      const res = await importClickUp(token);
      toast.success("Sincronización iniciada", {
        description: res.message,
      });
      // Recargar después de un momento
      setTimeout(fetchInitialData, 5000);
    } catch (error: any) {
      toast.error("Error en sincronización", { description: error.message });
    } finally {
      setIsSyncing(false);
    }
  };

  const toggleWorkspace = (id: number) => {
    const next = new Set(expandedWorkspaces);
    if (next.has(id)) next.delete(id); else next.add(id);
    setExpandedWorkspaces(next);
  };

  const toggleFolder = (id: number) => {
    const next = new Set(expandedFolders);
    if (next.has(id)) next.delete(id); else next.add(id);
    setExpandedFolders(next);
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
            {isSyncing ? "Sincronizar ClickUp" : "Sincronizar ClickUp"}
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
            {workspaces.map(ws => (
              <div key={ws.id} className="space-y-1">
                <div 
                  className="flex items-center gap-2 p-2 rounded-lg hover:bg-muted/50 cursor-pointer text-sm font-medium"
                  onClick={() => toggleWorkspace(ws.id)}
                >
                  <ChevronRight className={`h-4 w-4 text-muted-foreground transition-transform ${expandedWorkspaces.has(ws.id) ? "rotate-90" : ""}`} />
                  <LayoutDashboard className="h-4 w-4 text-primary" />
                  <span>{ws.name}</span>
                </div>
                
                {expandedWorkspaces.has(ws.id) && ws.folders.map(f => (
                  <div key={f.id} className="ml-4 space-y-1">
                    <div 
                      className="flex items-center gap-2 p-2 rounded-lg hover:bg-muted/50 cursor-pointer text-sm font-medium opacity-80"
                      onClick={() => toggleFolder(f.id)}
                    >
                      <ChevronRight className={`h-3 w-3 text-muted-foreground transition-transform ${expandedFolders.has(f.id) ? "rotate-90" : ""}`} />
                      <span>{f.name}</span>
                    </div>

                    {expandedFolders.has(f.id) && f.lists.map(list => (
                      <div 
                        key={list.id}
                        className={`ml-6 flex items-center justify-between p-2 rounded-lg cursor-pointer text-sm ${selectedListId === list.id ? "bg-primary/10 text-primary font-bold" : "hover:bg-muted/30"}`}
                        onClick={() => setSelectedListId(list.id)}
                      >
                        <div className="flex items-center gap-2">
                          <RefreshCw className="h-3 w-3 opacity-50" />
                          <span>{list.name}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            ))}
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
            {tasks.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
                <CheckCircle2 className="h-12 w-12 opacity-20 mb-4" />
                <p>No hay tareas en esta lista.</p>
              </div>
            ) : tasks.map(task => (
              <Card 
                key={task.id} 
                className={`border-l-4 hover:shadow-md transition-all cursor-pointer ${
                  task.priority === 'urgent' ? 'border-l-red-500' : 
                  task.priority === 'high' ? 'border-l-orange-500' : 
                  task.priority === 'normal' ? 'border-l-blue-500' : 'border-l-muted'
                }`}
              >
                <CardContent className="p-4">
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                            <CheckCircle2 
                              className={`h-5 w-5 transition-colors ${task.status === 'complete' ? 'text-green-500' : 'text-muted-foreground hover:text-green-500'}`} 
                            />
                            <div className="space-y-1">
                                <h3 className="font-semibold text-sm leading-none">{task.title}</h3>
                                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                    <span className={`flex items-center gap-1 font-medium bg-muted px-1.5 py-0.5 rounded ${
                                      task.status === 'complete' ? 'text-green-600' : 'text-primary'
                                    }`}>
                                        <Clock className="h-3 w-3" /> {task.status.toUpperCase()}
                                    </span>
                                    {task.due_date && (
                                      <span className="flex items-center gap-1">
                                          <CalendarIcon className="h-3 w-3" /> {new Date(task.due_date).toLocaleDateString()}
                                      </span>
                                    )}
                                    {task.clickup_id && (
                                      <Badge variant="outline" className="text-[9px] h-4">ID: {task.clickup_id}</Badge>
                                    )}
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="h-7 w-7 rounded-full border-2 border-background bg-muted flex items-center justify-center text-[10px] text-muted-foreground" title="Responsable">
                                <UserIcon className="h-4 w-4" />
                            </div>
                            <div className="flex items-center gap-2 text-muted-foreground">
                                <div className="flex items-center gap-1 text-[11px]">
                                    <MessageSquare className="h-3.5 w-3.5" /> 0
                                </div>
                            </div>
                        </div>
                    </div>
                </CardContent>
              </Card>
            ))}

            <Button variant="ghost" className="w-full text-muted-foreground border-dashed border h-10 hover:bg-muted/50">
                <Plus className="h-4 w-4 mr-2" /> Agregar Tarea
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
