import { motion } from "framer-motion";
import { 
  Book, ShieldCheck, Scale, LayoutDashboard, Calendar, Users, 
  Settings, ChevronRight, Info, HelpCircle, ArrowLeft, ExternalLink
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useNavigate } from "react-router-dom";

const sections = [
  {
    id: "acceso",
    title: "1. Acceso al Sistema",
    icon: ShieldCheck,
    content: "Utilice sus credenciales autorizadas en la pantalla de inicio. El sistema cuenta con modo oscuro y claro para su comodidad visual.",
    tips: ["Puede cambiar el tema en el interruptor de la parte inferior izquierda."]
  },
  {
    id: "judicial",
    title: "2. Gestión Judicial",
    icon: Scale,
    content: "El núcleo del sistema es el monitoreo automático. Puede consultar casos por radicado (23 dígitos) o por nombre. Las alertas en rojo indican actuaciones en las últimas 24 horas.",
    tips: ["Use 'Importar Excel' para carga masiva de radicados."]
  },
  {
    id: "proyectos",
    title: "3. Gestión de Proyectos",
    icon: LayoutDashboard,
    content: "Organice su trabajo en Espacios, Carpetas y Listas. El Tablero Kanban le permite visualizar el estado de cada tarea de forma ágil.",
    tips: ["Haga clic en un Espacio para ver todas las tareas del equipo."]
  },
  {
    id: "tareas",
    title: "4. Control de Tareas",
    icon: Info,
    content: "En el panel de detalle puede asignar responsables, establecer fechas de vencimiento, añadir etiquetas rápidas y gestionar subtareas.",
    tips: ["Escriba una etiqueta y presione Enter para crearla al instante."]
  },
  {
    id: "calendario",
    title: "5. Agenda y Calendario",
    icon: Calendar,
    content: "La vista de Agenda le permite ver vencimientos mensualmente. Haga clic en cualquier día para crear una tarea con esa fecha pre-seleccionada.",
    tips: ["Use el botón de 'Hoy' para volver rápidamente a la fecha actual."]
  },
  {
    id: "admin",
    title: "6. Administración",
    icon: Settings,
    content: "Solo para administradores. Permite gestionar usuarios, auditar radicados y configurar integraciones externas.",
    tips: ["Acceda vía /admin en la URL del servidor."]
  }
];

export default function HelpPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col h-full bg-background text-foreground overflow-y-auto custom-scrollbar p-8">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-4xl mx-auto w-full space-y-8 pb-20"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate(-1)} className="rounded-xl">
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
                Centro de Ayuda <Badge variant="secondary" className="bg-primary/20 text-primary">MANUAL</Badge>
              </h1>
              <p className="text-muted-foreground text-sm font-medium">Todo lo que necesita saber para dominar EMDECOB Judicial Expert</p>
            </div>
          </div>
          <div className="hidden md:flex p-3 bg-primary/10 rounded-2xl">
            <Book className="h-8 w-8 text-primary" />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {sections.map((section, idx) => (
            <motion.div
              key={section.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.1 }}
            >
              <Card className="bg-card/50 backdrop-blur-xl border-border/40 hover:border-primary/40 transition-all h-full shadow-lg">
                <CardHeader className="flex flex-row items-center gap-4 space-y-0">
                  <div className="p-2.5 bg-primary/10 rounded-xl">
                    <section.icon className="h-5 w-5 text-primary" />
                  </div>
                  <CardTitle className="text-base font-black uppercase tracking-wider">{section.title}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {section.content}
                  </p>
                  <div className="pt-4 border-t border-border/40">
                    {section.tips.map((tip, i) => (
                      <div key={i} className="flex gap-2 items-start text-[11px] font-bold text-primary italic">
                        <Info className="h-3.5 w-3.5 mt-0.5 shrink-0" />
                        <span>TIP: {tip}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        <Card className="bg-gradient-to-br from-primary/10 to-blue-500/10 border-primary/20 shadow-2xl">
          <CardContent className="p-8 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="space-y-2">
              <h3 className="text-xl font-black tracking-tight flex items-center gap-2">
                <HelpCircle className="h-6 w-6 text-primary" />
                ¿Necesita soporte técnico?
              </h3>
              <p className="text-sm text-muted-foreground">Si tiene dudas adicionales o requiere una función personalizada, nuestro equipo está listo para ayudarle.</p>
            </div>
            <Button 
              className="rounded-xl bg-primary hover:bg-primary/90 px-8 font-black uppercase tracking-widest text-xs h-12 shadow-lg shadow-primary/20"
              onClick={() => window.location.href = 'mailto:direccionanalitica@emdecob.com'}
            >
              Contactar Soporte
            </Button>
          </CardContent>
        </Card>

        <div className="text-center pt-10">
          <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.3em]">
            © 2026 EMDECOB · Master Workflow Engine v4.0
          </p>
        </div>
      </motion.div>
    </div>
  );
}
