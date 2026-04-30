import { useState, useEffect } from "react";
import { 
  CheckCircle2, Clock, Calendar as CalendarIcon, User as UserIcon, 
  Flag, AlertCircle, ChevronDown, ChevronRight, Activity, 
  Search, Filter, ListChecks, Hash
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

interface MyTasksViewProps {
  mode: "assigned" | "today";
}

export function MyTasksView({ mode }: MyTasksViewProps) {
  const { user } = useAuth();
  const { toast } = useToast();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  useEffect(() => {
    loadTasks();
  }, [mode, user?.id]);

  const loadTasks = async () => {
    if (!user?.id) return;
    setIsLoading(true);
    try {
      // Obtenemos todas las tareas asignadas al usuario
      // El backend ya tiene el filtro de assignee_id
      const res = await getTasks({ assignee_id: user.id });
      
      let filtered = res || [];
      
      if (mode === "today") {
        const today = startOfToday();
        filtered = filtered.filter(t => {
          if (!t.due_date) return false;
          const d = parseISO(t.due_date.toString());
          return isToday(d) || isBefore(d, today);
        });
      }

      setTasks(filtered);
    } catch (error) {
      toast({ title: "Error al cargar tareas", variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  const filteredTasks = tasks.filter(t => 
    t.title.toLowerCase().includes(search.toLowerCase()) ||
    t.clickup_id?.toLowerCase().includes(search.toLowerCase())
  );

  const handleTaskClick = (task: Task) => {
    setSelectedTask(task);
    setIsDrawerOpen(true);
  };

  return (
    <div className="flex flex-col h-full bg-background animate-in fade-in duration-500">
      <div className="p-8 border-b border-border/50 bg-card/30 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
               <h1 className="text-3xl font-black tracking-tight text-foreground flex items-center gap-4">
                  <ListChecks className="h-8 w-8 text-primary" />
                  {mode === "assigned" ? "Asignadas a mí" : "Hoy y vencido"}
               </h1>
               <p className="text-sm text-muted-foreground font-medium uppercase tracking-widest opacity-60">
                  {mode === "assigned" ? "Panel central de litigio personalizado" : "Trámites urgentes con términos legales próximos"}
               </p>
            </div>
            <div className="flex items-center gap-4">
               <Button onClick={loadTasks} variant="outline" className="rounded-xl border-primary/20 hover:bg-primary/5">
                  <Activity className={cn("h-4 w-4 mr-2 text-primary", isLoading && "animate-spin")} />
                  Sincronizar
               </Button>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative flex-1 group">
               <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
               <Input 
                 placeholder="Buscar por radicado o título de gestión..." 
                 className="pl-12 h-12 bg-card/50 border-border/50 rounded-2xl focus:ring-primary/20 focus:border-primary/40 transition-all text-[15px] font-medium"
                 value={search}
                 onChange={(e) => setSearch(e.target.value)}
               />
            </div>
            <Button variant="outline" className="h-12 w-12 rounded-2xl border-border/50 bg-card/50">
               <Filter className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>

      <ScrollArea className="flex-1 p-8">
        <div className="max-w-7xl mx-auto space-y-4">
           {isLoading ? (
             <div className="py-20 text-center space-y-4 opacity-50">
                <Activity className="h-12 w-12 mx-auto animate-spin text-primary" />
                <p className="text-sm font-black uppercase tracking-[0.3em]">Cargando expediente personal...</p>
             </div>
           ) : filteredTasks.length > 0 ? (
             <div className="bg-card/30 rounded-[2.5rem] border border-border/50 overflow-hidden shadow-2xl">
                <div className="grid grid-cols-[1fr_200px_150px_180px] gap-8 px-10 py-6 border-b border-border/50 text-[10px] font-black uppercase text-muted-foreground tracking-[0.4em] bg-muted/20">
                   <div>Descripción de la Gestión</div>
                   <div className="text-center">Estado</div>
                   <div className="text-center">Prioridad</div>
                   <div className="text-right">Término Legal</div>
                </div>
                <div className="divide-y divide-border/50">
                   {filteredTasks.map(task => (
                     <div 
                        key={task.id} 
                        className="grid grid-cols-[1fr_200px_150px_180px] gap-8 px-10 py-6 hover:bg-primary/5 transition-all cursor-pointer group animate-in slide-in-from-bottom-2 duration-300"
                        onClick={() => handleTaskClick(task)}
                     >
                        <div className="flex items-center gap-5">
                           <div className="h-10 w-10 rounded-xl bg-card border border-border/50 flex items-center justify-center text-primary shadow-lg group-hover:scale-110 transition-transform">
                              <Hash className="h-5 w-5" />
                           </div>
                           <div className="flex flex-col">
                              <span className="text-[16px] font-black text-foreground group-hover:text-primary transition-colors tracking-tight">{task.title}</span>
                              <span className="text-[11px] text-muted-foreground font-bold tracking-widest uppercase opacity-60">ID: {task.clickup_id || task.id}</span>
                           </div>
                        </div>
                        <div className="flex items-center justify-center">
                           <Badge className={cn(
                             "px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest border-none shadow-lg",
                             task.status?.toLowerCase().includes('done') ? "bg-[#2da44e] text-white" : "bg-primary/20 text-primary"
                           )}>
                              {task.status || 'ABIERTO'}
                           </Badge>
                        </div>
                        <div className="flex items-center justify-center">
                           <Flag className={cn(
                             "h-6 w-6 drop-shadow-sm",
                             task.priority?.toLowerCase() === 'high' ? "text-red-500" : "text-muted-foreground opacity-30"
                           )} />
                        </div>
                        <div className="flex items-center justify-end">
                           <div className={cn(
                             "flex items-center gap-3 text-[13px] font-black uppercase tracking-tighter px-5 py-2 rounded-xl border transition-all",
                             task.due_date && isBefore(parseISO(task.due_date.toString()), startOfToday()) 
                              ? "bg-red-500/10 text-red-500 border-red-500/20 shadow-red-500/10 shadow-lg" 
                              : "bg-muted/50 text-muted-foreground border-border/50"
                           )}>
                              <CalendarIcon className="h-4 w-4" />
                              {task.due_date ? format(parseISO(task.due_date.toString()), "d MMM, yyyy", { locale: es }) : 'SIN FECHA'}
                           </div>
                        </div>
                     </div>
                   ))}
                </div>
             </div>
           ) : (
             <div className="py-32 text-center space-y-8 bg-card/20 rounded-[3rem] border border-dashed border-border/50">
                <CheckCircle2 className="h-20 w-20 mx-auto text-muted-foreground opacity-20" />
                <div className="space-y-2">
                   <p className="text-xl font-black text-foreground tracking-tight">Todo al día, abogado</p>
                   <p className="text-sm text-muted-foreground font-medium uppercase tracking-widest">No hay tareas pendientes en este panel</p>
                </div>
             </div>
           )}
        </div>
      </ScrollArea>

      <TaskDrawer 
        task={selectedTask}
        open={isDrawerOpen}
        onOpenChange={setIsDrawerOpen}
        onTaskUpdate={(updated) => {
          setTasks(prev => prev.map(t => t.id === updated.id ? updated : t));
          setSelectedTask(updated);
        }}
      />
    </div>
  );
}
