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

const events = [
  {
    title: 'REINOSO CORDOBA - Vencimiento Actuación',
    start: new Date(2026, 3, 20, 10, 0),
    end: new Date(2026, 3, 20, 11, 0),
    resource: 'Alta',
  },
  {
    title: 'WILLIAM POLANIA - Envío Memorial',
    start: new Date(2026, 3, 21, 14, 0),
    end: new Date(2026, 3, 21, 15, 30),
    resource: 'Normal',
  },
  {
    title: 'FNA - Saneamiento Cartera',
    start: new Date(2026, 3, 22, 9, 0),
    end: new Date(2026, 3, 24, 18, 0),
    resource: 'Proyectos',
  },
];

export default function AgendaView() {
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
            <Button variant="outline" size="sm">
                <Filter className="mr-2 h-4 w-4" /> Filtrar Equipo
            </Button>
            <Button size="sm">
                <Plus className="mr-2 h-4 w-4" /> Programar Evento
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
                    <div className="text-2xl font-bold italic">4 Tareas</div>
                    <p className="text-xs text-muted-foreground mt-1">2 vencimientos críticos</p>
                </CardContent>
            </Card>

            <div className="space-y-2">
                <h3 className="text-sm font-semibold px-2">Próximos Vencimientos</h3>
                <div className="space-y-2">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="p-3 rounded-lg border bg-card hover:bg-muted/50 cursor-pointer transition-colors text-xs">
                            <div className="flex justify-between items-start mb-1">
                                <span className="font-bold">Proceso #342{i}</span>
                                <Badge variant="outline" className="text-[9px] h-4">Urgente</Badge>
                            </div>
                            <p className="text-muted-foreground truncate">Revisión de estados procesales...</p>
                            <div className="mt-2 text-primary font-medium">Hace 2 horas</div>
                        </div>
                    ))}
                </div>
            </div>
        </div>

        {/* Calendario Principal */}
        <Card className="lg:col-span-3 min-h-[600px] shadow-sm overflow-hidden">
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
                        style={{ height: '100%' }}
                        eventPropGetter={(event) => {
                            let backgroundColor = '#3b82f6';
                            if (event.resource === 'Alta') backgroundColor = '#ef4444';
                            if (event.resource === 'Proyectos') backgroundColor = '#8b5cf6';
                            return { style: { backgroundColor, border: 'none', borderRadius: '4px' } };
                        }}
                    />
                </div>
            </CardContent>
        </Card>
      </div>
    </div>
  );
}
