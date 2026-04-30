import { useState, useEffect, useMemo } from "react";
import { 
  LayoutDashboard, FolderPlus, ListPlus, Plus, RefreshCw, Search, 
  Filter, MoreVertical, ChevronRight, MessageSquare, 
  Calendar as CalendarIcon, User as UserIcon, CheckCircle2, Clock,
  LayoutGrid, CalendarDays, List as ListIcon, Zap, PlayCircle, Lock,
  ChevronDown, Calendar, PieChart as PieIcon, BarChart as BarIcon, 
  TrendingUp, Users, Activity, Flag, Settings, Layers, Users2, Database,
  PanelLeftClose, PanelLeftOpen, AlertTriangle, CalendarRange
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { toast } from "sonner";
import { 
  getWorkspaces, getTasks, importClickUp, updateTask, getUsers,
  type Workspace, type Task as TaskType, type User
} from "@/services/api";
import { TaskDrawer } from "@/components/TaskDrawer";
import { Calendar as BigCalendar, momentLocalizer, Views } from 'react-big-calendar';
import moment from 'moment';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { format, subDays, startOfMonth, endOfMonth, isToday, isYesterday, isWithinInterval, startOfDay, endOfDay, addDays, startOfYear, endOfYear } from 'date-fns';
import { es } from 'date-fns/locale';
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip as ChartTooltip, 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend 
} from 'recharts';
import { motion, AnimatePresence } from "framer-motion";

// Español para el calendario
moment.locale('es');
const localizer = momentLocalizer(moment);

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316', '#14b8a6', '#6366f1'];

export default function ProjectDashboardPage() {
  const [isSyncing, setIsSyncing] = useState(false);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [tasks, setTasks] = useState<TaskType[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("board");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  // Calendario state
  const [calendarDate, setCalendarDate] = useState(new Date());
  const [calendarView, setCalendarView] = useState<any>(Views.MONTH);
  
  // Filtros de navegación
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<number | null>(null);
  const [selectedFolderId, setSelectedFolderId] = useState<number | null>(null);
  const [selectedListId, setSelectedListId] = useState<number | null>(null);
  
  const [expandedWorkspaces, setExpandedWorkspaces] = useState<Set<number>>(new Set());
  const [expandedFolders, setExpandedFolders] = useState<Set<number>>(new Set());
  
  const [selectedTask, setSelectedTask] = useState<TaskType | null>(null);
  
  // Filtros de búsqueda/fecha
  const [searchTerm, setSearchTerm] = useState("");
  const [dateFilterType, setDateFilterType] = useState<string>("all");
  const [dateRange, setDateRange] = useState({ start: "", end: "" });
  const [responsibleFilter, setResponsibleFilter] = useState<string>("all");
  const [clickupToken, setClickupToken] = useState<string>(localStorage.getItem('clickup_token') || '');

  useEffect(() => {
    fetchInitialData();
    getUsers().then(setUsers).catch(console.error);
  }, []);

  const fetchInitialData = async () => {
    setIsLoading(true);
    try {
      const wsData = await getWorkspaces();
      const uniqueWS = Array.from(new Map(wsData.map(ws => [ws.id, ws])).values());
      setWorkspaces(uniqueWS);
      await fetchTasks();
    } catch (error) {
      toast.error("Error al cargar proyectos");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchTasks = async () => {
    try {
      const taskData = await getTasks({});
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
      case 'year': start = format(startOfYear(today), 'yyyy-MM-dd'); end = format(endOfYear(today), 'yyyy-MM-dd'); break;
      case 'last_year': start = format(startOfYear(subDays(startOfYear(today), 1)), 'yyyy-MM-dd'); end = format(endOfYear(subDays(startOfYear(today), 1)), 'yyyy-MM-dd'); break;
      case 'all': start = ""; end = ""; break;
    }
    setDateRange({ start, end });
  };

  const filteredTasks = useMemo(() => {
    return (tasks || []).filter(t => {
      if (selectedListId && t.list_id !== selectedListId) return false;
      
      if (selectedFolderId && !selectedListId) {
        const folder = workspaces.flatMap(ws => ws.folders).find(f => f.id === selectedFolderId);
        const listIds = folder?.lists.map(l => l.id) || [];
        if (!listIds.includes(t.list_id)) return false;
      }

      if (selectedWorkspaceId && !selectedFolderId && !selectedListId) {
        const ws = workspaces.find(w => w.id === selectedWorkspaceId);
        const listIds = ws?.folders.flatMap(f => f.lists.map(l => l.id)) || [];
        if (!listIds.includes(t.list_id)) return false;
      }

      if (searchTerm) {
        const search = searchTerm.toLowerCase();
        if (!t.title.toLowerCase().includes(search) && !t.description?.toLowerCase().includes(search)) return false;
      }
      
      if (responsibleFilter !== "all") {
        const matchesName = t.assignee_name?.includes(responsibleFilter);
        const matchesList = t.assignees?.some(a => (a.nombre || a.username) === responsibleFilter);
        if (!matchesName && !matchesList) return false;
      }
      
      if (dateFilterType !== "all" && t.due_date) {
        const d = new Date(t.due_date);
        if (dateRange.start && d < startOfDay(new Date(dateRange.start))) return false;
        if (dateRange.end && d > endOfDay(new Date(dateRange.end))) return false;
      } else if (dateFilterType !== "all" && !t.due_date) {
        return false;
      }

      return true;
    });
  }, [tasks, selectedListId, selectedFolderId, selectedWorkspaceId, workspaces, searchTerm, responsibleFilter, dateRange, dateFilterType]);

  const dynamicBoardColumns = useMemo(() => {
    const allStatuses = Array.from(new Set(tasks.map(t => t.status || 'ABIERTO')));
    
    allStatuses.sort((a, b) => {
      const aLower = (a || '').toLowerCase();
      const bLower = (b || '').toLowerCase();
      if (aLower.includes('abierto') || aLower.includes('to do') || aLower.includes('open')) return -1;
      if (aLower.includes('completado') || aLower.includes('complete') || aLower.includes('closed')) return 1;
      return 0;
    });

    return allStatuses.map((s, idx) => {
      const sLower = (s || '').toLowerCase();
      let dotColor = COLORS[idx % COLORS.length];
      if (sLower.includes('abierto') || sLower.includes('todo')) dotColor = '#94a3b8';
      if (sLower.includes('proceso') || sLower.includes('curso')) dotColor = '#3b82f6';
      if (sLower.includes('presentar')) dotColor = '#8b5cf6';
      if (sLower.includes('retiro')) dotColor = '#ef4444';
      if (sLower.includes('completado') || sLower.includes('finalizado')) dotColor = '#10b981';

      return {
        id: s,
        label: (s || 'SIN ESTADO').toUpperCase(),
        dot: dotColor
      };
    });
  }, [tasks]);

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
      if (t.assignees && t.assignees.length > 0) {
        t.assignees.forEach(a => {
          const name = a.nombre || a.username;
          map[name] = (map[name] || 0) + 1;
        });
      } else {
        const name = t.assignee_name || "Sin Asignar";
        map[name] = (map[name] || 0) + 1;
      }
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

  const dashboardMetrics = useMemo(() => {
    const now = new Date();
    return {
      sinAsignar: filteredTasks.filter(t => !t.assignee_id && !t.assignee_name).length,
      enCurso: filteredTasks.filter(t => (t.status || '').toLowerCase().includes('proceso') || (t.status || '').toLowerCase().includes('curso')).length,
      completadas: filteredTasks.filter(t => (t.status || '').toLowerCase().includes('completado') || (t.status || '').toLowerCase().includes('closed')).length,
      vencidas: filteredTasks.filter(t => t.due_date && new Date(t.due_date) < now && !t.status.toLowerCase().includes('completado')).length,
      porVencer: filteredTasks.filter(t => t.due_date && isWithinInterval(new Date(t.due_date), { start: now, end: addDays(now, 7) }) && !t.status.toLowerCase().includes('completado')).length
    };
  }, [filteredTasks]);

  const handleActionClick = (action: string) => {
    toast.success(`Iniciando ${action}`, { 
      description: "La funcionalidad se ha activado en tu entorno de trabajo."
    });
  };

  return (
    <div className="flex flex-col h-full bg-background text-foreground overflow-hidden relative font-sans transition-colors duration-500">
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-primary/10 rounded-full blur-[120px] pointer-events-none" />
      
      {/* Header */}
      <motion.div 
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex items-center justify-between py-4 px-6 border-b border-border/40 bg-background/80 backdrop-blur-xl z-20"
      >
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => setSidebarCollapsed(!sidebarCollapsed)} className="rounded-lg hover:bg-accent">
            {sidebarCollapsed ? <PanelLeftOpen className="h-5 w-5" /> : <PanelLeftClose className="h-5 w-5" />}
          </Button>
          <div className="p-2.5 bg-gradient-to-br from-primary to-blue-600 rounded-xl shadow-xl shadow-primary/20">
            <LayoutDashboard className="h-5 w-5 text-white" />
          </div>
          <div onClick={() => { setSelectedWorkspaceId(null); setSelectedFolderId(null); setSelectedListId(null); }} className="cursor-pointer hidden sm:block">
            <h1 className="text-xl font-black tracking-tight flex items-center gap-2">
              EMDECOB JURÍDICO <Badge variant="secondary" className="bg-primary/20 text-primary border-primary/20 text-[10px]">EXPERT</Badge>
            </h1>
            <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Master Workflow Engine</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
           <DropdownMenu>
             <DropdownMenuTrigger asChild>
               <Button variant="outline" size="sm" className="rounded-lg h-9 bg-accent/50 border-border/40 font-bold text-xs">
                 <Layers className="mr-2 h-3.5 w-3.5" /> Operaciones
               </Button>
             </DropdownMenuTrigger>
             <DropdownMenuContent className="w-56 bg-background border-border shadow-2xl rounded-xl">
               <DropdownMenuLabel className="text-[10px] uppercase font-black text-muted-foreground tracking-widest">Gestión Operativa</DropdownMenuLabel>
               <DropdownMenuSeparator />
               <DropdownMenuItem className="cursor-pointer" onClick={() => handleActionClick("Crear Espacio")}><Plus className="mr-2 h-4 w-4" /> Nuevo Espacio</DropdownMenuItem>
               <DropdownMenuItem className="cursor-pointer" onClick={() => handleActionClick("Crear Carpeta")}><FolderPlus className="mr-2 h-4 w-4" /> Nueva Carpeta</DropdownMenuItem>
               <DropdownMenuItem className="cursor-pointer" onClick={() => handleActionClick("Crear Lista")}><ListPlus className="mr-2 h-4 w-4" /> Nueva Lista</DropdownMenuItem>
               <DropdownMenuSeparator />
               <DropdownMenuItem className="cursor-pointer" onClick={() => handleActionClick("Plantillas")}><Database className="mr-2 h-4 w-4" /> Plantillas</DropdownMenuItem>
               <DropdownMenuItem className="cursor-pointer" onClick={() => handleActionClick("Equipos")}><Users2 className="mr-2 h-4 w-4" /> Equipos</DropdownMenuItem>
               <DropdownMenuItem className="cursor-pointer" onClick={() => handleActionClick("Configuración")}><Settings className="mr-2 h-4 w-4" /> Preferencias</DropdownMenuItem>
             </DropdownMenuContent>
           </DropdownMenu>

           <Button variant="ghost" onClick={handleSync} disabled={isSyncing} className="rounded-lg h-9 bg-accent/50 hover:bg-accent border border-border/40 text-xs px-4 font-bold">
             <RefreshCw className={`mr-2 h-3.5 w-3.5 ${isSyncing ? "animate-spin" : ""}`} /> Sincronizar
           </Button>
           
           <Button onClick={() => setSelectedTask({ title: '', status: 'ABIERTO', priority: 'normal', list_id: selectedListId } as any)} className="rounded-lg h-9 bg-primary hover:bg-primary/90 text-primary-foreground font-black text-[11px] px-6 shadow-lg shadow-primary/20 uppercase tracking-wider">
             <Plus className="mr-2 h-4 w-4" /> Nueva Tarea
           </Button>
        </div>
      </motion.div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <AnimatePresence>
          {!sidebarCollapsed && (
            <motion.div 
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 280, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              className="flex flex-col border-r border-border/40 bg-background/50 backdrop-blur-sm overflow-hidden"
            >
               <div className="p-4">
                 <div className="relative group">
                   <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                   <Input placeholder="Buscar..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-9 h-9 bg-accent/30 border-border/40 rounded-lg text-xs" />
                 </div>
               </div>
               <div className="flex-1 overflow-y-auto px-2 space-y-1 custom-scrollbar">
                  {workspaces.map(ws => (
                    <div key={ws.id}>
                       <div className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-all ${selectedWorkspaceId === ws.id && !selectedFolderId ? "bg-primary/10 text-primary" : "hover:bg-accent/50"}`} onClick={() => {
                         const n = new Set(expandedWorkspaces);
                         if (n.has(ws.id)) n.delete(ws.id); else n.add(ws.id);
                         setExpandedWorkspaces(n);
                         setSelectedWorkspaceId(ws.id);
                         setSelectedFolderId(null);
                         setSelectedListId(null);
                       }}>
                         <motion.div animate={{ rotate: expandedWorkspaces.has(ws.id) ? 0 : -90 }}>
                            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                         </motion.div>
                         <span className="text-[10px] font-black uppercase text-muted-foreground tracking-widest">{ws.name}</span>
                       </div>
                       
                       <AnimatePresence>
                         {expandedWorkspaces.has(ws.id) && (
                           <motion.div 
                             initial={{ height: 0, opacity: 0 }}
                             animate={{ height: "auto", opacity: 1 }}
                             exit={{ height: 0, opacity: 0 }}
                             className="overflow-hidden"
                           >
                             {ws.folders.map(f => (
                               <div key={f.id} className="ml-3">
                                  <div className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-all ${selectedFolderId === f.id && !selectedListId ? "bg-primary/10 text-primary" : "hover:bg-accent/50"}`} onClick={() => {
                                    const n = new Set(expandedFolders);
                                    if (n.has(f.id)) n.delete(f.id); else n.add(f.id);
                                    setExpandedFolders(n);
                                    setSelectedFolderId(f.id);
                                    setSelectedListId(null);
                                  }}>
                                    <motion.div animate={{ rotate: expandedFolders.has(f.id) ? 0 : -90 }}>
                                      <ChevronDown className="h-3 w-3 text-muted-foreground" />
                                    </motion.div>
                                    <span className="text-[11px] font-bold text-foreground/70">{f.name}</span>
                                  </div>
                                  <AnimatePresence>
                                    {expandedFolders.has(f.id) && (
                                      <motion.div 
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: "auto", opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        className="overflow-hidden"
                                      >
                                        {f.lists.map(list => (
                                          <motion.div 
                                            key={list.id} 
                                            whileHover={{ x: 5 }}
                                            onClick={(e) => { e.stopPropagation(); setSelectedListId(list.id); }}
                                            className={`ml-5 p-2 rounded-lg cursor-pointer text-[11px] transition-all flex items-center justify-between group ${selectedListId === list.id ? "bg-primary text-primary-foreground font-bold" : "text-muted-foreground hover:text-foreground"}`}
                                          >
                                             {list.name}
                                             {selectedListId === list.id && <Zap className="h-3 w-3 animate-pulse" />}
                                          </motion.div>
                                        ))}
                                      </motion.div>
                                    )}
                                  </AnimatePresence>
                               </div>
                             ))}
                           </motion.div>
                         )}
                       </AnimatePresence>
                    </div>
                  ))}
               </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
           <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
              <div className="h-16 flex items-center justify-between px-6 border-b border-border/40 bg-background/50">
                 <TabsList className="bg-accent/50 p-1 rounded-xl h-10 border border-border/40">
                   <TabsTrigger value="board" className="rounded-lg text-[10px] font-black uppercase tracking-widest px-6">Tablero</TabsTrigger>
                   <TabsTrigger value="list" className="rounded-lg text-[10px] font-black uppercase tracking-widest px-6">Lista</TabsTrigger>
                   <TabsTrigger value="calendar" className="rounded-lg text-[10px] font-black uppercase tracking-widest px-6">Agenda</TabsTrigger>
                   <TabsTrigger value="stats" className="rounded-lg text-[10px] font-black uppercase tracking-widest px-6">Dashboard</TabsTrigger>
                 </TabsList>

                 <div className="flex items-center gap-3">
                    <Select value={dateFilterType} onValueChange={handleDateFilterChange}>
                      <SelectTrigger className="w-[140px] h-9 bg-accent/30 border-border/40 rounded-xl text-[10px] font-black uppercase text-primary">
                        <CalendarRange className="h-3.5 w-3.5 mr-2" />
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="today">Hoy</SelectItem>
                        <SelectItem value="yesterday">Ayer</SelectItem>
                        <SelectItem value="7d">Últimos 7 Días</SelectItem>
                        <SelectItem value="30d">Últimos 30 Días</SelectItem>
                        <SelectItem value="month">Este Mes</SelectItem>
                        <SelectItem value="year">Este Año</SelectItem>
                        <SelectItem value="last_year">Año Pasado</SelectItem>
                        <SelectItem value="all">Histórico</SelectItem>
                      </SelectContent>
                    </Select>

                    <Select value={responsibleFilter} onValueChange={setResponsibleFilter}>
                       <SelectTrigger className="w-[160px] h-9 bg-accent/30 border-border/40 rounded-xl text-[10px] font-black uppercase text-muted-foreground">
                         <Users className="h-3.5 w-3.5 mr-2" />
                         <SelectValue placeholder="Abogado" />
                       </SelectTrigger>
                       <SelectContent>
                         <SelectItem value="all">Todos</SelectItem>
                         {Array.from(new Set(tasks.map(t => t.assignee_name).filter(Boolean))).map(name => (
                           <SelectItem key={name!} value={name!}>{name}</SelectItem>
                         ))}
                       </SelectContent>
                    </Select>
                 </div>
              </div>

              <div className="flex-1 overflow-hidden relative">
                 <AnimatePresence mode="wait">
                    {activeTab === "board" && (
                      <motion.div 
                        key="board"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        className="h-full p-6 flex gap-6 overflow-x-auto custom-scrollbar"
                      >
                         {dynamicBoardColumns.map((col, colIdx) => (
                           <div key={col.id} className="min-w-[320px] flex flex-col bg-accent/5 border border-border/40 rounded-3xl p-4 shadow-xl">
                             <div className="flex items-center justify-between mb-6 px-2">
                                <div className="flex items-center gap-2">
                                   <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: col.dot }} />
                                   <h3 className="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground">{col.label}</h3>
                                </div>
                                <Badge variant="outline" className="text-[10px]">{filteredTasks.filter(t => (t.status || 'ABIERTO') === col.id).length}</Badge>
                             </div>
                             <div className="flex-1 overflow-y-auto space-y-4 px-1 custom-scrollbar">
                                {parentTasks.filter(t => (t.status || 'ABIERTO') === col.id).map(task => (
                                  <Card key={task.id} className="bg-card/80 border-border/40 hover:border-primary/40 transition-all cursor-pointer shadow-lg overflow-hidden" onClick={() => setSelectedTask(task)}>
                                    <div className="p-4">
                                       <div className="flex justify-between items-start mb-3">
                                          <Badge variant="secondary" className="text-[9px] uppercase tracking-wider">{task.priority || 'Normal'}</Badge>
                                          {subtasksMap[task.id] && <div className="text-[9px] text-primary font-bold">{subtasksMap[task.id].length} Subtareas</div>}
                                       </div>
                                       <h4 className="text-[13px] font-bold leading-snug line-clamp-2 mb-4">{task.title}</h4>
                                       <div className="flex items-center justify-between border-t border-border/40 pt-3">
                                          <div className="flex items-center">
                                             <div className="flex -space-x-2 overflow-hidden mr-2">
                                                {task.assignees?.map((a, i) => (
                                                  <div key={i} className="h-5 w-5 rounded-full ring-2 ring-card bg-primary/20 flex items-center justify-center text-[8px] font-black text-primary border border-primary/20">{(a.nombre || a.username)[0]}</div>
                                                ))}
                                             </div>
                                             <span className="text-[9px] font-bold text-muted-foreground truncate max-w-[80px]">{task.assignee_name}</span>
                                          </div>
                                          {task.due_date && <span className={`text-[9px] font-black flex items-center gap-1 ${new Date(task.due_date) < new Date() && !task.status.toLowerCase().includes('completado') ? 'text-red-500' : 'text-muted-foreground'}`}><Clock className="h-3 w-3"/> {format(new Date(task.due_date), 'd MMM')}</span>}
                                       </div>
                                    </div>
                                  </Card>
                                ))}
                             </div>
                           </div>
                         ))}
                      </motion.div>
                    )}

                    {activeTab === "list" && (
                      <motion.div 
                        key="list"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="h-full p-6 overflow-y-auto space-y-2 custom-scrollbar"
                      >
                         {parentTasks.map(t => (
                           <div key={t.id} className="group flex items-center justify-between p-4 bg-accent/5 border border-border/40 rounded-2xl hover:bg-accent/10 transition-all cursor-pointer" onClick={() => setSelectedTask(t)}>
                              <div className="flex items-center gap-4">
                                 <div className="h-3 w-3 rounded-full border-2 border-muted-foreground/30" />
                                 <div>
                                    <div className="text-[13px] font-bold group-hover:text-primary transition-colors">{t.title}</div>
                                    <div className="text-[10px] text-muted-foreground flex items-center gap-3 mt-1">
                                       <span>{t.assignee_name || 'Sin asignar'}</span>
                                       {t.due_date && <span>{format(new Date(t.due_date), 'd MMM')}</span>}
                                    </div>
                                 </div>
                              </div>
                              <Badge variant="outline" className="text-[9px] font-black">{t.status}</Badge>
                           </div>
                         ))}
                      </motion.div>
                    )}

                    {activeTab === "calendar" && (
                      <motion.div 
                        key="calendar"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="h-full p-6"
                      >
                         <div className="h-full bg-card rounded-3xl border border-border/40 p-6 overflow-hidden shadow-2xl">
                            <BigCalendar
                              localizer={localizer}
                              events={calendarEvents}
                              startAccessor="start"
                              endAccessor="end"
                              date={calendarDate}
                              view={calendarView}
                              onNavigate={setCalendarDate}
                              onView={setCalendarView}
                              style={{ height: '100%' }}
                              onSelectEvent={(e: any) => setSelectedTask(e.resource)}
                              messages={{ today: "Hoy", previous: "Anterior", next: "Siguiente", month: "Mes", week: "Semana", day: "Día", agenda: "Agenda" }}
                              culture="es"
                            />
                         </div>
                      </motion.div>
                    )}

                    {activeTab === "stats" && (
                      <motion.div 
                        key="stats"
                        initial={{ opacity: 0, scale: 0.98 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 1.02 }}
                        className="h-full p-8 overflow-y-auto space-y-8 custom-scrollbar bg-accent/5"
                      >
                         {/* METRICAS SUPERIORES */}
                         <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
                            {[
                              { label: 'Sin Asignar', count: dashboardMetrics.sinAsignar, icon: Users, color: 'text-slate-400', bg: 'bg-slate-400/10' },
                              { label: 'En Curso', count: dashboardMetrics.enCurso, icon: Activity, color: 'text-blue-500', bg: 'bg-blue-500/10' },
                              { label: 'Vencidas', count: dashboardMetrics.vencidas, icon: AlertTriangle, color: 'text-red-500', bg: 'bg-red-500/10' },
                              { label: 'Por Vencer (7d)', count: dashboardMetrics.porVencer, icon: Clock, color: 'text-orange-500', bg: 'bg-orange-500/10' },
                              { label: 'Completadas', count: dashboardMetrics.completadas, icon: CheckCircle2, color: 'text-green-500', bg: 'bg-green-500/10' }
                            ].map((card, i) => (
                              <Card key={i} className="bg-card border-border/40 shadow-xl overflow-hidden relative group">
                                 <div className={`absolute top-0 right-0 w-24 h-24 ${card.bg} rounded-full -mr-12 -mt-12 blur-3xl`} />
                                 <CardContent className="p-6">
                                    <div className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground mb-4">{card.label}</div>
                                    <div className="flex items-center justify-between">
                                       <div className={`text-4xl font-black ${card.color}`}>{card.count}</div>
                                       <card.icon className={`h-8 w-8 ${card.color} opacity-20`} />
                                    </div>
                                 </CardContent>
                              </Card>
                            ))}
                         </div>

                         <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                            <Card className="bg-card border-border/40 shadow-xl">
                               <CardHeader className="border-b border-border/40">
                                  <CardTitle className="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground">Carga por Abogado</CardTitle>
                               </CardHeader>
                               <CardContent className="p-6 h-[400px]">
                                  <ResponsiveContainer width="100%" height="100%">
                                     <PieChart>
                                        <Pie data={statsByAssignee} cx="50%" cy="50%" innerRadius={80} outerRadius={120} paddingAngle={5} dataKey="value" stroke="none">
                                           {statsByAssignee.map((entry, index) => (
                                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                           ))}
                                        </Pie>
                                        <ChartTooltip contentStyle={{ background: 'var(--background)', border: '1px solid var(--border)', borderRadius: '12px' }} />
                                        <Legend verticalAlign="bottom" height={36}/>
                                     </PieChart>
                                  </ResponsiveContainer>
                               </CardContent>
                            </Card>

                            <Card className="bg-card border-border/40 shadow-xl">
                               <CardHeader className="border-b border-border/40">
                                  <CardTitle className="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground">Distribución de Estados</CardTitle>
                               </CardHeader>
                               <CardContent className="p-6 h-[400px]">
                                  <ResponsiveContainer width="100%" height="100%">
                                     <BarChart data={statsByStatus}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.1)" vertical={false} />
                                        <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: 'var(--muted-foreground)', fontSize: 9, fontWeight: 'bold' }} />
                                        <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--muted-foreground)', fontSize: 10 }} />
                                        <ChartTooltip cursor={{ fill: 'rgba(128,128,128,0.05)' }} contentStyle={{ background: 'var(--background)', border: '1px solid var(--border)', borderRadius: '12px' }} />
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
                      </motion.div>
                    )}
                 </AnimatePresence>
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
        allAssignees={Array.from(new Set(tasks.map(t => t.assignee_name).filter(Boolean))) as string[]}
        allStatuses={dynamicBoardColumns.map(c => c.id)}
      />
    </div>
  );
}
