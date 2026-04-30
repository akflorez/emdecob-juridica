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

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316', '#14b8a6', '#6366f1'];

export default function ProjectDashboardPage() {
  const [isSyncing, setIsSyncing] = useState(false);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [tasks, setTasks] = useState<TaskType[]>([]);
  const [users, setUsers] = useState<User[]>([]); // RESTORED
  const [isLoading, setIsLoading] = useState(true);
  const [selectedListId, setSelectedListId] = useState<number | null>(null);
  const [expandedWorkspaces, setExpandedWorkspaces] = useState<Set<number>>(new Set());
  const [expandedFolders, setExpandedFolders] = useState<Set<number>>(new Set());
  
  const [selectedTask, setSelectedTask] = useState<TaskType | null>(null);
  
  // Filtros
  const [searchTerm, setSearchTerm] = useState("");
  const [dateFilterType, setDateFilterType] = useState<string>("all"); // DEFAULT TO ALL TO SEE TASKS
  const [dateRange, setDateRange] = useState({ 
    start: "", 
    end: "" 
  });
  const [responsibleFilter, setResponsibleFilter] = useState<string>("all");
  const [clickupToken, setClickupToken] = useState<string>(localStorage.getItem('clickup_token') || '');

  useEffect(() => {
    fetchInitialData();
    getUsers().then(setUsers).catch(console.error); // RESTORED
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
      if (!t.due_date) return true; // Show dateless tasks always
      
      const d = new Date(t.due_date);
      if (dateRange.start && d < startOfDay(new Date(dateRange.start))) return false;
      if (dateRange.end && d > endOfDay(new Date(dateRange.end))) return false;
      return true;
    });
  }, [tasks, searchTerm, responsibleFilter, dateRange, dateFilterType]);

  const dynamicBoardColumns = useMemo(() => {
    const statuses = Array.from(new Set(filteredTasks.map(t => t.status || 'ABIERTO')));
    statuses.sort((a, b) => {
      const aLower = (a || '').toLowerCase();
      const bLower = (b || '').toLowerCase();
      if (aLower === 'abierto' || aLower === 'to do' || aLower === 'open') return -1;
      if (aLower === 'completado' || aLower === 'complete' || aLower === 'closed') return 1;
      return 0;
    });

    return statuses.map((s, idx) => {
      const sLower = (s || '').toLowerCase();
      let dotColor = COLORS[idx % COLORS.length];
      if (sLower.includes('abierto') || sLower.includes('todo')) dotColor = '#94a3b8';
      if (sLower.includes('proceso') || sLower.includes('curso')) dotColor = '#3b82f6';
      if (sLower.includes('retiro')) dotColor = '#ef4444';
      if (sLower.includes('completado') || sLower.includes('finalizado')) dotColor = '#10b981';

      return {
        id: s,
        label: (s || 'SIN ESTADO').toUpperCase(),
        dot: dotColor
      };
    });
  }, [filteredTasks]);

  const parentTasks = filteredTasks.filter(t => !t.parent_id);
  const subtasksMap = filteredTasks.reduce((acc, t) => {
    if (t.parent_id) {
       if (!acc[t.parent_id]) acc[t.parent_id] = [];
       acc[t.parent_id].push(t);
    }
    return acc;
  }, {} as Record<number, TaskType[]>);

  const statsByAssignee = useMemo(() => {
    const map: Record<string, number> = {};
    filteredTasks.forEach(t => {
      const name = t.assignee_name || "Sin Asignar";
      map[name] = (map[name] || 0) + 1;
    });
    return Object.entries(map).map(([name, value]) => ({ name, value }));
  }, [filteredTasks]);

  const statsByStatus = useMemo(() => {
    return dynamicBoardColumns.map(col => ({
      name: col.label,
      value: filteredTasks.filter(t => (t.status || 'ABIERTO') === col.id).length,
      color: col.dot
    }));
  }, [filteredTasks, dynamicBoardColumns]);

  const calendarEvents = useMemo(() => {
    return filteredTasks
      .filter(t => t.due_date && !isNaN(new Date(t.due_date).getTime()))
      .map(t => ({
        id: t.id,
        title: (t.title || 'Sin Título') + ((t.status || '').toLowerCase().includes('completado') ? ' ✅' : ''),
        start: new Date(t.due_date!),
        end: new Date(t.due_date!),
        resource: t,
      }));
  }, [filteredTasks]);

  return (
    <div className="flex flex-col h-full bg-[#0d0e12] text-slate-200 overflow-hidden relative">
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-primary/10 rounded-full blur-[120px] pointer-events-none" />
      
      {/* Header */}
      <div className="flex items-center justify-between py-4 px-6 border-b border-white/5 bg-black/40 backdrop-blur-xl z-20">
        <div className="flex items-center gap-4">
          <div className="p-2.5 bg-gradient-to-br from-primary to-blue-600 rounded-xl shadow-xl shadow-primary/20">
            <LayoutDashboard className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-black tracking-tight text-white flex items-center gap-2">
              EMDECOB JURÍDICO <Badge variant="secondary" className="bg-primary/20 text-primary border-primary/20 text-[10px]">EXPERT</Badge>
            </h1>
            <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Master Workflow Engine</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
           <Button variant="ghost" onClick={handleSync} disabled={isSyncing} className="rounded-lg h-9 bg-white/5 hover:bg-white/10 text-xs border border-white/5 px-4 font-bold">
             <RefreshCw className={`mr-2 h-3.5 w-3.5 ${isSyncing ? "animate-spin" : ""}`} /> Sincronizar ClickUp
           </Button>
           <Button onClick={() => setSelectedTask({ title: '', status: 'ABIERTO', priority: 'normal', list_id: selectedListId } as any)} className="rounded-lg h-9 bg-primary hover:bg-primary/90 text-white font-black text-[11px] px-6 shadow-lg shadow-primary/20 uppercase tracking-wider">
             <Plus className="mr-2 h-4 w-4" /> Nueva Tarea
           </Button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 flex flex-col border-r border-white/5 bg-black/40">
           <div className="p-4">
             <div className="relative group">
               <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
               <Input placeholder="Explorar procesos..." className="pl-9 h-9 bg-white/5 border-white/10 rounded-lg text-xs" />
             </div>
           </div>
           <div className="flex-1 overflow-y-auto px-2 space-y-1 custom-scrollbar">
              {workspaces.map(ws => (
                <div key={ws.id}>
                   <div className="flex items-center gap-2 p-2 rounded-lg hover:bg-white/5 cursor-pointer" onClick={() => {
                     const n = new Set(expandedWorkspaces);
                     if (n.has(ws.id)) n.delete(ws.id); else n.add(ws.id);
                     setExpandedWorkspaces(n);
                   }}>
                     <ChevronDown className={`h-3.5 w-3.5 text-slate-600 transition-transform ${expandedWorkspaces.has(ws.id) ? "" : "-rotate-90"}`} />
                     <span className="text-[10px] font-black uppercase text-slate-500 tracking-widest">{ws.name}</span>
                   </div>
                   {expandedWorkspaces.has(ws.id) && ws.folders.map(f => (
                     <div key={f.id} className="ml-3">
                        <div className="flex items-center gap-2 p-2 rounded-lg hover:bg-white/5 cursor-pointer" onClick={() => {
                          const n = new Set(expandedFolders);
                          if (n.has(f.id)) n.delete(f.id); else n.add(f.id);
                          setExpandedFolders(n);
                        }}>
                          <ChevronDown className={`h-3 w-3 text-slate-600 transition-transform ${expandedFolders.has(f.id) ? "" : "-rotate-90"}`} />
                          <span className="text-[11px] font-bold text-slate-400">{f.name}</span>
                        </div>
                        {expandedFolders.has(f.id) && f.lists.map(list => (
                          <div 
                            key={list.id} 
                            onClick={() => setSelectedListId(list.id)}
                            className={`ml-5 p-2 rounded-lg cursor-pointer text-[11px] transition-all ${selectedListId === list.id ? "bg-primary/20 text-primary font-bold" : "text-slate-500 hover:text-slate-300"}`}
                          >
                             {list.name}
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
              <div className="h-16 flex items-center justify-between px-6 border-b border-white/5 bg-black/20">
                 <TabsList className="bg-white/5 p-1 rounded-xl h-10">
                   <TabsTrigger value="board" className="rounded-lg text-[10px] font-black uppercase tracking-widest px-6 data-[state=active]:bg-primary">Tablero</TabsTrigger>
                   <TabsTrigger value="list" className="rounded-lg text-[10px] font-black uppercase tracking-widest px-6">Lista</TabsTrigger>
                   <TabsTrigger value="calendar" className="rounded-lg text-[10px] font-black uppercase tracking-widest px-6">Agenda</TabsTrigger>
                   <TabsTrigger value="stats" className="rounded-lg text-[10px] font-black uppercase tracking-widest px-6">Dashboard</TabsTrigger>
                 </TabsList>

                 <div className="flex items-center gap-3">
                    <Select value={dateFilterType} onValueChange={handleDateFilterChange}>
                      <SelectTrigger className="w-[140px] h-9 bg-white/5 border-white/10 rounded-xl text-[10px] font-black uppercase text-primary">
                        <Calendar className="h-3.5 w-3.5 mr-2" />
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-900 border-white/10 text-white">
                        <SelectItem value="today">Hoy</SelectItem>
                        <SelectItem value="yesterday">Ayer</SelectItem>
                        <SelectItem value="7d">7 Días</SelectItem>
                        <SelectItem value="30d">30 Días</SelectItem>
                        <SelectItem value="month">Este Mes</SelectItem>
                        <SelectItem value="all">Todo el tiempo</SelectItem>
                      </SelectContent>
                    </Select>

                    <Select value={responsibleFilter} onValueChange={setResponsibleFilter}>
                       <SelectTrigger className="w-[160px] h-9 bg-white/5 border-white/10 rounded-xl text-[10px] font-black uppercase text-slate-400">
                         <Users className="h-3.5 w-3.5 mr-2" />
                         <SelectValue placeholder="Abogado" />
                       </SelectTrigger>
                       <SelectContent className="bg-slate-900 border-white/10 text-white">
                         <SelectItem value="all">Todos los abogados</SelectItem>
                         {users.filter(u => u.rol !== 'admin').map(u => (
                           <SelectItem key={u.id} value={u.nombre}>{u.nombre}</SelectItem>
                         ))}
                         {/* Fallback por si no hay usuarios cargados pero sí nombres en tareas */}
                         {users.length === 0 && Array.from(new Set(tasks.map(t => t.assignee_name).filter(Boolean))).map(name => (
                           <SelectItem key={name} value={name!}>{name}</SelectItem>
                         ))}
                       </SelectContent>
                    </Select>
                 </div>
              </div>

              <div className="flex-1 overflow-hidden relative">
                 <TabsContent value="board" className="h-full m-0 p-6 flex gap-6 overflow-x-auto custom-scrollbar">
                    {dynamicBoardColumns.length === 0 ? (
                      <div className="flex-1 flex flex-col items-center justify-center text-slate-500 gap-4">
                        <Activity className="h-12 w-12 opacity-20" />
                        <p className="text-sm font-bold uppercase tracking-widest opacity-40">No hay tareas para mostrar en este filtro</p>
                      </div>
                    ) : dynamicBoardColumns.map(col => (
                      <div key={col.id} className="min-w-[320px] flex flex-col bg-white/[0.02] border border-white/5 rounded-3xl p-4 shadow-2xl relative">
                        <div className="flex items-center justify-between mb-6 px-2">
                           <div className="flex items-center gap-2">
                              <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: col.dot }} />
                              <h3 className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400">{col.label}</h3>
                           </div>
                           <Badge variant="outline" className="bg-white/5 border-white/10 text-[10px] font-mono text-slate-500">{filteredTasks.filter(t => (t.status || 'ABIERTO') === col.id).length}</Badge>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-4 px-1 custom-scrollbar">
                           {parentTasks.filter(t => (t.status || 'ABIERTO') === col.id).map(task => (
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

                 <TabsContent value="stats" className="h-full m-0 p-8 overflow-y-auto space-y-8 custom-scrollbar bg-black/40">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                       {[
                         { label: 'Sin Asignar', count: tasks.filter(t => !t.assignee_id).length, icon: Users, color: 'text-slate-400', bg: 'bg-slate-400/10' },
                         { label: 'En Curso', count: tasks.filter(t => (t.status || '').toLowerCase().includes('proceso') || (t.status || '').toLowerCase().includes('curso')).length, icon: Activity, color: 'text-blue-500', bg: 'bg-blue-500/10' },
                         { label: 'Completadas', count: tasks.filter(t => (t.status || '').toLowerCase().includes('completado') || (t.status || '').toLowerCase().includes('closed')).length, icon: CheckCircle2, color: 'text-green-500', bg: 'bg-green-500/10' }
                       ].map((card, i) => (
                         <Card key={i} className="bg-white/[0.02] border-white/5 shadow-2xl overflow-hidden relative group">
                            <div className={`absolute top-0 right-0 w-24 h-24 ${card.bg} rounded-full -mr-12 -mt-12 blur-3xl`} />
                            <CardContent className="p-8">
                               <div className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-500 mb-4">{card.label}</div>
                               <div className="flex items-center justify-between">
                                  <div className={`text-5xl font-black ${card.color}`}>{card.count}</div>
                                  <card.icon className={`h-10 w-10 ${card.color} opacity-20 group-hover:opacity-100 transition-all duration-500`} />
                               </div>
                            </CardContent>
                         </Card>
                       ))}
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                       <Card className="bg-[#13141a] border-white/5 shadow-2xl">
                          <CardHeader className="border-b border-white/5">
                             <CardTitle className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400 flex items-center gap-2">
                                <PieIcon className="h-4 w-4 text-primary" /> Tareas por responsable
                             </CardTitle>
                          </CardHeader>
                          <CardContent className="p-6 h-[400px]">
                             <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                   <Pie data={statsByAssignee} cx="50%" cy="50%" innerRadius={80} outerRadius={120} paddingAngle={5} dataKey="value" stroke="none">
                                      {statsByAssignee.map((entry, index) => (
                                         <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                      ))}
                                   </Pie>
                                   <ChartTooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }} />
                                   <Legend verticalAlign="bottom" height={36}/>
                                </PieChart>
                             </ResponsiveContainer>
                          </CardContent>
                       </Card>

                       <Card className="bg-[#13141a] border-white/5 shadow-2xl">
                          <CardHeader className="border-b border-white/5">
                             <CardTitle className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400 flex items-center gap-2">
                                <BarIcon className="h-4 w-4 text-blue-500" /> Distribución por estados ClickUp
                             </CardTitle>
                          </CardHeader>
                          <CardContent className="p-6 h-[400px]">
                             <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={statsByStatus}>
                                   <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                                   <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 9, fontWeight: 'bold' }} />
                                   <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 10 }} />
                                   <ChartTooltip cursor={{ fill: 'rgba(255,255,255,0.02)' }} contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }} />
                                   <Bar dataKey="value" radius={[6, 6, 0, 0]} barSize={40}>
                                      {statsByStatus.map((entry, index) => (
                                         <Cell key={`cell-${index}`} fill={entry.color} />
                                      ))}
                                   </Bar>
                                </BarChart>
                             </ResponsiveContainer>
                          </CardContent>
                       </Card>
                    </div>
                 </TabsContent>
                 
                 <TabsContent value="list" className="h-full m-0 p-6 overflow-y-auto space-y-2">
                    {parentTasks.map(t => (
                      <div key={t.id} className="group flex items-center justify-between p-4 bg-white/[0.02] border border-white/5 rounded-2xl hover:bg-white/[0.04] transition-all cursor-pointer" onClick={() => setSelectedTask(t)}>
                         <div className="flex items-center gap-4">
                            <div className="h-3 w-3 rounded-full border-2 border-slate-700" />
                            <div>
                               <div className="text-[13px] font-bold text-slate-200 group-hover:text-primary transition-colors">{t.title}</div>
                               <div className="text-[10px] text-slate-500 flex items-center gap-3 mt-1">
                                  <span>{t.assignee_name || 'Sin asignar'}</span>
                                  {t.due_date && <span>{format(new Date(t.due_date), 'd MMM')}</span>}
                               </div>
                            </div>
                         </div>
                         <Badge variant="outline" className="text-[9px] font-black tracking-widest">{t.status}</Badge>
                      </div>
                    ))}
                 </TabsContent>

                 <TabsContent value="calendar" className="h-full m-0 p-6">
                    <div className="h-full bg-white/[0.02] rounded-3xl border border-white/5 p-6 relative overflow-hidden">
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
