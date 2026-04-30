import { useState, useEffect, useMemo } from "react";
import { 
  CheckCircle2, Clock, Calendar as CalendarIcon, User as UserIcon, 
  Flag, AlertCircle, ChevronDown, ChevronRight, Activity, 
  Search, Filter, ListChecks, Hash, UserCheck, RefreshCw
} from "lucide-react";
import { getTasks, type Task } from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { format, isToday, isBefore, parseISO, startOfToday } from "date-fns";
import { es } from "date-fns/locale";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { TaskDrawer } from "./TaskDrawer";
import { cn } from "@/lib/utils";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export function MyTasksView() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("assigned");

  useEffect(() => {
    loadTasks();
  }, [user?.id]);

  const loadTasks = async () => {
    if (!user?.id) return;
    setIsLoading(true);
    try {
      const res = await getTasks({ assignee_id: user.id });
      setTasks(res || []);
    } catch (error) {
      toast({ title: "Error al cargar tareas", variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  const getFilteredTasks = (mode: string) => {
    let filtered = tasks;
    if (mode === "today") {
      const today = startOfToday();
      filtered = filtered.filter(t => {
        if (!t.due_date) return false;
        const d = parseISO(t.due_date.toString());
        return isToday(d) || isBefore(d, today);
      });
    }
    return filtered.filter(t => 
      t.title.toLowerCase().includes(search.toLowerCase()) ||
      t.clickup_id?.toLowerCase().includes(search.toLowerCase())
    );
  };

  const overdueCount = useMemo(() => {
    const today = startOfToday();
    return tasks.filter(t => {
      if (!t.due_date) return false;
      const d = parseISO(t.due_date.toString());
      return isToday(d) || isBefore(d, today);
    }).length;
  }, [tasks]);

  const handleTaskClick = (task: Task) => {
    setSelectedTask(task);
    setIsDrawerOpen(true);
  };

  return (
    <div className="flex flex-col h-full bg-[#0a0a0a] animate-in fade-in duration-700">
      <div className="p-10 border-b border-white/5 bg-white/[0.01]">
        <div className="max-w-[1600px] mx-auto space-y-8">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
               <h1 className="text-4xl font-black tracking-tighter text-white flex items-center gap-5">
                  <div className="h-12 w-12 rounded-2xl bg-primary/10 flex items-center justify-center border border-primary/20 shadow-2xl">
                    <UserCheck className="h-7 w-7 text-primary" />
                  </div>
                  Experiencia de Usuario: Mis Tareas
               </h1>
               <p className="text-[12px] text-gray-600 font-black uppercase tracking-[0.4em] opacity-80">
                  Panel central de litigio y gestión de términos legales
               </p>
            </div>
            <Button onClick={loadTasks} variant="outline" className="h-12 px-8 rounded-2xl bg-white/5 border-white/10 hover:bg-white/10 text-white font-black text-[11px] uppercase tracking-widest transition-all shadow-xl gap-3">
               <RefreshCw className={cn("h-4 w-4 text-primary", isLoading && "animate-spin")} />
               Sincronizar ClickUp
            </Button>
          </div>

          <Tabs defaultValue="assigned" className="w-full" onValueChange={setActiveTab}>
             <div className="flex items-center justify-between border-b border-white/5 pb-1">
                <TabsList className="bg-transparent border-none p-0 h-auto gap-10">
                   <TabsTrigger value="assigned" className="bg-transparent border-none text-gray-700 data-[state=active]:text-primary data-[state=active]:shadow-none p-0 pb-4 rounded-none border-b-2 border-transparent data-[state=active]:border-primary transition-all text-[14px] font-black uppercase tracking-widest shadow-none hover:text-gray-400">
                      Asignadas a mí
                   </TabsTrigger>
                   <TabsTrigger value="today" className="bg-transparent border-none text-gray-700 data-[state=active]:text-red-500 data-[state=active]:shadow-none p-0 pb-4 rounded-none border-b-2 border-transparent data-[state=active]:border-red-500 transition-all text-[14px] font-black uppercase tracking-widest flex items-center gap-3 shadow-none hover:text-gray-400">
                      Hoy y vencido
                      {overdueCount > 0 && <Badge className="bg-red-500/10 text-red-500 border-none text-[10px] h-5 px-2">{overdueCount}</Badge>}
                   </TabsTrigger>
                </TabsList>

                <div className="flex items-center gap-6 pb-4">
                   <div className="relative group w-80">
                      <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-700 group-focus-within:text-primary transition-colors" />
                      <Input 
                        placeholder="Filtrar gestiones..." 
                        className="pl-12 h-10 bg-white/[0.03] border-white/10 rounded-xl focus:ring-primary/20 focus:border-primary/40 transition-all text-[13px] font-medium text-white"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                      />
                   </div>
                   <Button variant="outline" className="h-10 w-10 rounded-xl border-white/10 bg-white/[0.03] text-gray-600">
                      <Filter className="h-4 w-4" />
                   </Button>
                </div>
             </div>

             <div className="mt-8">
                <TabsContent value="assigned" className="m-0 focus-visible:outline-none outline-none">
                   <TaskList tasks={getFilteredTasks("assigned")} isLoading={isLoading} onTaskClick={handleTaskClick} />
                </TabsContent>
                <TabsContent value="today" className="m-0 focus-visible:outline-none outline-none">
                   <TaskList tasks={getFilteredTasks("today")} isLoading={isLoading} onTaskClick={handleTaskClick} isUrgent />
                </TabsContent>
             </div>
          </Tabs>
        </div>
      </div>

      <TaskDrawer 
        task={selectedTask}
        open={isDrawerOpen}
        onOpenChange={setIsDrawerOpen}
        onTaskUpdate={(updated) => {
          setTasks(prev => prev.map(t => t.id === updated.id ? updated : t));
          setSelectedTask(updated);
        }}
        clickupToken={localStorage.getItem("clickup_token") || undefined}
      />
    </div>
  );
}

interface TaskListProps {
  tasks: Task[];
  isLoading: boolean;
  onTaskClick: (task: Task) => void;
  isUrgent?: boolean;
}

function TaskList({ tasks, isLoading, onTaskClick, isUrgent }: TaskListProps) {
  if (isLoading) {
    return (
      <div className="py-40 text-center space-y-6 opacity-40">
         <Activity className="h-16 w-16 mx-auto animate-spin text-primary" />
         <p className="text-[11px] font-black uppercase tracking-[0.5em] text-gray-500">Analizando carga de trabajo...</p>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="py-40 text-center space-y-10 bg-white/[0.01] rounded-[4rem] border border-dashed border-white/5 mx-10">
         <CheckCircle2 className="h-24 w-24 mx-auto text-gray-800 opacity-20" />
         <div className="space-y-3">
            <p className="text-2xl font-black text-gray-400 tracking-tight">Todo al día, abogado</p>
            <p className="text-[10px] text-gray-700 font-black uppercase tracking-widest">No hay gestiones pendientes en este panel</p>
         </div>
      </div>
    );
  }

  return (
    <div className="bg-white/[0.01] rounded-[3rem] border border-white/5 overflow-hidden shadow-2xl">
       <div className="grid grid-cols-[1fr_180px_120px_180px] gap-10 px-12 py-6 border-b border-white/10 text-[9px] font-black uppercase text-gray-600 tracking-[0.4em] bg-white/[0.02]">
          <div>Descripción Técnica de la Gestión</div>
          <div className="text-center">Estado Judicial</div>
          <div className="text-center">Prioridad</div>
          <div className="text-right">Término Legal</div>
       </div>
       <div className="divide-y divide-white/5">
          {tasks.map(task => (
            <div 
               key={task.id} 
               className="grid grid-cols-[1fr_180px_120px_180px] gap-10 px-12 py-5 hover:bg-white/[0.04] transition-all cursor-pointer group animate-in slide-in-from-bottom-3 duration-500 border-l-2 border-transparent hover:border-primary"
               onClick={() => onTaskClick(task)}
            >
               <div className="flex items-center gap-6">
                  <div className="h-10 w-10 rounded-xl bg-black border border-white/10 flex items-center justify-center text-primary shadow-xl group-hover:scale-110 group-hover:border-primary/40 transition-all">
                     <Hash className="h-5 w-5" />
                  </div>
                  <div className="flex flex-col gap-1">
                     <span className="text-[15px] font-black text-gray-200 group-hover:text-primary transition-colors tracking-tight leading-tight">{task.title}</span>
                     <span className="text-[10px] text-gray-700 font-black tracking-widest uppercase opacity-60">REF: {task.clickup_id || task.id}</span>
                  </div>
               </div>
               <div className="flex items-center justify-center">
                  <Badge className={cn(
                    "px-4 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest border-none shadow-xl",
                    task.status?.toLowerCase().includes('done') ? "bg-[#2da44e] text-white" : "bg-primary/20 text-primary"
                  )}>
                     {task.status || 'ABIERTO'}
                  </Badge>
               </div>
               <div className="flex items-center justify-center">
                  <Flag className={cn(
                    "h-6 w-6 drop-shadow-xl transition-transform group-hover:scale-125",
                    task.priority?.toLowerCase() === 'high' ? "text-red-500" : "text-gray-900"
                  )} />
               </div>
               <div className="flex items-center justify-end">
                  <div className={cn(
                    "flex items-center gap-3 text-[12px] font-black uppercase tracking-tighter px-6 py-2 rounded-xl border transition-all shadow-inner",
                    task.due_date && isBefore(parseISO(task.due_date.toString()), startOfToday()) 
                     ? "bg-red-500/10 text-red-500 border-red-500/20 shadow-red-500/20 shadow-lg animate-pulse" 
                     : "bg-white/5 text-gray-500 border-white/5"
                  )}>
                     <Clock className="h-4 w-4" />
                     {task.due_date ? format(parseISO(task.due_date.toString()), "d MMM, yyyy", { locale: es }) : 'SIN TÉRMINO'}
                  </div>
               </div>
            </div>
          ))}
       </div>
    </div>
  );
}
