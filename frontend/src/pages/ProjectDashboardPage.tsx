import { useState, useEffect } from "react";
import { 
  LayoutDashboard, FolderPlus, ListPlus, Plus, RefreshCw, Search, 
  Filter, MoreVertical, ChevronRight, MessageSquare, 
  Calendar as CalendarIcon, User as UserIcon, CheckCircle2, Clock,
  LayoutGrid, CalendarDays, List as ListIcon
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
  { id: 'to do', label: 'To Do', color: 'border-slate-500' },
  { id: 'in progress', label: 'En Progreso', color: 'border-blue-500' },
  { id: 'review', label: 'Revisión', color: 'border-yellow-500' },
  { id: 'complete', label: 'Completado', color: 'border-green-500' }
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

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (selectedListId) fetchTasks(selectedListId);
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

  // Drag & Drop HTML5 nativo
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

  // Mapeo para el BigCalendar
  const calendarEvents = tasks.filter(t => t.due_date).map(t => ({
    id: t.id,
    title: t.title,
    start: new Date(t.due_date!),
    end: new Date(t.due_date!),
    resource: t,
  }));

  return (
    <div className="flex flex-col h-full space-y-6">
      {/* Header Panel */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Gestión de Proyectos</h1>
          <p className="text-muted-foreground">Administra tareas y sincroniza flujos colaborativos en tiempo real.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleSync} disabled={isSyncing} className="group">
            <RefreshCw className={`mr-2 h-4 w-4 ${isSyncing ? "animate-spin" : "group-hover:rotate-180 transition-transform duration-500"}`} />
            Sincronizar ClickUp
          </Button>
          <Button size="sm"><Plus className="mr-2 h-4 w-4" /> Nueva Tarea</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-250px)]">
        
        {/* Sidebar de Jerarquía (Explorador) */}
        <div className="lg:col-span-1 shadow-sm border rounded-xl bg-card/60 backdrop-blur-md overflow-hidden flex flex-col">
          <div className="p-4 border-b bg-muted/30 flex items-center justify-between">
            <span className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Explorador</span>
            <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-primary/20 hover:text-primary transition-colors">
              <FolderPlus className="h-4 w-4" />
            </Button>
          </div>
          
          <div className="flex-1 overflow-auto p-3 space-y-2">
            {workspaces.map(ws => (
              <div key={ws.id} className="space-y-1">
                <div 
                  className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/60 cursor-pointer text-sm font-semibold transition-colors"
                  onClick={() => toggleWorkspace(ws.id)}
                >
                  <div className="flex items-center gap-2">
                    <ChevronRight className={`h-4 w-4 text-muted-foreground transition-transform ${expandedWorkspaces.has(ws.id) ? "rotate-90" : ""}`} />
                    <LayoutDashboard className="h-4 w-4 text-primary" />
                    <span>{ws.name}</span>
                  </div>
                  <Plus className="h-3 w-3 opacity-0 hover:opacity-100 transition-opacity" />
                </div>
                
                {expandedWorkspaces.has(ws.id) && ws.folders.map(f => (
                  <div key={f.id} className="ml-4 space-y-1 relative before:absolute before:left-[-12px] before:top-0 before:h-full before:w-[1px] before:bg-border/50">
                    <div 
                      className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/50 cursor-pointer text-sm font-medium opacity-90"
                      onClick={() => toggleFolder(f.id)}
                    >
                      <div className="flex items-center gap-2">
                        <ChevronRight className={`h-3 w-3 text-muted-foreground transition-transform ${expandedFolders.has(f.id) ? "rotate-90" : ""}`} />
                        <span>{f.name}</span>
                      </div>
                      <Plus className="h-3 w-3 opacity-0 hover:opacity-100 transition-opacity text-primary" />
                    </div>

                    {expandedFolders.has(f.id) && f.lists.map(list => (
                      <div 
                        key={list.id}
                        className={`ml-5 flex items-center justify-between px-3 py-1.5 rounded-lg cursor-pointer text-[13px] transition-all ${selectedListId === list.id ? "bg-primary text-primary-foreground font-bold shadow-md" : "text-muted-foreground hover:bg-muted"}`}
                        onClick={() => setSelectedListId(list.id)}
                      >
                        <div className="flex items-center gap-2">
                          <span className={`w-1.5 h-1.5 rounded-full ${selectedListId === list.id ? 'bg-background' : 'bg-primary/50'}`} />
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

        {/* Content Area - Tabs para List / Kanban / Calendar */}
        <div className="lg:col-span-3 flex flex-col h-full overflow-hidden">
          <Tabs defaultValue="list" className="flex-1 flex flex-col h-full w-full">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input placeholder="Buscar tareas..." className="pl-9 bg-muted/20 border-border/50" />
              </div>
              <div className="flex flex-row items-center justify-between sm:justify-end gap-2 w-full sm:w-auto">
                <TabsList className="bg-muted/40 p-1">
                  <TabsTrigger value="list" className="flex items-center gap-2"><ListIcon className="h-4 w-4"/> Lista</TabsTrigger>
                  <TabsTrigger value="board" className="flex items-center gap-2"><LayoutGrid className="h-4 w-4"/> Tablero</TabsTrigger>
                  <TabsTrigger value="calendar" className="flex items-center gap-2"><CalendarDays className="h-4 w-4"/> Calendario</TabsTrigger>
                </TabsList>
                <Button variant="ghost" size="icon" className="text-muted-foreground"><Filter className="h-4 w-4" /></Button>
              </div>
            </div>

            <div className="flex-1 min-h-[500px] border border-border/40 rounded-xl overflow-hidden bg-background/50 backdrop-blur-sm relative">
              
              {/* TAB: LIST */}
              <TabsContent value="list" className="h-full m-0 p-4 overflow-y-auto space-y-3">
                {tasks.length === 0 ? (
                  <EmptyState text="No hay tareas en esta lista." />
                ) : tasks.map(task => (
                  <TaskRow key={task.id} task={task} onClick={() => setSelectedTask(task)} />
                ))}
              </TabsContent>

              {/* TAB: BOARD KANBAN */}
              <TabsContent value="board" className="h-full m-0 p-4 overflow-x-auto flex gap-4 items-start">
                  {BOARD_COLUMNS.map(col => (
                    <div 
                      key={col.id} 
                      className={`min-w-[300px] max-w-[300px] flex flex-col bg-muted/20 border-t-[3px] rounded-lg h-full max-h-full ${col.color}`}
                      onDragOver={e => e.preventDefault()}
                      onDrop={() => handleDrop(col.id)}
                    >
                      <div className="p-3 font-semibold text-sm flex items-center justify-between border-b border-border/50">
                        <span>{col.label}</span>
                        <Badge variant="secondary" className="px-2">{tasks.filter(t => t.status === col.id).length}</Badge>
                      </div>
                      <div className="flex-1 overflow-y-auto p-2 space-y-3">
                        {tasks.filter(t => t.status === col.id).map(task => (
                          <div 
                            key={task.id}
                            draggable
                            onDragStart={() => setDraggedTaskId(task.id)}
                            onClick={() => setSelectedTask(task)}
                            className="bg-card border border-border/60 hover:border-primary/50 rounded-md p-3 shadow-sm cursor-grab active:cursor-grabbing hover:shadow-md transition-all"
                          >
                            <h4 className="font-medium text-sm mb-2 leading-tight">{task.title}</h4>
                            <div className="flex items-center justify-between text-xs text-muted-foreground">
                              <span className="bg-muted px-1.5 rounded">{task.priority || 'Normal'}</span>
                              {task.due_date && <span className="flex items-center gap-1"><CalendarIcon className="h-3 w-3"/> {new Date(task.due_date).toLocaleDateString()}</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                      <div className="p-2 border-t border-border/50">
                        <Button variant="ghost" className="w-full h-8 text-xs text-muted-foreground"><Plus className="h-3 w-3 mr-1"/> Añadir Tarea</Button>
                      </div>
                    </div>
                  ))}
              </TabsContent>

              {/* TAB: CALENDAR */}
              <TabsContent value="calendar" className="h-full m-0 p-4">
                <style>{`
                  .rbc-calendar { font-family: inherit; }
                  .rbc-event { background-color: hsl(var(--primary)); border-radius: 6px; padding: 2px 5px; font-size: 12px; }
                  .rbc-today { background-color: hsl(var(--primary)/0.05); }
                  .rbc-toolbar button { color: hsl(var(--foreground)); }
                  .rbc-toolbar button.rbc-active { background-color: hsl(var(--primary)/0.1); box-shadow: none; }
                `}</style>
                <div className="h-full bg-card/40 rounded-xl">
                  <BigCalendar
                    localizer={localizer}
                    events={calendarEvents}
                    startAccessor="start"
                    endAccessor="end"
                    style={{ height: '100%' }}
                    onSelectEvent={(e: any) => setSelectedTask(e.resource)}
                    messages={{ today: "Hoy", previous: "Anterior", next: "Siguiente", month: "Mes", week: "Semana", day: "Día" }}
                  />
                </div>
              </TabsContent>

            </div>
          </Tabs>
        </div>
      </div>
      
      {/* Componente Modal Sheet para Detalles y Modificadores de la Tarea */}
      <TaskDrawer 
        task={selectedTask}
        open={!!selectedTask}
        onOpenChange={(open) => !open && setSelectedTask(null)}
        onTaskUpdate={(t) => setTasks(prev => prev.map(pt => pt.id === t.id ? t : pt))}
      />
    </div>
  );
}

// Subcomponente de fila de tabla limpia
function TaskRow({ task, onClick }: { task: TaskType; onClick: () => void }) {
  return (
    <Card 
      onClick={onClick}
      className={`border-l-4 hover:shadow border border-border/50 transition-all cursor-pointer bg-card/60 ${
        task.priority === 'urgent' ? 'border-l-red-500' : 
        task.priority === 'high' ? 'border-l-orange-500' : 
        task.priority === 'normal' ? 'border-l-blue-500' : 'border-l-primary'
      }`}
    >
      <CardContent className="p-3 px-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <CheckCircle2 className={`h-4 w-4 ${task.status === 'complete' ? 'text-green-500' : 'text-muted-foreground'}`} />
            <div>
              <h3 className="font-semibold text-sm">{task.title}</h3>
              <div className="flex items-center gap-3 mt-1">
                <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${task.status === 'complete' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' : 'bg-muted text-muted-foreground'}`}>
                  {task.status}
                </span>
                {task.due_date && (
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <CalendarIcon className="h-3 w-3" /> {new Date(task.due_date).toLocaleDateString()}
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3 text-muted-foreground">
            <UserIcon className="h-4 w-4 opacity-50" />
            <MessageSquare className="h-4 w-4 opacity-50" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground py-20">
      <CheckCircle2 className="h-16 w-16 opacity-10" />
      <p className="font-medium text-sm">{text}</p>
    </div>
  );
}
