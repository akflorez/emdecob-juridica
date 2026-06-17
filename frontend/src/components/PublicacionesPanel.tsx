import React, { useEffect, useState } from 'react';
import { 
  FileDown, Download, Calendar, ExternalLink, 
  RefreshCw, Loader2, AlertCircle, FileText, CheckCircle2, HelpCircle
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { CasePublication, refreshCasePublications, refreshCasePublicationsById, getCaseByRadicado, getCaseById, getCasePublications, getCasePublicationsById, descartarPublicacion, aceptarPublicacion } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface PublicacionesPanelProps {
  radicado: string;
  caseId?: number;
  publications: CasePublication[];
  onRefresh: (newPubs: CasePublication[]) => void;
  isLoading?: boolean;
  // Nuevos campos de progreso
  initialSyncStatus?: string | null;
  initialSyncProgress?: number;
}

export function PublicacionesPanel({ 
  radicado, 
  caseId, 
  publications, 
  onRefresh, 
  isLoading: initialLoading,
  initialSyncStatus,
  initialSyncProgress = 0
}: PublicacionesPanelProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<string | null>(initialSyncStatus || null);
  const [syncProgress, setSyncProgress] = useState<number>(initialSyncProgress);
  const { toast } = useToast();

  useEffect(() => {
    setSyncStatus(initialSyncStatus || null);
  }, [initialSyncStatus]);

  useEffect(() => {
    setSyncProgress(initialSyncProgress);
  }, [initialSyncProgress]);

  
  const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';
  const cleanBaseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;

  const [busquedas, setBusquedas] = useState<any[]>([]);

  // Fetch inicial para obtener las búsquedas actuales y estado global
  useEffect(() => {
    const fetchInitialStatus = async () => {
      try {
        const result = caseId 
          ? await getCasePublicationsById(caseId)
          : await getCasePublications(radicado);
        
        if (result && !Array.isArray(result)) {
          setBusquedas(result.busquedas || []);
          const status = result.estado_busqueda || result.sync_pub_status;
          if (status) setSyncStatus(status);
          if (result.items) onRefresh(result.items);
        }
      } catch (e) {
        console.error("Error fetching initial status:", e);
      }
    };
    if (radicado) fetchInitialStatus();
  }, [radicado, caseId]);

  // Polling cada 8 segundos si hay búsquedas activas (pendientes o en procesamiento)
  useEffect(() => {
    let interval: any;
    
    const hasActiveSearches = busquedas.some(b => b.estado === 'pendiente' || b.estado === 'procesando');
    
    if (syncStatus === 'pendiente' || syncStatus === 'procesando' || isRefreshing || hasActiveSearches) {
      interval = setInterval(async () => {
        try {
          const result = caseId 
            ? await getCasePublicationsById(caseId)
            : await getCasePublications(radicado);
          
          if (result && !Array.isArray(result)) {
            const items = result.items || [];
            const status = result.estado_busqueda || result.sync_pub_status;
            const currentBusquedas = result.busquedas || [];
            
            setBusquedas(currentBusquedas);
            setSyncStatus(status);
            
            const stillActive = currentBusquedas.some((b: any) => b.estado === 'pendiente' || b.estado === 'procesando');
            
            if (!stillActive && status !== 'pendiente' && status !== 'procesando') {
              onRefresh(items);
              setIsRefreshing(false);
              if (interval) clearInterval(interval);
            }
          }
        } catch (e) {
          console.error("Error polling publications progress:", e);
        }
      }, 8000); 
    }

    return () => { if (interval) clearInterval(interval); };
  }, [syncStatus, isRefreshing, busquedas, radicado, caseId, onRefresh]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    setSyncStatus("procesando");
    
    try {
      const result = caseId 
        ? await refreshCasePublicationsById(caseId)
        : await refreshCasePublications(radicado);
        
      if (result.ok) {
        toast({
          title: 'Sincronización manual iniciada',
          description: result.message || 'Se ha forzado la búsqueda.',
        });
      }
    } catch (error: any) {
      setSyncStatus("error");
      toast({
        title: 'Error al solicitar sincronización',
        description: error.message || 'No se pudo conectar con el servidor.',
        variant: 'destructive',
      });
      setIsRefreshing(false);
    }
  };


  const formatDate = (dateString?: string | null) => {
    if (!dateString) return '—';
    try {
      const d = dateString.includes('T') ? dateString : `${dateString}T12:00:00`;
      return new Date(d).toLocaleDateString('es-CO', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      });
    } catch { return dateString; }
  };

  const parseComplementarios = (jsonStr?: string | null): Array<{ url: string; nombre: string; contiene_radicado?: boolean }> => {
    if (!jsonStr) return [];
    try {
      const parsed = JSON.parse(jsonStr);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  };

  if (initialLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const isSearching = busquedas.some(b => b.estado === 'pendiente' || b.estado === 'procesando') || syncStatus === 'pendiente' || syncStatus === 'procesando';

  return (
    <div className="space-y-4">
      {/* BANNER DE BÚSQUEDA ACTIVA */}
      {isSearching && (
        <Card className="bg-blue-500/5 border-blue-500/20 animate-in fade-in slide-in-from-top-2 duration-500">
          <CardContent className="pt-4 pb-4 flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin text-primary shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-semibold text-foreground">Buscando publicaciones procesales en segundo plano...</p>
              <p className="text-xs text-muted-foreground">El worker está procesando las búsquedas y aparecerán aquí automáticamente.</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* SECCIÓN DE BÚSQUEDAS EN COLA */}
      {busquedas.length > 0 && (
        <Card className="bg-muted/30 border-primary/20 animate-in fade-in slide-in-from-top-2 duration-500">
          <CardContent className="pt-4 pb-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium flex items-center gap-2">
                {isSearching && (
                  <RefreshCw className="h-4 w-4 animate-spin text-primary" />
                )}
                Cola de Búsquedas Automáticas
              </span>
            </div>
            
            <div className="space-y-2 mt-3">
              {busquedas.map((b, i) => (
                <div key={i} className="flex justify-between items-center text-xs bg-background p-2 rounded border">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="font-semibold">Mes: {b.mes_busqueda}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {b.estado === 'procesando' && <span className="text-blue-500 flex items-center gap-1"><Loader2 className="h-3 w-3 animate-spin"/> Procesando</span>}
                    {b.estado === 'pendiente' && <span className="text-amber-500">En cola</span>}
                    {b.estado === 'encontrada' && <span className="text-emerald-500">Encontrada</span>}
                    {b.estado === 'sin_resultado' && <span className="text-muted-foreground">Sin resultado</span>}
                    {b.estado === 'error' && <span className="text-destructive" title={b.error}>Error (Intento {b.intentos})</span>}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            Publicaciones Procesales (Portal de la Rama)
          </h3>
          <p className="text-sm text-muted-foreground">
            Documentos y estados detectados automáticamente para este radicado.
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleRefresh} 
            disabled={isRefreshing || syncStatus === 'pendiente' || syncStatus === 'procesando'}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing || syncStatus === 'pendiente' || syncStatus === 'procesando' ? 'animate-spin' : ''}`} />
            {isRefreshing || syncStatus === 'pendiente' || syncStatus === 'procesando' ? 'Buscando...' : 'Sincronizar ahora'}
          </Button>
        </div>
      </div>

      {(() => {
        const validadas = publications.filter(p => p.estado_validacion === 'validado');
        const requierenRevision = publications.filter(p => p.estado_validacion === 'requiere_revision');
        const descartadas = publications.filter(p => p.estado_validacion === 'descartado');

        if (publications.length === 0 && busquedas.filter(b => ['pendiente', 'procesando'].includes(b.estado)).length === 0) {
          return (
            <Card className="border-dashed">
              <CardContent className="py-12 flex flex-col items-center justify-center text-center">
                <div className="bg-muted p-3 rounded-full mb-4">
                  <FileDown className="h-10 w-10 text-muted-foreground" />
                </div>
                <h4 className="font-semibold text-lg">Sin publicaciones detectadas</h4>
                <p className="text-muted-foreground max-w-sm">
                  No hemos encontrado publicaciones en el portal para este radicado. 
                  Intenta sincronizar manualmente si crees que debería haber alguna.
                </p>
                <Button variant="link" onClick={handleRefresh} className="mt-2">
                  Volver a intentar búsqueda
                </Button>
              </CardContent>
            </Card>
          );
        }

        const renderTable = (pubsList: CasePublication[], isRevisionTab: boolean) => (
          <div className="border rounded-lg overflow-hidden bg-card text-card-foreground">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead className="w-[170px]">Fecha / Estado</TableHead>
                  <TableHead className="w-[200px]">Validación / Análisis</TableHead>
                  <TableHead>Detalle de Publicación</TableHead>
                  <TableHead className="w-[280px] text-right">Documentos y Fuente</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pubsList.map((pub) => (
                  <TableRow key={pub.id} className="hover:bg-muted/30 transition-colors">

                    {/* FECHA / ESTADO */}
                    <TableCell className="align-top space-y-1.5 py-4">
                      {pub.fecha_estado_electronico && (
                        <div className="flex items-center gap-1.5 text-xs">
                          <span className="text-[10px] uppercase font-bold text-muted-foreground bg-muted px-1.5 py-0.5 rounded shrink-0">Estado</span>
                          <span className="font-medium text-foreground">{formatDate(pub.fecha_estado_electronico)}</span>
                        </div>
                      )}
                      {pub.fecha_publicacion && (
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          <span className="text-[10px] uppercase font-bold bg-muted px-1.5 py-0.5 rounded shrink-0 font-medium">Pub.</span>
                          <span>{formatDate(pub.fecha_publicacion)}</span>
                        </div>
                      )}
                      {pub.numero_estado && (
                        <div className="mt-1">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
                            No. {pub.numero_estado}
                          </span>
                        </div>
                      )}
                    </TableCell>

                    {/* VALIDACIÓN / ANÁLISIS */}
                    <TableCell className="align-top space-y-2 py-4">
                      {pub.estado_validacion === 'validado' ? (
                        (pub.match_score === 0 && pub.motivo_match?.includes('Registro previo')) ? (
                          <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-500/10 text-slate-600 dark:text-slate-400 border border-slate-500/20">
                            <CheckCircle2 className="h-3 w-3 shrink-0" />
                            Validado (Legacy)
                          </div>
                        ) : pub.validado_manual ? (
                          <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-600/10 text-emerald-700 dark:text-emerald-400 border border-emerald-600/30">
                            <CheckCircle2 className="h-3 w-3 shrink-0" />
                            Validado Manual
                          </div>
                        ) : (
                          <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                            <CheckCircle2 className="h-3 w-3 shrink-0" />
                            Validado (Score: {pub.match_score})
                          </div>
                        )
                      ) : pub.estado_validacion === 'requiere_revision' ? (
                        <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                          <AlertCircle className="h-3 w-3 shrink-0" />
                          Revisión (Score: {pub.match_score})
                        </div>
                      ) : (
                        <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-destructive/10 text-destructive border border-destructive/20">
                          <HelpCircle className="h-3 w-3 shrink-0" />
                          Descartado {pub.descartado_manual && "Manual"}
                        </div>
                      )}
                      
                      {pub.match_type && (
                        <div className="text-xs">
                          <span className="font-bold text-muted-foreground text-[9px] uppercase bg-muted px-1.5 py-0.5 rounded">
                            Tipo: {pub.match_type}
                          </span>
                        </div>
                      )}

                      {(pub.motivo_match || pub.observacion || pub.observacion_revision) && (
                        <p className="text-[10px] text-muted-foreground leading-tight mt-1 max-w-[200px]">
                          {pub.motivo_match} {pub.observacion} {pub.observacion_revision && <span className="block mt-1 font-medium text-foreground">Obs: {pub.observacion_revision}</span>}
                        </p>
                      )}

                      {pub.texto_bloque_match && (
                        <div className="mt-2 bg-muted/40 border p-1.5 rounded-md text-[10px] text-muted-foreground break-words max-w-[220px] max-h-24 overflow-y-auto">
                          <span className="font-semibold block mb-0.5 text-[9px] uppercase tracking-wider">Bloque de Evidencia:</span>
                          "{pub.texto_bloque_match}"
                        </div>
                      )}
                    </TableCell>

                    {/* DETALLE DE PUBLICACIÓN */}
                    <TableCell className="align-top py-4 text-sm">
                      <div className="font-semibold text-foreground mb-1">
                        {pub.tipo_publicacion || 'Publicación'}
                      </div>
                      <p className="text-muted-foreground text-xs leading-relaxed max-w-md">
                        {pub.descripcion || 'Sin descripción disponible'}
                      </p>
                    </TableCell>

                      {/* ACCIONES Y DOCUMENTOS */}
                      <TableCell className="align-top text-right space-y-2 py-4">
                        
                        {/* Descarga Principal */}
                        {pub.url_fuente_principal ? (
                          <div>
                            <a 
                              href={pub.url_fuente_principal} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline bg-primary/5 hover:bg-primary/10 border border-primary/20 px-2.5 py-1.5 rounded-md transition-colors"
                            >
                              <Download className="h-3.5 w-3.5" />
                              {pub.tipo_fuente_principal === 'resumen_publicacion' ? 'Ver Resumen Estado' : 
                               pub.tipo_fuente_principal === 'cuadro_consultar_aqui' ? 'Ver Cuadro' : 
                               pub.tipo_fuente_principal === 'documento_estado' ? 'Ver Documento Estado' : 
                               'Ver Doc Principal'}
                            </a>
                          </div>
                        ) : pub.documento_url ? (
                          <div>
                            <a 
                              href={pub.documento_url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline bg-primary/5 hover:bg-primary/10 border border-primary/20 px-2.5 py-1.5 rounded-md transition-colors"
                            >
                              <Download className="h-3.5 w-3.5" />
                              Ver Documento
                            </a>
                          </div>
                        ) : (
                          <span className="text-xs text-muted-foreground italic">Sin documento principal</span>
                        )}

                        {/* Documentos Complementarios */}
                        {(() => {
                          const comps = parseComplementarios(pub.documentos_complementarios).filter(doc => doc.contiene_radicado);
                          if (comps.length === 0) return null;
                          return (
                            <div className="mt-2 space-y-1 text-left flex flex-col items-end border-t pt-2 border-dashed">
                              <span className="text-[9px] font-bold text-muted-foreground uppercase tracking-wider mb-1">Doc. Complementarios</span>
                              {comps.map((doc, idx) => (
                                <a 
                                  key={idx} 
                                  href={doc.url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 text-[11px] text-muted-foreground hover:text-primary hover:underline transition-colors max-w-[260px] truncate"
                                  title={doc.nombre}
                                >
                                  {doc.contiene_radicado ? (
                                    <CheckCircle2 className="h-3 w-3 text-emerald-500 shrink-0" />
                                  ) : (
                                    <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/40 shrink-0 mx-0.5 animate-pulse" />
                                  )}
                                  <span className="truncate">{doc.nombre || `Doc Complementario ${idx + 1}`}</span>
                                </a>
                              ))}
                            </div>
                          );
                        })()}

                        {/* Enlace original */}
                        {pub.source_url && (
                          <div className="pt-1.5">
                            <a 
                              href={pub.source_url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-[10px] text-muted-foreground hover:text-primary transition-colors"
                            >
                              <ExternalLink className="h-2.5 w-2.5" />
                              Ver en Portal Judicial
                            </a>
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
        );

        return (
          <div className="mt-4 space-y-4">
            {/* PUBLICACIONES VALIDADAS */}
            {validadas.length > 0 ? renderTable(validadas, false) : (
              <div className="text-center py-8 text-muted-foreground border rounded-lg bg-card">
                {busquedas.filter(b => ['pendiente', 'procesando'].includes(b.estado)).length > 0
                  ? "Buscando publicaciones procesales..."
                  : "No hay publicaciones validadas aún."}
              </div>
            )}

            {/* PUBLICACIONES QUE REQUIEREN REVISIÓN */}
            {requierenRevision.length > 0 && (
              <details className="group border rounded-lg overflow-hidden bg-amber-500/5 border-amber-500/20">
                <summary className="flex items-center gap-2 px-4 py-3 cursor-pointer select-none text-sm font-semibold text-amber-700 dark:text-amber-400 hover:bg-amber-500/10 transition-colors">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  {requierenRevision.length} publicación(es) que requieren revisión manual
                  <span className="ml-auto text-xs font-normal text-muted-foreground">Clic para ver/ocultar</span>
                </summary>
                <div className="border-t border-amber-500/20">
                  {renderTable(requierenRevision, true)}
                </div>
              </details>
            )}
          </div>
        );
      })()}

      <div className="bg-blue-500/5 border border-blue-500/20 p-4 rounded-lg flex gap-3">
        <AlertCircle className="h-5 w-5 text-blue-500 shrink-0" />
        <p className="text-xs text-blue-700 leading-relaxed">
          <strong>Nota del sistema:</strong> Esta información proviene del portal centralizado de Publicaciones Procesales. 
          Si el juzgado de este caso no publica en dicho portal, la lista podría estar vacía.
        </p>
      </div>
    </div>
  );
}
