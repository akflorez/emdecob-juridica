import { useState, useEffect } from "react";
import { 
  LayoutDashboard, FolderPlus, ListPlus, Plus, RefreshCw, Search, 
  Filter, MoreVertical, ChevronRight, MessageSquare, 
  Calendar as CalendarIcon, User as UserIcon, CheckCircle2, Clock,
  LayoutGrid, CalendarDays, List as ListIcon, Zap, PlayCircle, Lock
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { toast } from "sonner";
import { 
  getWorkspaces, getTasks, importClickUp, updateTask,
  type Workspace, type Task as TaskType
} from "@/services/api";
import { TaskDrawer } from "@/components/TaskDrawer";
import { Calendar as BigCalendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import 'react-big-calendar/lib/css/react-big-calendar.css';

// Español para el calendario
moment.locale('es');
const localizer = momentLocalizer(moment);

const BOARD_COLUMNS = [
  { id: 'to do', label: 'To Do', color: 'bg-slate-100 text-slate-700 dark:bg-slate-900 dark:text-slate-300', dot: 'bg-slate-400' },
  { id: 'in progress', label: 'En Progreso', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400', dot: 'bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]' },
  { id: 'review', label: 'Revisión', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-400', dot: 'bg-yellow-400 shadow-[0_0_8px_rgba(250,204,21,0.5)]' },
  { id: 'complete', label: 'Completado', color: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400', dot: 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' }
];

export default function ProjectDashboardPage() {
  const [isSyncing, setIsSyncing] = useState(false);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [tasks, setTasks] = useState<TaskType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedListId, setSelectedListId] = useState<number | null>(null);
  const [expandedWorkspaces, setExpandedWorkspaces] = useState<Set<number>>(new Set());
  const [expandedFolders, setExpandedFolders] = useState<Set<number>>(new Set());
  
  // States para el Modal/Drawer interactivo
  const [selectedTask, setSelectedTask] = useState<TaskType | null>(null);
  const [draggedTaskId, setDraggedTaskId] = useState<number | null>(null);
  
  // Filtros
  const [searchTerm, setSearchTerm] = useState("");
  const [dateRange, setDateRange] = useState({ start: "", end: "" });
  const [responsibleFilter, setResponsibleFilter] = useState<number | "all">("all");
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    getUsers().then(setUsers).catch(console.error);
  }, []);

  useEffect(() => {
    fetchInitialData();
  }, []);

  // Cuando cambia selectedListId, recargar tareas de esa lista
  // Si no hay lista seleccionada, cargar TODAS las tareas
  useEffect(() => {
    fetchTasks(selectedListId ?? undefined);
  }, [selectedListId]);

  const fetchInitialData = async () => {
    setIsLoading(true);
    try {
      const wsData = await getWorkspaces();
      setWorkspaces(wsData);
      // Expandir el primer workspace y carpeta para navegación visual
      // pero NO pre-seleccionar ninguna lista: queremos ver todas las tareas al inicio
      if (wsData.length > 0) {
        setExpandedWorkspaces(new Set([wsData[0].id]));
        if (wsData[0].folders.length > 0) {
          setExpandedFolders(new Set([wsData[0].folders[0].id]));
        }
      }
      // Cargar TODAS las tareas sin filtro al inicio
      await fetchTasks(undefined);
    } catch (error) {
      toast.error("Error al cargar proyectos");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchTasks = async (listId?: number) => {
    try {
      console.log('[DASHBOARD] Fetching tasks. list_id:', listId ?? 'ALL');
      const taskData = await getTasks({ list_id: listId });
      console.log('[DASHBOARD] Received:', taskData?.length ?? 0, 'tasks');
      setTasks(Array.isArray(taskData) ? taskData : []);
    } catch (error) {
      console.error('[DASHBOARD] Error fetching tasks:', error);
      toast.error("Error al cargar tareas");
      setTasks([]);
    }
  };

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (selectedListId) fetchTasks(selectedListId);
    }, 500);
    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm]);

  const handleSync = async () => {
    const token = prompt("Ingresa tu ClickUp API Token:");
    if (!token) return;
    setIsSyncing(true);
    try {
      const res = await importClickUp(token);
      toast.success("Sincronización iniciada", { description: res.message });
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

  const handleDrop = async (status: string) => {
    if (!draggedTaskId) return;
    const t = tasks.find(x => x.id === draggedTaskId);
    if (t && t.status !== status) {
      setTasks(prev => prev.map(x => x.id === draggedTaskId ? { ...x, status } : x));
      try {
        await updateTask(draggedTaskId, { status });
      } catch(e) {
        toast.error("Error sincronizando movimiento.");
        fetchTasks(selectedListId!); // revertir
      }
    }
    setDraggedTaskId(null);
  };

  const filteredTasks = tasks.filter(t => {
    // Filtro de búsqueda (Radicado o Título)
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      const matchTitle = t.title.toLowerCase().includes(search);
      const matchDesc = t.description?.toLowerCase().includes(search);
      if (!matchTitle && !matchDesc) return false;
    }

    // Filtro de responsable
    if (responsibleFilter !== "all" && t.assignee_id !== responsibleFilter) {
        return false;
    }

    // Filtro de fechas
    if (!dateRange.start && !dateRange.end) return true;
    if (!t.due_date) return true; // Keep dateless tasks so they show up
    const d = new Date(t.due_date);
    if (dateRange.start && d < new Date(dateRange.start)) return false;
    if (dateRange.end && d > new Date(dateRange.end)) return false;
    return true;
  });

  // Agrupar por parent_id para visualización jerárquica
  const parentTasks = filteredTasks.filter(t => !t.parent_id);
  const subtasksMap = filteredTasks.reduce((acc, t) => {
    if (t.parent_id) {
       if (!acc[t.parent_id]) acc[t.parent_id] = [];
       acc[t.parent_id].push(t);
    }
    return acc;
  }, {} as Record<number, TaskType[]>);

  const calendarEvents = filteredTasks.map(t => {
    const d = t.due_date ? new Date(t.due_date) : new Date();
    return {
      id: t.id,
      title: t.title + (!t.due_date ? ' (Sin Fecha)' : ''),
      start: d,
      end: d,
      resource: t,
    };
  });

  return (
    <div className="flex flex-col h-full bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-primary/5 via-background to-background relative overflow-hidden">
      {/* Decorative Orbs */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[100px] -z-10 pointer-events-none mix-blend-screen" />
      <div className="absolute bottom-[-20%] left-[-10%] w-[400px] h-[400px] bg-blue-500/10 rounded-full blur-[100px] -z-10 pointer-events-none" />

      {/* Header Panel */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 py-6 border-b border-border/40 px-6 backdrop-blur-sm z-10 relative">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-gradient-to-tr from-primary to-blue-500 rounded-lg shadow-lg shadow-primary/20">
              <Zap className="h-5 w-5 text-white" />
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/70 leading-[1.2]">
              Gestión Avanzada
            </h1>
            <Badge variant="outline" className="bg-orange-500/10 text-orange-600 border-orange-200 font-bold ml-2 h-6 self-start mt-2 px-3 animate-pulse">v4.0 SENIOR</Badge>
          </div>
          <p className="text-sm font-medium text-muted-foreground ml-[44px]">Sincronización de grado militar y diagnóstico resiliente.</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={handleSync} disabled={isSyncing} className="group relative overflow-hidden bg-background/50 backdrop-blur border-border/50 hover:bg-muted/50 transition-all duration-300 rounded-full px-6">
            <span className="relative z-10 flex items-center font-semibold">
              <RefreshCw className={`mr-2 h-4 w-4 text-primary ${isSyncing ? "animate-spin" : "group-hover:rotate-180 transition-transform duration-700"}`} />
              Sincronizar ClickUp
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
          </Button>
          <Button onClick={() => setSelectedTask({ title: '', status: 'to do', priority: 'normal', list_id: selectedListId } as any)} className="rounded-full shadow-lg shadow-primary/20 hover:shadow-primary/40 hover:-translate-y-0.5 transition-all duration-300 font-bold px-6 bg-gradient-to-r from-primary to-blue-600 hover:from-primary/90 hover:to-blue-500">
            <Plus className="mr-2 h-4 w-4" /> Lanzar Tarea
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-140px)] p-6 pt-6 z-10">
        
        {/* Sidebar de Jerarquía (Explorador) */}
        <div className="lg:col-span-3 flex flex-col h-full bg-card/80 backdrop-blur-xl border border-border/40 rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(255,255,255,0.02)] overflow-hidden transition-all duration-300 hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)]">
          <div className="p-4 border-b border-border/40 bg-gradient-to-r from-muted/50 to-transparent flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground/80 flex items-center gap-2">
              <LayoutDashboard className="h-3.5 w-3.5" /> Explorador
            </span>
            <Button variant="ghost" size="icon" className="h-7 w-7 rounded-full bg-background/50 shadow-sm hover:bg-primary hover:text-primary-foreground transition-all duration-300">
              <Plus className="h-3.5 w-3.5" />
            </Button>
          </div>
          
          <div className="flex-1 overflow-auto p-3 space-y-3 custom-scrollbar">
            {workspaces.map(ws => (
              <div key={ws.id} className="space-y-1 relative">
                <div 
                  className="flex items-center justify-between p-2 rounded-xl hover:bg-primary/5 cursor-pointer text-sm font-bold transition-all duration-200 group"
                  onClick={() => toggleWorkspace(ws.id)}
                >
                  <div className="flex items-center gap-2.5 text-foreground/90 group-hover:text-primary transition-colors">
                    <ChevronRight className={`h-4 w-4 text-muted-foreground/50 transition-transform duration-300 ${expandedWorkspaces.has(ws.id) ? "rotate-90 text-primary" : "group-hover:translate-x-1"}`} />
                    <div className="p-1 rounded bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/10">
                      <Lock className="h-3 w-3 text-primary" />
                    </div>
                    <span className="truncate">{ws.name}</span>
                  </div>
                </div>
                
                {/* Folders con Animacion Slide-Down */}
                {expandedWorkspaces.has(ws.id) && ws.folders.map(f => (
                  <div key={f.id} className="ml-5 space-y-1 relative before:absolute before:-left-3 before:top-4 before:h-[calc(100%-16px)] before:w-px before:bg-gradient-to-b before:from-border before:to-transparent animate-in slide-in-from-top-2 fade-in duration-200">
                    <div 
                      className="flex items-center justify-between p-2 rounded-xl hover:bg-muted/50 cursor-pointer text-sm font-semibold opacity-90 transition-all group"
                      onClick={() => toggleFolder(f.id)}
                    >
                      <div className="flex items-center gap-2.5">
                        <ChevronRight className={`h-3.5 w-3.5 text-muted-foreground transition-transform duration-300 ${expandedFolders.has(f.id) ? "rotate-90" : "group-hover:translate-x-1"}`} />
                        <FolderPlus className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors" />
                        <span className="group-hover:text-foreground transition-colors truncate">{f.name}</span>
                      </div>
                    </div>

                    {expandedFolders.has(f.id) && f.lists.map(list => (
                      <div 
                        key={list.id}
                        className={`ml-5 flex items-center justify-between px-3 py-2 rounded-xl cursor-pointer text-[13px] transition-all duration-300 animate-in slide-in-from-left-2 fade-in ${selectedListId === list.id ? "bg-gradient-to-r from-primary to-primary/80 text-primary-foreground font-bold shadow-md shadow-primary/25 translate-x-1" : "text-muted-foreground hover:bg-muted hover:text-foreground hover:translate-x-1"}`}
                        onClick={() => setSelectedListId(list.id)}
                      >
                        <div className="flex items-center gap-2.5">
                          <span className={`w-2 h-2 rounded-full shadow-[0_0_5px_currentColor] ${selectedListId === list.id ? 'bg-white' : 'bg-primary/40'}`} />
                          <span className="truncate">{list.name}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* Content Area - Tabs para List / Kanban / Calendar */}
        <div className="lg:col-span-9 flex flex-col h-full overflow-hidden bg-card/40 backdrop-blur-sm border border-border/30 rounded-2xl shadow-xl">
          <Tabs defaultValue="board" className="flex-1 flex flex-col h-full w-full p-4 pb-0">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
              <div className="relative flex-1 max-w-md group">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                </div>
                <Input 
                  placeholder="Buscar por radicado o nombre..." 
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 bg-background/50 backdrop-blur shadow-sm border-border/50 focus-visible:ring-primary/30 rounded-full h-10 transition-all duration-300" 
                />
              </div>

              <div className="flex gap-2 items-center">
                <Select 
                  value={String(responsibleFilter)} 
                  onValueChange={(val) => setResponsibleFilter(val === "all" ? "all" : Number(val))}
                >
                  <SelectTrigger className="h-9 w-[180px] text-xs bg-background/50 rounded-lg">
                    <SelectValue placeholder="Responsable: Todos" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos los responsables</SelectItem>
                    {users.map(u => (
                      <SelectItem key={u.id} value={String(u.id)}>{u.nombre || u.username}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Input 
                  type="date" 
                  value={dateRange.start} 
                  onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
                  className="h-9 w-32 text-xs rounded-lg bg-background/50"
                />
                <span className="text-muted-foreground">→</span>
                <Input 
                  type="date" 
                  value={dateRange.end} 
                  onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
                  className="h-9 w-32 text-xs rounded-lg bg-background/50"
                />
              </div>
              
              <div className="flex items-center justify-end gap-3 flex-wrap">
                <TabsList className="bg-muted/50 backdrop-blur-md p-1 rounded-full shadow-inner border border-white/5 dark:border-white/10">
                  <TabsTrigger value="list" className="rounded-full px-5 py-1.5 data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-sm transition-all duration-300 font-semibold text-sm">
                    <ListIcon className="h-4 w-4 mr-2" /> Lista
                  </TabsTrigger>
                  <TabsTrigger value="board" className="rounded-full px-5 py-1.5 data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-sm transition-all duration-300 font-semibold text-sm">
                    <LayoutGrid className="h-4 w-4 mr-2" /> Tablero
                  </TabsTrigger>
                  <TabsTrigger value="calendar" className="rounded-full px-5 py-1.5 data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-sm transition-all duration-300 font-semibold text-sm">
                    <CalendarDays className="h-4 w-4 mr-2" /> Agenda
                  </TabsTrigger>
                  <TabsTrigger value="stats" className="rounded-full px-5 py-1.5 data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-sm transition-all duration-300 font-semibold text-sm">
                    <Zap className="h-4 w-4 mr-2" /> Dashboard
                  </TabsTrigger>
                </TabsList>
                <div className="h-6 w-px bg-border mx-1 hidden sm:block" />
                <Button variant="outline" size="icon" className="rounded-full bg-background/50 backdrop-blur hover:bg-muted shadow-sm">
                  <Filter className="h-4 w-4 text-muted-foreground" />
                </Button>
                <Button variant="outline" size="icon" className="rounded-full bg-background/50 backdrop-blur hover:bg-muted shadow-sm">
                  <MoreVertical className="h-4 w-4 text-muted-foreground" />
                </Button>
              </div>
            </div>

            <div className="flex-1 w-full relative overflow-hidden pt-2 rounded-t-xl">
              
              {/* TAB: LIST (Datatable ultra moderna) */}
              <TabsContent value="list" className="h-full m-0 overflow-y-auto space-y-3 custom-scrollbar pb-6 animate-in fade-in duration-500">
                {parentTasks.length === 0 ? (
                  <EmptyState text="El lienzo está en blanco. Inicia un nuevo flujo." />
                ) : parentTasks.map((task, i) => (
                  <div key={task.id} className="space-y-2">
                    <TaskRow task={task} onClick={() => setSelectedTask(task)} index={i} />
                    {subtasksMap[task.id] && (
                      <div className="ml-12 space-y-2 border-l-2 border-dashed border-primary/20 pl-4 py-1">
                        {subtasksMap[task.id].map((sub, si) => (
                          <TaskRow key={sub.id} task={sub} onClick={() => setSelectedTask(sub)} index={si} isSubtask />
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </TabsContent>

              {/* TAB: BOARD KANBAN (Drag and Drop nativo) */}
              <TabsContent value="board" className="h-[calc(100%-20px)] m-0 overflow-x-auto flex gap-5 items-start custom-scrollbar pb-4 animate-in fade-in zoom-in-95 duration-500">
                {BOARD_COLUMNS.map(col => (
                  <div 
                    key={col.id}
                    onDragOver={e => e.preventDefault()}
                    onDrop={() => handleDrop(col.id)}
                    className="min-w-[320px] max-w-[320px] flex flex-col bg-background/40 backdrop-blur-md border border-border/40 rounded-2xl h-full shadow-sm hover:shadow-md transition-all duration-300"
                  >
                    <div className="p-4 flex items-center justify-between border-b border-border/40 rounded-t-2xl bg-muted/30">
                      <div className="flex items-center gap-2">
                        <div className={`h-2 w-2 rounded-full ${col.color}`} />
                        <span className="font-bold tracking-wide uppercase text-xs text-foreground/80">{col.label}</span>
                        <Badge variant="secondary" className="ml-1 text-[10px] bg-background/50">{filteredTasks.filter(t => t.status?.trim().toLowerCase() === col.id.trim().toLowerCase()).length}</Badge>
                      </div>
                      <Plus className="h-4 w-4 text-muted-foreground/50 cursor-pointer hover:text-primary transition-colors" />
                    </div>
                    
                    <div className="flex-1 overflow-y-auto p-3 space-y-3 custom-scrollbar">
                      {filteredTasks.filter(t => t.status?.trim().toLowerCase() === col.id.trim().toLowerCase()).map(task => (
                        <div 
                          key={task.id}
                          draggable
                          onDragStart={() => setDraggedTaskId(task.id)}
                          onClick={() => setSelectedTask(task)}
                          className="group bg-card/80 hover:bg-card p-4 rounded-xl border border-border/50 shadow-sm hover:shadow-md hover:border-primary/30 transition-all duration-300 cursor-pointer relative overflow-hidden animate-in fade-in slide-in-from-bottom-2"
                        >
                          <div className={`absolute left-0 top-0 w-1 h-full ${task.priority === 'urgent' ? 'bg-red-500/50' : 'bg-primary/30'}`} />
                          <h4 className="font-bold text-[14px] mb-4 leading-snug line-clamp-2 pl-2 text-foreground/90 group-hover:text-primary transition-colors">{task.title}</h4>
                          <div className="flex items-center justify-between text-xs pl-2 border-t border-border/40 pt-3">
                            <span className="text-muted-foreground font-medium flex items-center gap-1">
                              <UserIcon className="h-3 w-3" /> US
                            </span>
                            {task.due_date && (
                              <span className="flex items-center gap-1 font-bold text-primary">
                                <CalendarIcon className="h-3 w-3" />
                                {(() => {
                                  const d = new Date(task.due_date);
                                  return isNaN(d.getTime()) ? 'Pendiente' : d.toLocaleDateString('es-CO', {day: 'numeric', month: 'short'});
                                })()}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </TabsContent>

              {/* TAB: CALENDAR (Visión Macro) */}
              <TabsContent value="calendar" className="h-full m-0 p-1 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <style>{`
                  .rbc-calendar { font-family: inherit; }
                  .rbc-month-view { border-radius: 12px; overflow: hidden; border-color: hsl(var(--border)/0.5); border-width: 1px; }
                  .rbc-header { padding: 10px 0; font-weight: 700; text-transform: uppercase; font-size: 11px; background: hsl(var(--muted)/0.3); border-color: hsl(var(--border)/0.5); }
                  .rbc-day-bg { border-color: hsl(var(--border)/0.3); }
                  .rbc-off-range-bg { background: hsl(var(--muted)/0.1); }
                  .rbc-event { background-image: linear-gradient(to right, hsl(var(--primary)), hsl(var(--primary)/0.8)); border: none; border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: 600; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 2px; }
                  .rbc-today { background-color: hsl(var(--primary)/0.03); }
                  .rbc-toolbar button { color: hsl(var(--foreground)); border-radius: 8px; border-color: hsl(var(--border)/0.5); padding: 4px 12px; font-weight: 500; transition: all 0.2s; }
                  .rbc-toolbar button:hover { background-color: hsl(var(--muted)); }
                  .rbc-toolbar button.rbc-active { background-color: hsl(var(--primary)); color: white; border-color: hsl(var(--primary)); box-shadow: 0 4px 10px hsl(var(--primary)/0.3); }
                `}</style>
                <div className="h-full bg-background/80 backdrop-blur-xl rounded-2xl p-4 shadow-sm border border-border/40">
                  <BigCalendar
                    localizer={localizer}
                    events={calendarEvents}
                    startAccessor="start"
                    endAccessor="end"
                    style={{ height: '100%' }}
                    onSelectEvent={(e: any) => setSelectedTask(e.resource)}
                    messages={{ today: "Hoy", previous: "Volver", next: "Avanzar", month: "Mes", week: "Semana", day: "Día" }}
                  />
                </div>
              </TabsContent>

              {/* TAB: STATS (DASHBOARD PREMIUM) */}
              <TabsContent value="stats" className="h-full m-0 overflow-y-auto p-4 space-y-6 animate-in fade-in slide-in-from-right-4 duration-500 custom-scrollbar">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <Card className="bg-gradient-to-br from-primary/10 to-transparent border-primary/20 shadow-lg">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold text-primary uppercase tracking-tighter">Total Tareas</span>
                        <Zap className="h-5 w-5 text-primary" />
                      </div>
                      <div className="text-4xl font-black mt-2">{tasks.length}</div>
                      <p className="text-[10px] text-muted-foreground font-medium mt-1">Sincronizadas desde ClickUp</p>
                    </CardContent>
                  </Card>
                  
                  <Card className="bg-gradient-to-br from-green-500/10 to-transparent border-green-500/20 shadow-lg">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold text-green-600 uppercase tracking-tighter">Completadas</span>
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      </div>
                      <div className="text-4xl font-black mt-2 text-green-600">{tasks.filter(t => t.status === 'complete').length}</div>
                      <p className="text-[10px] text-muted-foreground font-medium mt-1">Éxito operativo</p>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-br from-blue-500/10 to-transparent border-blue-500/20 shadow-lg">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold text-blue-600 uppercase tracking-tighter">En Proceso</span>
                        <RefreshCw className="h-5 w-5 text-blue-500" />
                      </div>
                      <div className="text-4xl font-black mt-2 text-blue-600">{tasks.filter(t => t.status === 'in progress').length}</div>
                      <p className="text-[10px] text-muted-foreground font-medium mt-1">Gestión activa</p>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-br from-orange-500/10 to-transparent border-orange-500/20 shadow-lg">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold text-orange-600 uppercase tracking-tighter">Pendientes</span>
                        <Clock className="h-5 w-5 text-orange-500" />
                      </div>
                      <div className="text-4xl font-black mt-2 text-orange-600">{tasks.filter(t => t.status === 'to do').length}</div>
                      <p className="text-[10px] text-muted-foreground font-medium mt-1">Por iniciar</p>
                    </CardContent>
                  </Card>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-2 space-y-4">
                    <h3 className="text-xl font-bold flex items-center gap-2 px-2">
                      <UserIcon className="h-5 w-5 text-primary" /> Rendimiento por Responsable
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {users.map(u => {
                        const userTasks = tasks.filter(t => t.assignee_id === u.id);
                        if (userTasks.length === 0) return null;
                        const completed = userTasks.filter(t => t.status === 'complete').length;
                        const total = userTasks.length;
                        const pct = Math.round((completed / total) * 100);
                        
                        return (
                          <div key={u.id} className="p-5 rounded-2xl bg-card border border-border/40 shadow-sm hover:shadow-md transition-all group overflow-hidden relative">
                            <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${pct > 80 ? 'bg-green-500' : pct > 40 ? 'bg-blue-500' : 'bg-orange-500'}`} />
                            <div className="flex justify-between items-start mb-4">
                              <div className="flex items-center gap-3">
                                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-xs font-bold text-primary border border-primary/20">
                                  {(u.nombre || u.username || '??').split(' ').filter(Boolean).map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                                </div>
                                <div>
                                  <div className="font-bold text-foreground group-hover:text-primary transition-colors">{u.nombre || u.username}</div>
                                  <div className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Abogado / Gestor</div>
                                </div>
                              </div>
                              <Badge variant="secondary" className="font-black text-lg h-9 px-3">{pct}%</Badge>
                            </div>
                            
                            <div className="space-y-2">
                              <div className="flex justify-between text-xs font-bold">
                                <span>Progreso</span>
                                <span>{completed} / {total} Completadas</span>
                              </div>
                              <div className="h-3 w-full bg-muted/50 rounded-full overflow-hidden border border-border/20">
                                <div 
                                  className={`h-full transition-all duration-1000 ${pct > 80 ? 'bg-green-500' : pct > 40 ? 'bg-blue-500' : 'bg-orange-500'}`} 
                                  style={{ width: `${pct}%` }} 
                                />
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-xl font-bold flex items-center gap-2 px-2">
                      <ListIcon className="h-5 w-5 text-primary" /> Distribución de Estados
                    </h3>
                    <Card className="p-6 bg-card/50 backdrop-blur border-border/40">
                      <div className="space-y-5">
                        {BOARD_COLUMNS.map(col => {
                          const count = tasks.filter(t => t.status === col.id).length;
                          const pct = tasks.length > 0 ? Math.round((count / tasks.length) * 100) : 0;
                          return (
                            <div key={col.id} className="space-y-1.5">
                              <div className="flex justify-between text-xs">
                                <span className="font-bold flex items-center gap-2">
                                  <div className={`h-2 w-2 rounded-full ${col.dot}`} />
                                  {col.label}
                                </span>
                                <span className="text-muted-foreground font-bold">{count} ({pct}%)</span>
                              </div>
                              <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                                <div 
                                  className={`h-full ${col.color.split(' ')[0].replace('-100', '-500')}`} 
                                  style={{ width: `${pct}%` }} 
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </Card>
                  </div>
                </div>
              </TabsContent>
            </div>
          </Tabs>
        </div>
      </div>
      
      <TaskDrawer 
        task={selectedTask}
        open={!!selectedTask}
        onOpenChange={(open) => !open && setSelectedTask(null)}
        onTaskUpdate={(t) => {
          setTasks(prev => {
            const exists = prev.some(pt => pt.id === t.id);
            if (exists) return prev.map(pt => pt.id === t.id ? t : pt);
            return [t, ...prev];
          });
          setSelectedTask(t);
        }}
      />
    </div>
  );
}

// Subcomponente de fila Data-Table (List Mode) - Estilizado al máximo nivel
function TaskRow({ task, onClick, index, isSubtask }: { task: TaskType; onClick: () => void; index: number; isSubtask?: boolean }) {
  return (
    <div 
      onClick={onClick}
      style={{ animationDelay: `${index * 50}ms` }}
      className={`group relative flex items-center justify-between ${isSubtask ? 'p-3 bg-background/40 hover:bg-background/60 text-xs py-2' : 'p-4 bg-background/60'} backdrop-blur-md border border-border/40 hover:border-primary/40 rounded-xl hover:shadow-[0_8px_30px_rgb(0,0,0,0.06)] transition-all duration-300 cursor-pointer overflow-hidden animate-in fade-in slide-in-from-bottom-2`}
    >
      {/* Dynamic left indicator line */}
      <div className={`absolute left-0 top-0 bottom-0 w-1 ${task.status === 'complete' ? 'bg-green-500' : task.priority === 'urgent' ? 'bg-red-500' : 'bg-primary'} transition-all duration-300 group-hover:w-1.5`} />
      
      <div className="flex items-center gap-5 ml-2 overflow-hidden">
        <div className={`flex-shrink-0 ${isSubtask ? 'h-7 w-7' : 'h-9 w-9'} flex items-center justify-center rounded-full transition-all duration-500 ${task.status === 'complete' ? 'bg-green-100 text-green-600 dark:bg-green-900/30' : 'bg-muted/80 text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary'}`}>
          <CheckCircle2 className={`${isSubtask ? 'h-4 w-4' : 'h-5 w-5'}`} />
        </div>
        <div className="flex flex-col gap-1 min-w-0">
          <h3 className={`font-semibold ${isSubtask ? 'text-[13px]' : 'text-[15px]'} truncate max-w-[400px] text-foreground/90 group-hover:text-primary transition-colors`}>{task.title}</h3>
          {!isSubtask && (
            <div className="flex items-center gap-3 text-xs">
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full font-bold uppercase tracking-wider text-[9px] ${
                task.status === 'complete' ? 'bg-green-500/10 text-green-600 border border-green-500/20' : 
                task.status === 'in progress' ? 'bg-blue-500/10 text-blue-600 border border-blue-500/20' :
                'bg-muted text-muted-foreground border border-border'
              }`}>
                {task.status}
              </span>
              <span className="text-muted-foreground/60 flex items-center gap-1 font-medium">
                <Clock className="h-3 w-3" />
                {task.priority || 'Normal'}
              </span>
            </div>
          )}
        </div>
      </div>
      
      <div className="flex items-center gap-6 ml-4">
        <div className="hidden md:flex items-center -space-x-2 mr-4">
            <div className="h-8 w-8 rounded-full border-2 border-background bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-[10px] text-white font-bold shadow-sm opacity-80 group-hover:opacity-100 transition-opacity">US</div>
        </div>
        {task.due_date ? (
          <div className="hidden sm:flex flex-col items-end">
            <span className="text-xs font-semibold text-foreground/70">Vencimiento</span>
            <span className="flex items-center gap-1.5 text-sm font-medium">
              {(() => {
                const d = new Date(task.due_date);
                return isNaN(d.getTime()) ? 'Pendiente' : d.toLocaleDateString('es-CO', {day: 'numeric', month: 'short'});
              })()}
            </span>
          </div>
        ) : (
          <div className="hidden sm:text-muted-foreground/30 sm:flex items-center"><CalendarIcon className="h-4 w-4" /></div>
        )}
      </div>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-[400px] w-full text-center">
      <div className="relative mb-6">
        <div className="absolute inset-0 bg-primary/20 blur-2xl rounded-full" />
        <div className="h-24 w-24 rounded-full bg-gradient-to-tr from-muted to-muted/30 border border-white/10 dark:border-white/5 flex items-center justify-center shadow-2xl relative">
          <LayoutGrid className="h-10 w-10 text-muted-foreground/50" />
        </div>
      </div>
      <h3 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/60 mb-2">Workspace Despejado</h3>
      <p className="text-sm font-medium text-muted-foreground max-w-[250px]">{text}</p>
      <Button className="mt-8 rounded-full shadow-lg shadow-primary/20 px-8">Crear la primera tarea</Button>
    </div>
  );
}
