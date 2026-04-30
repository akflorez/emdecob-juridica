import { useState, useEffect, useMemo } from "react";
import { 
  LayoutDashboard, FolderPlus, ListPlus, Plus, RefreshCw, Search, 
  Filter, MoreVertical, ChevronRight, MessageSquare, 
  Calendar as CalendarIcon, User as UserIcon, CheckCircle2, Clock,
  LayoutGrid, CalendarDays, List as ListIcon, Zap, PlayCircle, Lock,
  ChevronDown, Calendar, PieChart as PieIcon, BarChart as BarIcon, 
  TrendingUp, Users, Activity
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  getWorkspaces, getTasks, importClickUp, updateTask, getUsers,
  type Workspace, type Task as TaskType, type User
} from "@/services/api";
import { TaskDrawer } from "@/components/TaskDrawer";
import { Calendar as BigCalendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { format, subDays, startOfMonth, endOfMonth, isToday, isYesterday, isWithinInterval, startOfDay, endOfDay } from 'date-fns';
import { es } from 'date-fns/locale';
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip as ChartTooltip, 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend 
} from 'recharts';

// Español para el calendario
moment.locale('es');
const localizer = momentLocalizer(moment);

const BOARD_COLUMNS = [
  { id: 'to do', label: 'To Do', color: 'bg-slate-100 text-slate-700 dark:bg-slate-900 dark:text-slate-300', dot: 'bg-slate-400' },
  { id: 'in progress', label: 'En Progreso', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400', dot: 'bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]' },
  { id: 'review', label: 'Revisión', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-400', dot: 'bg-yellow-400 shadow-[0_0_8px_rgba(250,204,21,0.5)]' },
  { id: 'complete', label: 'Completado', color: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400', dot: 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' }
];

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function ProjectDashboardPage() {
  const [isSyncing, setIsSyncing] = useState(false);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [tasks, setTasks] = useState<TaskType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedListId, setSelectedListId] = useState<number | null>(null);
  const [expandedWorkspaces, setExpandedWorkspaces] = useState<Set<number>>(new Set());
  const [expandedFolders, setExpandedFolders] = useState<Set<number>>(new Set());
  
  const [selectedTask, setSelectedTask] = useState<TaskType | null>(null);
  const [draggedTaskId, setDraggedTaskId] = useState<number | null>(null);
  
  // Filtros
  const [searchTerm, setSearchTerm] = useState("");
  const [dateFilterType, setDateFilterType] = useState<string>("month");
  const [dateRange, setDateRange] = useState({ 
    start: format(startOfMonth(new Date()), 'yyyy-MM-dd'), 
    end: format(endOfMonth(new Date()), 'yyyy-MM-dd') 
  });
  const [responsibleFilter, setResponsibleFilter] = useState<string>("all");
  const [clickupToken, setClickupToken] = useState<string>(localStorage.getItem('clickup_token') || '');

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    fetchTasks(selectedListId ?? undefined);
  }, [selectedListId]);

  const fetchInitialData = async () => {
    setIsLoading(true);
    try {
      const wsData = await getWorkspaces();
      setWorkspaces(wsData);
      if (wsData.length > 0) {
        setExpandedWorkspaces(new Set([wsData[0].id]));
        if (wsData[0].folders.length > 0) {
          setExpandedFolders(new Set([wsData[0].folders[0].id]));
        }
      }
      await fetchTasks(undefined);
    } catch (error) {
      toast.error("Error al cargar proyectos");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchTasks = async (listId?: number) => {
    try {
      const taskData = await getTasks({ list_id: listId });
      setTasks(Array.isArray(taskData) ? taskData : []);
    } catch (error) {
      toast.error("Error al cargar tareas");
      setTasks([]);
    }
  };

  const handleSync = async () => {
    const token = prompt("Ingresa tu ClickUp API Token:", clickupToken);
    if (!token) return;
    setClickupToken(token);
    localStorage.setItem('clickup_token', token);
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

  const handleDateFilterChange = (val: string) => {
    setDateFilterType(val);
    const today = new Date();
    let start = "";
    let end = "";

    switch(val) {
      case 'today': start = end = format(today, 'yyyy-MM-dd'); break;
      case 'yesterday': start = end = format(subDays(today, 1), 'yyyy-MM-dd'); break;
      case '7d': start = format(subDays(today, 7), 'yyyy-MM-dd'); end = format(today, 'yyyy-MM-dd'); break;
      case '30d': start = format(subDays(today, 30), 'yyyy-MM-dd'); end = format(today, 'yyyy-MM-dd'); break;
      case 'month': start = format(startOfMonth(today), 'yyyy-MM-dd'); end = format(endOfMonth(today), 'yyyy-MM-dd'); break;
      case 'all': start = ""; end = ""; break;
    }
    setDateRange({ start, end });
  };

  const filteredTasks = useMemo(() => {
    return (tasks || []).filter(t => {
      if (searchTerm) {
        const search = searchTerm.toLowerCase();
        if (!t.title.toLowerCase().includes(search) && !t.description?.toLowerCase().includes(search)) return false;
      }
      if (responsibleFilter !== "all" && t.assignee_name !== responsibleFilter) return false;
      if (dateFilterType === "all") return true;
      if (!t.due_date) return true;
      const d = new Date(t.due_date);
      if (dateRange.start && d < startOfDay(new Date(dateRange.start))) return false;
      if (dateRange.end && d > endOfDay(new Date(dateRange.end))) return false;
      return true;
    });
  }, [tasks, searchTerm, responsibleFilter, dateRange, dateFilterType]);

  const parentTasks = filteredTasks.filter(t => !t.parent_id);
  const subtasksMap = filteredTasks.reduce((acc, t) => {
    if (t.parent_id) {
       if (!acc[t.parent_id]) acc[t.parent_id] = [];
       acc[t.parent_id].push(t);
    }
    return acc;
  }, {} as Record<number, TaskType[]>);

  // Datos para Gráficos
  const statsByAssignee = useMemo(() => {
    const map: Record<string, number> = {};
    filteredTasks.forEach(t => {
      const name = t.assignee_name || "Sin Asignar";
      map[name] = (map[name] || 0) + 1;
    });
    return Object.entries(map).map(([name, value]) => ({ name, value }));
  }, [filteredTasks]);

  const statsByStatus = useMemo(() => {
    return BOARD_COLUMNS.map(col => ({
      name: col.label,
      value: filteredTasks.filter(t => (t.status || '').toLowerCase() === col.id).length
    }));
  }, [filteredTasks]);

  const calendarEvents = useMemo(() => {
    return filteredTasks
      .filter(t => t.due_date && !isNaN(new Date(t.due_date).getTime()))
      .map(t => ({
        id: t.id,
        title: (t.title || 'Sin Título') + (t.status === 'complete' ? ' ✅' : ''),
        start: new Date(t.due_date!),
        end: new Date(t.due_date!),
        resource: t,
      }));
  }, [filteredTasks]);

  return (
    <div className="flex flex-col h-full bg-[#0d0e12] text-slate-200 overflow-hidden relative">
      {/* Premium Glows */}
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-primary/10 rounded-full blur-[120px] pointer-events-none" />
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 py-4 px-6 border-b border-white/5 bg-black/40 backdrop-blur-xl z-20">
        <div className="flex items-center gap-4">
          <div className="p-2.5 bg-gradient-to-br from-primary to-blue-600 rounded-xl shadow-xl shadow-primary/20">
            <LayoutDashboard className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-black tracking-tight text-white flex items-center gap-2">
              EMDECOB JURÍDICO <Badge variant="secondary" className="bg-primary/20 text-primary border-primary/20 text-[10px]">PRO</Badge>
            </h1>
            <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Advanced Portfolio Management</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
           <Button variant="ghost" onClick={handleSync} disabled={isSyncing} className="rounded-lg h-9 bg-white/5 hover:bg-white/10 text-xs border border-white/5">
             <RefreshCw className={`mr-2 h-3.5 w-3.5 ${isSyncing ? "animate-spin" : ""}`} /> Sincronizar
           </Button>
           <Button onClick={() => setSelectedTask({ title: '', status: 'to do', priority: 'normal', list_id: selectedListId } as any)} className="rounded-lg h-9 bg-primary hover:bg-primary/90 text-white font-bold text-xs px-5 shadow-lg shadow-primary/20">
             <Plus className="mr-2 h-4 w-4" /> Nueva Tarea
           </Button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Navigation Sidebar */}
        <div className="w-64 flex flex-col border-r border-white/5 bg-black/20 backdrop-blur-md">
           <div className="p-4">
             <div className="relative group">
               <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
               <Input placeholder="Buscar lista..." className="pl-9 h-9 bg-white/5 border-white/10 rounded-lg text-xs" />
             </div>
           </div>
           <div className="flex-1 overflow-y-auto px-2 space-y-1 custom-scrollbar">
              {workspaces.map(ws => (
                <div key={ws.id} className="space-y-0.5">
                   <div className="flex items-center gap-2 p-2 rounded-lg hover:bg-white/5 cursor-pointer group" onClick={() => {
                     const n = new Set(expandedWorkspaces);
                     if (n.has(ws.id)) n.delete(ws.id); else n.add(ws.id);
                     setExpandedWorkspaces(n);
                   }}>
                     <ChevronDown className={`h-3.5 w-3.5 text-muted-foreground transition-transform ${expandedWorkspaces.has(ws.id) ? "" : "-rotate-90"}`} />
                     <span className="text-[11px] font-black uppercase text-slate-400 group-hover:text-primary transition-colors">{ws.name}</span>
                   </div>
                   {expandedWorkspaces.has(ws.id) && ws.folders.map(f => (
                     <div key={f.id} className="ml-3 space-y-0.5">
                        <div className="flex items-center gap-2 p-2 rounded-lg hover:bg-white/5 cursor-pointer group" onClick={() => {
                          const n = new Set(expandedFolders);
                          if (n.has(f.id)) n.delete(f.id); else n.add(f.id);
                          setExpandedFolders(n);
                        }}>
                          <ChevronDown className={`h-3 w-3 text-muted-foreground transition-transform ${expandedFolders.has(f.id) ? "" : "-rotate-90"}`} />
                          <span className="text-[11px] font-bold text-slate-500 group-hover:text-slate-300">{f.name}</span>
                        </div>
                        {expandedFolders.has(f.id) && f.lists.map(list => (
                          <div 
                            key={list.id} 
                            onClick={() => setSelectedListId(list.id)}
                            className={`ml-5 p-2 rounded-lg cursor-pointer text-[11px] flex items-center justify-between group transition-all ${selectedListId === list.id ? "bg-primary/10 text-primary border border-primary/20 shadow-lg shadow-primary/5" : "text-slate-500 hover:text-slate-300 hover:bg-white/5"}`}
                          >
                             <div className="flex items-center gap-2">
                               <div className={`h-1.5 w-1.5 rounded-full ${selectedListId === list.id ? 'bg-primary animate-pulse' : 'bg-slate-700'}`} />
                               {list.name}
                             </div>
                             {selectedListId === list.id && <Zap className="h-3 w-3" />}
                          </div>
                        ))}
                     </div>
                   ))}
                </div>
              ))}
           </div>
        </div>

        {/* Main Console */}
        <div className="flex-1 flex flex-col overflow-hidden">
           <Tabs defaultValue="board" className="flex-1 flex flex-col overflow-hidden">
              <div className="h-14 flex items-center justify-between px-6 border-b border-white/5 bg-black/20">
                 <TabsList className="bg-white/5 p-1 rounded-xl h-9 border border-white/5">
                   <TabsTrigger value="board" className="rounded-lg text-[10px] font-bold uppercase tracking-widest px-4 data-[state=active]:bg-primary data-[state=active]:text-white">Tablero</TabsTrigger>
                   <TabsTrigger value="list" className="rounded-lg text-[10px] font-bold uppercase tracking-widest px-4">Lista</TabsTrigger>
                   <TabsTrigger value="calendar" className="rounded-lg text-[10px] font-bold uppercase tracking-widest px-4">Agenda</TabsTrigger>
                   <TabsTrigger value="stats" className="rounded-lg text-[10px] font-bold uppercase tracking-widest px-4">Panel Control</TabsTrigger>
                 </TabsList>

                 <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1.5 bg-white/5 p-1 rounded-xl border border-white/5">
                       <Select value={dateFilterType} onValueChange={handleDateFilterChange}>
                         <SelectTrigger className="w-[120px] h-7 text-[10px] border-none bg-transparent font-black uppercase text-primary">
                           <Calendar className="h-3 w-3 mr-2" />
                           <SelectValue />
                         </SelectTrigger>
                         <SelectContent className="bg-slate-900 border-white/10 text-white">
                           <SelectItem value="today">Hoy</SelectItem>
                           <SelectItem value="yesterday">Ayer</SelectItem>
                           <SelectItem value="7d">7 Días</SelectItem>
                           <SelectItem value="30d">30 Días</SelectItem>
                           <SelectItem value="month">Este Mes</SelectItem>
                           <SelectItem value="all">Todo</SelectItem>
                         </SelectContent>
                       </Select>
                    </div>
                    <Select value={responsibleFilter} onValueChange={setResponsibleFilter}>
                       <SelectTrigger className="w-[140px] h-7 text-[10px] bg-white/5 border-white/10 rounded-lg uppercase font-bold">
                         <Users className="h-3 w-3 mr-2" />
                         <SelectValue placeholder="Responsable" />
                       </SelectTrigger>
                       <SelectContent className="bg-slate-900 border-white/10 text-white">
                         <SelectItem value="all">Todos</SelectItem>
                         {Array.from(new Set(tasks.map(t => t.assignee_name).filter(Boolean))).map(name => (
                           <SelectItem key={name} value={name!}>{name}</SelectItem>
                         ))}
                       </SelectContent>
                    </Select>
                 </div>
              </div>

              <div className="flex-1 overflow-hidden relative">
                 {/* TAB: TABLERO (KANBAN EXPERTO) */}
                 <TabsContent value="board" className="h-full m-0 p-6 flex gap-6 overflow-x-auto custom-scrollbar">
                    {BOARD_COLUMNS.map(col => (
                      <div key={col.id} className="min-w-[320px] flex flex-col bg-white/[0.02] border border-white/5 rounded-3xl p-4 shadow-2xl relative group/col">
                        <div className="flex items-center justify-between mb-6 px-2">
                           <div className="flex items-center gap-2">
                              <div className={`h-2.5 w-2.5 rounded-full ${col.dot}`} />
                              <h3 className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400">{col.label}</h3>
                           </div>
                           <Badge variant="outline" className="bg-white/5 border-white/10 text-[10px] font-mono text-slate-500">{filteredTasks.filter(t => t.status === col.id).length}</Badge>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-4 px-1 custom-scrollbar">
                           {parentTasks.filter(t => t.status === col.id).map(task => (
                             <Card key={task.id} className="bg-[#1a1c23] border-white/5 hover:border-primary/40 hover:translate-y-[-2px] transition-all duration-300 cursor-pointer shadow-lg group overflow-hidden" onClick={() => setSelectedTask(task)}>
                               <div className="p-4 relative">
                                  <div className="flex justify-between items-start mb-3">
                                     <Badge variant="secondary" className="text-[9px] uppercase tracking-wider bg-white/5 border-white/10 text-slate-400">{task.priority || 'Normal'}</Badge>
                                     {subtasksMap[task.id] && <div className="text-[9px] text-primary flex items-center gap-1 font-bold"><ListPlus className="h-3 w-3"/> {subtasksMap[task.id].length}</div>}
                                  </div>
                                  <h4 className="text-[13px] font-bold text-slate-200 leading-snug line-clamp-2 mb-4 group-hover:text-primary transition-colors">{task.title}</h4>
                                  <div className="flex items-center justify-between border-t border-white/5 pt-3">
                                     <div className="flex items-center gap-2">
                                        <div className="h-5 w-5 rounded-full bg-primary/20 flex items-center justify-center text-[10px] font-black text-primary border border-primary/20">{(task.assignee_name || 'US')[0]}</div>
                                        <span className="text-[10px] font-bold text-slate-500">{task.assignee_name || 'Sin Asignar'}</span>
                                     </div>
                                     {task.due_date && <span className="text-[10px] font-black text-slate-400 flex items-center gap-1"><Clock className="h-3 w-3"/> {format(new Date(task.due_date), 'd MMM')}</span>}
                                  </div>
                               </div>
                             </Card>
                           ))}
                        </div>
                      </div>
                    ))}
                 </TabsContent>

                 {/* TAB: LISTA */}
                 <TabsContent value="list" className="h-full m-0 p-6 overflow-y-auto space-y-2">
                    {parentTasks.map(t => (
                      <div key={t.id} className="group flex items-center justify-between p-4 bg-white/[0.02] border border-white/5 rounded-2xl hover:bg-white/[0.04] hover:border-primary/20 transition-all cursor-pointer" onClick={() => setSelectedTask(t)}>
                         <div className="flex items-center gap-4">
                            <div className={`h-3 w-3 rounded-full border-2 ${t.status === 'complete' ? 'bg-green-500 border-green-500/30' : 'border-slate-700'}`} />
                            <div>
                               <div className="text-[13px] font-bold text-slate-200 group-hover:text-primary transition-colors">{t.title}</div>
                               <div className="text-[10px] text-slate-500 flex items-center gap-3 mt-1">
                                  <span className="flex items-center gap-1"><Users className="h-3 w-3"/> {t.assignee_name || 'Sin asignar'}</span>
                                  {t.due_date && <span className="flex items-center gap-1"><Calendar className="h-3 w-3"/> {format(new Date(t.due_date), 'd MMM, yyyy')}</span>}
                               </div>
                            </div>
                         </div>
                         <Badge className={`uppercase text-[9px] font-black tracking-widest ${t.status === 'complete' ? 'bg-green-500/10 text-green-500 border-green-500/20' : 'bg-primary/10 text-primary border-primary/20'}`}>{t.status}</Badge>
                      </div>
                    ))}
                 </TabsContent>

                 {/* TAB: AGENDA */}
                 <TabsContent value="calendar" className="h-full m-0 p-6">
                    <div className="h-full bg-white/[0.02] rounded-3xl border border-white/5 p-6 shadow-2xl relative overflow-hidden">
                       <style>{`
                         .rbc-calendar { color: #94a3b8; }
                         .rbc-month-view, .rbc-header { border-color: rgba(255,255,255,0.05) !important; }
                         .rbc-off-range-bg { background: rgba(0,0,0,0.2); }
                         .rbc-event { background: #3b82f6 !important; border: none; font-size: 10px; font-weight: 800; border-radius: 6px; }
                         .rbc-today { background: rgba(59,130,246,0.05); }
                       `}</style>
                       <BigCalendar
                         localizer={localizer}
                         events={calendarEvents}
                         startAccessor="start"
                         endAccessor="end"
                         style={{ height: '100%' }}
                         onSelectEvent={(e: any) => setSelectedTask(e.resource)}
                         messages={{ today: "Hoy", previous: "Back", next: "Next", month: "Mes", week: "Semana", day: "Día" }}
                       />
                    </div>
                 </TabsContent>

                 {/* TAB: PANEL DE CONTROL (CLICKUP STYLE) */}
                 <TabsContent value="stats" className="h-full m-0 p-8 overflow-y-auto space-y-8 custom-scrollbar bg-black/40">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                       {[
                         { label: 'Sin Asignar', count: tasks.filter(t => !t.assignee_id).length, icon: Users, color: 'text-slate-400', bg: 'bg-slate-400/10' },
                         { label: 'En Curso', count: tasks.filter(t => t.status === 'in progress').length, icon: Activity, color: 'text-blue-500', bg: 'bg-blue-500/10' },
                         { label: 'Completadas', count: tasks.filter(t => t.status === 'complete').length, icon: CheckCircle2, color: 'text-green-500', bg: 'bg-green-500/10' }
                       ].map((card, i) => (
                         <Card key={i} className="bg-white/[0.02] border-white/5 shadow-2xl overflow-hidden relative group">
                            <div className={`absolute top-0 right-0 w-24 h-24 ${card.bg} rounded-full -mr-12 -mt-12 blur-3xl`} />
                            <CardContent className="p-8">
                               <div className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-500 mb-4">{card.label}</div>
                               <div className="flex items-center justify-between">
                                  <div className={`text-5xl font-black ${card.color}`}>{card.count}</div>
                                  <card.icon className={`h-10 w-10 ${card.color} opacity-20 group-hover:opacity-100 transition-all duration-500`} />
                               </div>
                               <div className="mt-4 text-[10px] font-bold text-slate-600 uppercase tracking-widest">Tareas totales en este estado</div>
                            </CardContent>
                         </Card>
                       ))}
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                       {/* Chart: Total de tareas por persona */}
                       <Card className="bg-[#13141a] border-white/5 shadow-2xl">
                          <CardHeader className="border-b border-white/5">
                             <CardTitle className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400 flex items-center gap-2">
                                <PieIcon className="h-4 w-4 text-primary" /> Total tareas por persona asignada
                             </CardTitle>
                          </CardHeader>
                          <CardContent className="p-6 h-[400px]">
                             <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                   <Pie
                                      data={statsByAssignee}
                                      cx="50%"
                                      cy="50%"
                                      innerRadius={80}
                                      outerRadius={120}
                                      paddingAngle={5}
                                      dataKey="value"
                                      stroke="none"
                                   >
                                      {statsByAssignee.map((entry, index) => (
                                         <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                      ))}
                                   </Pie>
                                   <ChartTooltip 
                                      contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                                      itemStyle={{ fontSize: '12px', fontWeight: 'bold' }}
                                   />
                                   <Legend verticalAlign="bottom" height={36}/>
                                </PieChart>
                             </ResponsiveContainer>
                          </CardContent>
                       </Card>

                       {/* Chart: Tareas abiertas por persona */}
                       <Card className="bg-[#13141a] border-white/5 shadow-2xl">
                          <CardHeader className="border-b border-white/5">
                             <CardTitle className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400 flex items-center gap-2">
                                <BarIcon className="h-4 w-4 text-blue-500" /> Tareas por estado actual
                             </CardTitle>
                          </CardHeader>
                          <CardContent className="p-6 h-[400px]">
                             <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={statsByStatus}>
                                   <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                                   <XAxis 
                                      dataKey="name" 
                                      axisLine={false} 
                                      tickLine={false} 
                                      tick={{ fill: '#64748b', fontSize: 10, fontWeight: 'bold' }} 
                                   />
                                   <YAxis 
                                      axisLine={false} 
                                      tickLine={false} 
                                      tick={{ fill: '#64748b', fontSize: 10 }} 
                                   />
                                   <ChartTooltip 
                                      cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                                      contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                                   />
                                   <Bar dataKey="value" radius={[6, 6, 0, 0]} barSize={40}>
                                      {statsByStatus.map((entry, index) => (
                                         <Cell key={`cell-${index}`} fill={entry.name === 'Completado' ? '#10b981' : entry.name === 'En Progreso' ? '#3b82f6' : '#64748b'} />
                                      ))}
                                   </Bar>
                                </BarChart>
                             </ResponsiveContainer>
                          </CardContent>
                       </Card>
                    </div>

                    {/* Workload Section */}
                    <div className="grid grid-cols-1 lg:grid-cols-1 gap-8">
                       <Card className="bg-[#13141a] border-white/5 shadow-2xl overflow-hidden">
                          <CardHeader className="border-b border-white/5 bg-white/[0.02]">
                             <CardTitle className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400">Rendimiento Detallado por Equipo</CardTitle>
                          </CardHeader>
                          <CardContent className="p-0">
                             <div className="overflow-x-auto">
                                <table className="w-full text-left text-[11px]">
                                   <thead className="bg-white/[0.01] text-slate-500 uppercase tracking-widest font-black border-b border-white/5">
                                      <tr>
                                         <th className="px-6 py-4">Usuario</th>
                                         <th className="px-6 py-4">Total</th>
                                         <th className="px-6 py-4">Completadas</th>
                                         <th className="px-6 py-4">Eficiencia</th>
                                         <th className="px-6 py-4">Carga actual</th>
                                      </tr>
                                   </thead>
                                   <tbody className="divide-y divide-white/5">
                                      {Array.from(new Set(tasks.map(t => t.assignee_name).filter(Boolean))).map(name => {
                                         const userTasks = tasks.filter(t => t.assignee_name === name);
                                         const done = userTasks.filter(t => t.status === 'complete').length;
                                         const open = userTasks.length - done;
                                         const pct = userTasks.length > 0 ? Math.round((done / userTasks.length) * 100) : 0;
                                         return (
                                            <tr key={name!} className="hover:bg-white/[0.02] transition-colors group">
                                               <td className="px-6 py-4 flex items-center gap-3">
                                                  <div className="h-7 w-7 rounded-full bg-primary/20 flex items-center justify-center font-bold text-primary border border-primary/20">{name![0]}</div>
                                                  <span className="font-bold text-slate-300 group-hover:text-primary transition-colors">{name}</span>
                                               </td>
                                               <td className="px-6 py-4 font-mono text-slate-500">{userTasks.length}</td>
                                               <td className="px-6 py-4 text-green-500 font-bold">{done}</td>
                                               <td className="px-6 py-4">
                                                  <div className="flex items-center gap-3">
                                                     <div className="h-1.5 flex-1 bg-white/5 rounded-full overflow-hidden">
                                                        <div className="h-full bg-primary" style={{ width: `${pct}%` }} />
                                                     </div>
                                                     <span className="font-black text-slate-400">{pct}%</span>
                                                  </div>
                                               </td>
                                               <td className="px-6 py-4">
                                                  <Badge variant="outline" className={`${open > 10 ? 'bg-red-500/10 text-red-500' : 'bg-blue-500/10 text-blue-500'} border-none`}>{open} Abiertas</Badge>
                                               </td>
                                            </tr>
                                         );
                                      })}
                                   </tbody>
                                </table>
                             </div>
                          </CardContent>
                       </Card>
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
        }}
        clickupToken={clickupToken}
      />
    </div>
  );
}
