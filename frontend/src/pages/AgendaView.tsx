import { Calendar as BigCalendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import 'moment/locale/es';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calendar as CalendarIcon, Clock, Filter, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";

// Configuración de moment en español
moment.locale('es');
const localizer = momentLocalizer(moment);

import { useState, useEffect } from 'react';
import { getTasks, type Task as TaskType, createTask, updateTask } from '@/services/api';
import { toast } from "sonner";
import { RefreshCw } from 'lucide-react';
import { TaskDrawer } from '@/components/TaskDrawer';

export default function AgendaView() {
  const [tasks, setTasks] = useState<TaskType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState<TaskType | null>(null);

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    setIsLoading(true);
    try {
      console.log('[AGENDA] Fetching tasks globally...');
      const data = await getTasks({});
      console.log('[AGENDA] Received:', data?.length || 0, 'tasks');
      setTasks(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('[AGENDA] Error:', error);
      toast.error("No se pudo cargar la agenda.");
      setTasks([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTaskUpdate = (t: TaskType) => {
    setTasks(prev => {
      const exists = prev.some(x => x.id === t.id);
      if (exists) return prev.map(x => x.id === t.id ? t : x);
      return [t, ...prev];
    });
    setSelectedTask(t);
    fetchTasks(); // Refrescar para asegurar orden
  };

  const events = tasks.map(t => {
    const d = t.due_date ? new Date(t.due_date) : new Date();
    return {
      id: t.id,
      title: t.title + (!t.due_date ? ' (Sin Fecha)' : ''),
      start: d,
      end: d,
      resource: t.priority,
      task: t
    };
  });

  const todayTasks = tasks.filter(t => {
    if (!t.due_date) return false;
    const d = new Date(t.due_date);
    const today = new Date();
    return d.toDateString() === today.toDateString();
  });

  return (
    <div className="flex flex-col h-full space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <CalendarIcon className="h-8 w-8 text-primary" />
            Agenda y Calendario
          </h1>
          <p className="text-muted-foreground">Vista unificada de todas las tareas y vencimientos del equipo.</p>
        </div>
        
        <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={fetchTasks} disabled={isLoading}>
                <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} /> Actualizar
            </Button>
            <Button size="sm" onClick={() => setSelectedTask({ title: '', status: 'to do', priority: 'normal' } as any)}>
                <Plus className="mr-2 h-4 w-4" /> Programar Tarea
            </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Estadísticas Rápidas */}
        <div className="lg:col-span-1 space-y-4">
            <Card className="bg-primary/5 border-primary/20">
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <Clock className="h-4 w-4" /> Para Hoy
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold italic">{todayTasks.length} Tareas</div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {todayTasks.filter(t => t.priority === 'urgent' || t.priority === 'high').length} críticas
                    </p>
                </CardContent>
            </Card>

            <div className="space-y-2">
                <h3 className="text-sm font-semibold px-2">Próximos Vencimientos</h3>
                <div className="space-y-2 max-h-[400px] overflow-y-auto custom-scrollbar pr-1">
                    {tasks.slice(0, 10).map((t) => (
                        <div 
                          key={t.id} 
                          className="p-3 rounded-lg border bg-card hover:bg-muted/50 cursor-pointer transition-colors text-xs"
                          onClick={() => setSelectedTask(t)}
                        >
                            <div className="flex justify-between items-start mb-1">
                                <span className="font-bold truncate max-w-[150px]">{t.title}</span>
                                <Badge variant="outline" className={`text-[9px] h-4 ${t.priority === 'urgent' ? 'text-red-500 border-red-500' : ''}`}>
                                  {t.priority || 'Normal'}
                                </Badge>
                            </div>
                            <p className="text-muted-foreground truncate">{t.due_date ? new Date(t.due_date).toLocaleDateString('es-CO') : 'Programado para Hoy'}</p>
                        </div>
                    ))}
                    {tasks.length === 0 && (
                        <p className="text-xs text-muted-foreground text-center py-4">No hay tareas programadas.</p>
                    )}
                </div>
            </div>
        </div>

        {/* Calendario Principal */}
        <Card className="lg:col-span-3 min-h-[600px] shadow-sm overflow-hidden bg-card/50 backdrop-blur-sm">
            <CardContent className="p-0">
                <div className="h-[650px] p-4 text-sm" id="main-calendar">
                    <BigCalendar
                        localizer={localizer}
                        events={events}
                        startAccessor="start"
                        endAccessor="end"
                        messages={{
                            next: "Sig",
                            previous: "Ant",
                            today: "Hoy",
                            month: "Mes",
                            week: "Semana",
                            day: "Día",
                            agenda: "Agenda",
                            date: "Fecha",
                            time: "Hora",
                            event: "Evento"
                        }}
                        onSelectEvent={(e: any) => setSelectedTask(e.task)}
                        style={{ height: '100%' }}
                        eventPropGetter={(event) => {
                            let backgroundColor = '#3b82f6';
                            const p = event.resource?.toLowerCase();
                            if (p === 'urgent' || p === 'high' || p === 'alta') backgroundColor = '#ef4444';
                            if (p === 'proyectos') backgroundColor = '#8b5cf6';
                            return { style: { backgroundColor, border: 'none', borderRadius: '4px' } };
                        }}
                    />
                </div>
            </CardContent>
        </Card>
      </div>

      <TaskDrawer 
        task={selectedTask}
        open={!!selectedTask}
        onOpenChange={(open) => !open && setSelectedTask(null)}
        onTaskUpdate={handleTaskUpdate}
      />
    </div>
  );
}
