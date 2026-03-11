import { User, Users, Building2, Tag, Clock, Calendar, CalendarClock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Case } from "@/types/cases";

interface CaseCardProps {
  caseData: Case & { raw_proceso?: any; created_at?: string; updated_at?: string };
  compact?: boolean;
}

function safeText(v: any) {
  const s = typeof v === "string" ? v.trim() : "";
  return s ? s : "—";
}

function formatDateSafe(dateString?: string | null) {
  if (!dateString) return "—";
  const d = new Date(dateString);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("es-CO", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

// Parsea "Demandante: NOMBRE | Demandado: NOMBRE" desde sujetosProcesales
function parseSujetosProcesales(sujetos?: string) {
  if (!sujetos) return { demandante: null, demandado: null };

  let demandante: string | null = null;
  let demandado: string | null = null;

  const demandanteMatch = sujetos.match(/Demandante:\s*([^|]+)/i);
  if (demandanteMatch) demandante = demandanteMatch[1].trim();

  const demandadoMatch = sujetos.match(/Demandado:\s*(.+?)(?:\s*\||$)/i);
  if (demandadoMatch) demandado = demandadoMatch[1].trim();

  return { demandante, demandado };
}

export function CaseCard({ caseData, compact = false }: CaseCardProps) {
  const rawProceso = caseData?.raw_proceso;

  // Parsear sujetos procesales desde raw_proceso
  const sujetosParsed = parseSujetosProcesales(rawProceso?.sujetosProcesales);

  // Usar datos parseados o los que vengan directos
  const radicado = safeText(caseData?.radicado);
  const demandante = safeText(sujetosParsed.demandante || caseData?.demandante);
  const demandado = safeText(sujetosParsed.demandado || caseData?.demandado);
  const juzgado = safeText(rawProceso?.despacho || caseData?.juzgado);
  const alias =
    typeof caseData?.alias === "string" && caseData.alias.trim() ? caseData.alias.trim() : null;

  /**
   * ✅ FECHAS (CORREGIDO)
   * Primero usar lo que viene del backend (DB): fecha_radicacion / ultima_actuacion
   * Si no vienen, usar raw_proceso (solo si ese endpoint lo incluye)
   */
  const fechaRadicacion = formatDateSafe(
    // @ts-expect-error: algunos tipos no incluyen snake_case, pero el backend sí lo envía
    (caseData as any)?.fecha_radicacion ?? rawProceso?.fechaProceso ?? null
  );

  const ultimaActuacion = formatDateSafe(
    // @ts-expect-error
    (caseData as any)?.ultima_actuacion ?? rawProceso?.fechaUltimaActuacion ?? null
  );

  // Fecha de consulta: creada en tu sistema
  const fechaConsulta = formatDateSafe(
    // @ts-expect-error
    (caseData as any)?.created_at ?? null
  );

  // Si quieres mostrar la última actualización del sistema (updated_at), descomenta:
  // const ultimaActualizacionSistema = formatDateSafe((caseData as any)?.updated_at ?? null);

  if (compact) {
    return (
      <Card className="card-hover">
        <CardContent className="pt-4">
          <div className="space-y-2">
            <p className="font-mono text-sm text-primary font-medium break-all">{radicado}</p>
            <p className="text-sm">
              <span className="text-muted-foreground">Demandante:</span> {demandante}
            </p>
            <p className="text-sm">
              <span className="text-muted-foreground">Demandado:</span> {demandado}
            </p>
            <p className="text-xs text-muted-foreground">{juzgado}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="card-hover">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-lg">
          <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          Ficha del Caso
        </CardTitle>
      </CardHeader>

      <CardContent>
        <div className="grid gap-4 md:grid-cols-2">
          {/* Radicado */}
          <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
            <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
              <Tag className="h-5 w-5 text-primary" />
            </div>
            <div className="min-w-0">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Radicado</p>
              <p className="font-mono text-sm font-medium mt-1 break-all">{radicado}</p>
            </div>
          </div>

          {/* Demandante */}
          <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
            <div className="w-10 h-10 rounded-lg bg-success/20 flex items-center justify-center flex-shrink-0">
              <User className="h-5 w-5 text-success" />
            </div>
            <div className="min-w-0">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Demandante</p>
              <p className="font-medium mt-1 break-words">{demandante}</p>
            </div>
          </div>

          {/* Demandado */}
          <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
            <div className="w-10 h-10 rounded-lg bg-warning/20 flex items-center justify-center flex-shrink-0">
              <Users className="h-5 w-5 text-warning" />
            </div>
            <div className="min-w-0">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Demandado</p>
              <p className="font-medium mt-1 break-words">{demandado}</p>
            </div>
          </div>

          {/* Juzgado */}
          <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
            <div className="w-10 h-10 rounded-lg bg-info/20 flex items-center justify-center flex-shrink-0">
              <Building2 className="h-5 w-5 text-info" />
            </div>
            <div className="min-w-0">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Juzgado</p>
              <p className="font-medium mt-1 break-words">{juzgado}</p>
            </div>
          </div>

          {/* Fecha de Radicación */}
          <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
            <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
              <Calendar className="h-5 w-5 text-primary" />
            </div>
            <div className="min-w-0">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Fecha de Radicación</p>
              <p className="font-medium mt-1">{fechaRadicacion}</p>
            </div>
          </div>

          {/* Última Actuación */}
          <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
            <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center flex-shrink-0">
              <CalendarClock className="h-5 w-5 text-accent" />
            </div>
            <div className="min-w-0">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Última Actuación</p>
              <p className="font-medium mt-1">{ultimaActuacion}</p>
            </div>
          </div>

          {/* Alias */}
          {alias && (
            <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
              <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center flex-shrink-0">
                <Tag className="h-5 w-5 text-accent" />
              </div>
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Alias</p>
                <p className="font-medium mt-1 break-words">{alias}</p>
              </div>
            </div>
          )}

          {/* Fecha de Consulta */}
          <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
            <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center flex-shrink-0">
              <Clock className="h-5 w-5 text-muted-foreground" />
            </div>
            <div className="min-w-0">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Fecha de Consulta</p>
              <p className="font-medium mt-1">{fechaConsulta}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
