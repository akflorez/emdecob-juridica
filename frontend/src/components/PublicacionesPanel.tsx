import React, { useEffect, useState } from 'react';
import { 
  FileDown, Download, Calendar, ExternalLink, 
  RefreshCw, Loader2, AlertCircle, FileText, CheckCircle2
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { CasePublication, refreshCasePublications, refreshCasePublicationsById, getCaseByRadicado, getCaseById, getCasePublications, getCasePublicationsById, descartarPublicacion, aceptarPublicacion, apiFetch } from '@/services/api';
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
  isSuperAdmin?: boolean;
}

export function PublicacionesPanel({ 
  radicado, 
  caseId, 
  publications, 
  onRefresh, 
  isLoading: initialLoading,
  initialSyncStatus,
  initialSyncProgress = 0,
  isSuperAdmin = false
}: PublicacionesPanelProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<string | null>(initialSyncStatus || null);
  const [syncProgress, setSyncProgress] = useState<number>(initialSyncProgress);
  const { toast } = useToast();

  const [companyId, setCompanyId] = useState<number | null>(null);
  const [activeJob, setActiveJob] = useState<any | null>(null);
  const [isStartingJob, setIsStartingJob] = useState(false);

  useEffect(() => {
    setSyncStatus(initialSyncStatus || null);
  }, [initialSyncStatus]);

  useEffect(() => {
    setSyncProgress(initialSyncProgress);
  }, [initialSyncProgress]);

  const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';
  const cleanBaseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;

  const [busquedas, setBusquedas] = useState<any[]>([]);

  // Fetch inicial para obtener las búsquedas actuales, estado global y ID de la empresa
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
          if (result.company_id) setCompanyId(result.company_id);
        }
      } catch (e) {
        console.error("Error fetching initial status:", e);
      }
    };
    if (radicado) fetchInitialStatus();
  }, [radicado, caseId]);

  // Verificar Job de Sincronización Masiva al cargar companyId
  const checkActiveJob = async (id: number) => {
    try {
      const companyParam = `?company_id=${id}`;
      const result = await apiFetch<{ job: any }>(`/publicaciones/sincronizacion-masiva/active${companyParam}`);
      if (result && result.job) {
        setActiveJob(result.job);
      } else {
        setActiveJob(null);
      }
    } catch (e) {
      console.error("Error checking active mass sync job:", e);
    }
  };

  useEffect(() => {
    if (companyId) {
      checkActiveJob(companyId);
    }
  }, [companyId]);

  // Polling para el Job masivo activo
  useEffect(() => {
    let interval: any;
    if (activeJob && (activeJob.estado === 'pendiente' || activeJob.estado === 'procesando')) {
      interval = setInterval(async () => {
        try {
          const jobStatus = await apiFetch<any>(`/publicaciones/sincronizacion-masiva/${activeJob.id}`);
          if (jobStatus) {
            setActiveJob(jobStatus);
            if (jobStatus.estado !== 'pendiente' && jobStatus.estado !== 'procesando') {
              toast({
                title: 'Sincronización masiva finalizada',
                description: `Se procesaron ${jobStatus.total_casos} casos y se crearon ${jobStatus.busquedas_creadas} búsquedas.`,
              });
              // Refrescar estado del caso actual
              const result = caseId 
                ? await getCasePublicationsById(caseId)
                : await getCasePublications(radicado);
              if (result && !Array.isArray(result)) {
                setBusquedas(result.busquedas || []);
                const status = result.estado_busqueda || result.sync_pub_status;
                if (status) setSyncStatus(status);
                if (result.items) onRefresh(result.items);
              }
              // Ocultar card de progreso después de 5 segundos
              setTimeout(() => {
                setActiveJob(null);
              }, 5000);
            }
          }
        } catch (e) {
          console.error("Error polling active mass sync job:", e);
        }
      }, 5000);
    }
    return () => { if (interval) clearInterval(interval); };
  }, [activeJob, radicado, caseId, onRefresh]);

  const handleStartMassSync = async (force: boolean = false) => {
    if (!companyId) {
      toast({
        title: 'Error',
        description: 'No se pudo determinar el ID de la empresa para sincronizar.',
        variant: 'destructive',
      });
      return;
    }
    setIsStartingJob(true);
    try {
      const res = await apiFetch<{ ok: boolean; job_id: number; message: string }>('/publicaciones/sincronizacion-masiva', {
        method: 'POST',
        body: JSON.stringify({
          company_id: companyId,
          force: force
        })
      });
      if (res.ok) {
        toast({
          title: 'Sincronización masiva iniciada',
          description: 'Estamos preparando las búsquedas de publicaciones para todos los radicados.',
        });
        // Obtener estado inicial del job
        const jobStatus = await apiFetch<any>(`/publicaciones/sincronizacion-masiva/${res.job_id}`);
        if (jobStatus) {
          setActiveJob(jobStatus);
        }
      }
    } catch (error: any) {
      toast({
        title: 'Error al iniciar sincronización',
        description: error.message || 'Ya existe un proceso activo o no se pudo conectar con el servidor.',
        variant: 'destructive',
      });
    } finally {
      setIsStartingJob(false);
    }
  };

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

  const handleAprobar = async (pubId: number) => {
    try {
      const res = await aceptarPublicacion(pubId);
      if (res.ok) {
        toast({
          title: 'Publicación aprobada',
          description: 'La publicación ahora es visible para el cliente.',
        });
        const updated = publications.map(p => 
          p.id === pubId ? { ...p, estado_validacion: 'validado' as const, requiere_revision: false } : p
        );
        onRefresh(updated);
      }
    } catch (e: any) {
      toast({
        title: 'Error al aprobar',
        description: e.message || 'No se pudo aprobar la publicación.',
        variant: 'destructive',
      });
    }
  };

  const handleDescartarClick = async (pubId: number) => {
    const motivo = window.prompt("Ingrese el motivo del descarte:", "No corresponde al caso");
    if (motivo === null) return;
    
    try {
      const res = await descartarPublicacion(pubId, motivo || "Descarte manual");
      if (res.ok) {
        toast({
          title: 'Publicación descartada',
          description: 'La publicación ha sido descartada internamente.',
        });
        const updated = publications.map(p => 
          p.id === pubId ? { ...p, estado_validacion: 'descartado' as const, requiere_revision: false } : p
        );
        onRefresh(updated);
      }
    } catch (e: any) {
      toast({
        title: 'Error al descartar',
        description: e.message || 'No se pudo descartar la publicación.',
        variant: 'destructive',
      });
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

      {/* BANNER DE SINCRONIZACIÓN MASIVA ACTIVA */}
      {activeJob && (
        <Card className="bg-primary/5 border-primary/20 shadow-sm animate-in fade-in slide-in-from-top-2 duration-500">
          <CardContent className="pt-4 pb-4 space-y-3">
            <div className="flex items-center gap-3">
              <RefreshCw className="h-5 w-5 animate-spin text-primary shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-foreground">
                  Sincronización Masiva de la Empresa ({activeJob.estado === 'pendiente' ? 'Preparando...' : 'Procesando...'})
                </p>
                <p className="text-xs text-muted-foreground">
                  Estamos preparando las búsquedas de publicaciones. Las publicaciones aparecerán automáticamente a medida que el sistema las procese.
                </p>
              </div>
              <span className="text-xs font-semibold bg-primary/10 text-primary px-2 py-0.5 rounded-full shrink-0">
                {activeJob.porcentaje}%
              </span>
            </div>
            
            <Progress value={activeJob.porcentaje} className="h-2 w-full" />
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-1 text-xs text-muted-foreground">
              <div>
                <span className="font-semibold text-foreground">Casos procesados:</span> {activeJob.casos_procesados} / {activeJob.total_casos}
              </div>
              <div>
                <span className="font-semibold text-foreground">Búsquedas creadas:</span> {activeJob.busquedas_creadas}
              </div>
              {activeJob.radicado_actual && (
                <div className="col-span-2 truncate">
                  <span className="font-semibold text-foreground">Radicado actual:</span> <span className="font-mono">{activeJob.radicado_actual}</span>
                </div>
              )}
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
        <div className="flex flex-col sm:flex-row gap-2">
          {!activeJob && companyId && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleStartMassSync(false)}
              disabled={isStartingJob}
              className="border-primary/50 text-primary hover:bg-primary/5"
            >
              {isStartingJob ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4 mr-2" />
              )}
              Sincronizar publicaciones de todos los radicados
            </Button>
          )}
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
        const validadas = publications.filter(p => 
          ['validado', 'validado_automatico', 'validado_por_fuente_oficial'].includes(p.estado_validacion || '')
        );
        const requierenRevision = publications.filter(p => p.estado_validacion === 'requiere_revision');

        const activeSearches = busquedas.filter(b => ['pendiente', 'procesando'].includes(b.estado));
        const errorSearches = busquedas.filter(b => b.estado === 'error');
        const hasActive = activeSearches.length > 0;
        const hasError = errorSearches.length > 0;

        let emptyTitle = 'Sin publicaciones detectadas';
        let emptyMessage = 'No se encontraron publicaciones en el portal para este radicado.';
        
        if (hasActive) {
          emptyTitle = 'Buscando publicaciones procesales...';
          emptyMessage = 'El worker está procesando las búsquedas y aparecerán aquí automáticamente.';
        } else if (hasError) {
          emptyTitle = 'Búsqueda incompleta';
          emptyMessage = 'No fue posible completar la búsqueda de algunos meses debido a un error técnico.';
        } else {
          emptyTitle = 'Sin publicaciones';
          emptyMessage = 'No se encontraron publicaciones en el portal para este radicado.';
        }

        const renderTable = (pubsList: CasePublication[], showTechnicalDetails: boolean = false) => (
          <div className="border rounded-lg overflow-hidden bg-card text-card-foreground">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead className="w-[180px]">Fecha</TableHead>
                  <TableHead>Publicación</TableHead>
                  {showTechnicalDetails && <TableHead className="w-[280px]">Auditoría Técnica</TableHead>}
                  <TableHead className="w-[260px] text-right">Documentos</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pubsList.map((pub) => (
                  <TableRow key={pub.id} className="hover:bg-muted/30 transition-colors">
                    {/* FECHA */}
                    <TableCell className="align-top space-y-1.5 py-4">
                      {pub.fecha_estado_electronico && (
                        <div className="flex items-center gap-1.5 text-xs">
                          <span className="text-[10px] uppercase font-bold text-muted-foreground bg-muted px-1.5 py-0.5 rounded shrink-0">Estado</span>
                          <span className="font-medium text-foreground">{formatDate(pub.fecha_estado_electronico)}</span>
                        </div>
                      )}
                      {pub.fecha_publicacion && (
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          <span className="text-[10px] uppercase font-bold bg-muted px-1.5 py-0.5 rounded shrink-0">Pub.</span>
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

                    {/* TIPO / DESCRIPCIÓN */}
                    <TableCell className="align-top py-4 text-sm">
                      <div className="font-semibold text-foreground mb-1 flex items-center gap-1.5">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                        {pub.tipo_publicacion || 'Publicación Procesal'}
                      </div>
                      <p className="text-muted-foreground text-xs leading-relaxed max-w-md">
                        {pub.descripcion || 'Publicación encontrada en el portal de la Rama Judicial.'}
                      </p>
                    </TableCell>

                    {/* AUDITORÍA TÉCNICA (Solo visible para SuperAdmin/debug) */}
                    {showTechnicalDetails && (
                      <TableCell className="align-top py-4 text-xs space-y-2">
                        <div className="flex flex-wrap gap-1.5 items-center">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                            ['validado', 'validado_automatico', 'validado_por_fuente_oficial'].includes(pub.estado_validacion || '')
                              ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
                              : pub.estado_validacion === 'requiere_revision'
                              ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20'
                              : 'bg-destructive/10 text-destructive border-destructive/20'
                          }`}>
                            {['validado', 'validado_automatico', 'validado_por_fuente_oficial'].includes(pub.estado_validacion || '') ? 'Validado' : pub.estado_validacion === 'requiere_revision' ? 'Revisión' : 'Descartado'} 
                            (Score: {pub.match_score})
                          </span>
                          {pub.match_type && (
                            <span className="text-[9px] font-extrabold uppercase bg-muted text-muted-foreground px-1.5 py-0.5 rounded border">
                              Tipo: {pub.match_type}
                            </span>
                          )}
                        </div>

                        {pub.motivo_match && (
                          <p className="text-[10px] text-muted-foreground leading-tight">
                            <strong>Motivo:</strong> {pub.motivo_match}
                          </p>
                        )}

                        {pub.texto_bloque_match && (
                          <details className="text-[10px] text-muted-foreground">
                            <summary className="cursor-pointer font-semibold hover:text-primary select-none text-[9px] uppercase tracking-wider">Ver bloque de evidencia</summary>
                            <div className="mt-1 bg-muted/50 p-1.5 rounded border max-h-24 overflow-y-auto whitespace-pre-wrap font-mono text-[9px]">
                              "{pub.texto_bloque_match}"
                            </div>
                          </details>
                        )}

                        {pub.estado_validacion === 'requiere_revision' && (
                          <div className="flex gap-2 pt-1">
                            <Button 
                              size="sm" 
                              onClick={() => handleAprobar(pub.id)}
                              className="h-7 px-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-bold uppercase rounded"
                            >
                              Aprobar
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => handleDescartarClick(pub.id)}
                              className="h-7 px-2.5 text-[10px] font-bold uppercase rounded border-amber-500/30 text-amber-600 hover:bg-amber-500/5 hover:text-amber-700"
                            >
                              Descartar
                            </Button>
                          </div>
                        )}
                      </TableCell>
                    )}

                    {/* DOCUMENTOS */}
                    <TableCell className="align-top text-right space-y-2 py-4">
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
                             'Ver Documento'}
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
                        <span className="text-xs text-muted-foreground italic">Sin documento</span>
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
                                className="inline-flex items-center gap-1 text-[11px] text-muted-foreground hover:text-primary hover:underline transition-colors max-w-[240px] truncate"
                                title={doc.nombre}
                              >
                                <CheckCircle2 className="h-3 w-3 text-emerald-500 shrink-0" />
                                <span className="truncate">{doc.nombre || `Documento ${idx + 1}`}</span>
                              </a>
                            ))}
                          </div>
                        );
                      })()}

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
            {validadas.length > 0 ? (
              renderTable(validadas, isSuperAdmin)
            ) : (
              <Card className="border-dashed">
                <CardContent className="py-12 flex flex-col items-center justify-center text-center">
                  <div className="bg-muted p-3 rounded-full mb-4">
                    {hasActive ? (
                      <Loader2 className="h-10 w-10 animate-spin text-primary" />
                    ) : hasError ? (
                      <AlertCircle className="h-10 w-10 text-destructive" />
                    ) : (
                      <FileDown className="h-10 w-10 text-muted-foreground" />
                    )}
                  </div>
                  <h4 className="font-semibold text-lg">{emptyTitle}</h4>
                  <p className="text-muted-foreground max-w-sm">
                    {emptyMessage}
                  </p>
                  {!hasActive && (
                    <Button variant="outline" onClick={handleRefresh} className="mt-4">
                      Volver a intentar búsqueda
                    </Button>
                  )}
                </CardContent>
              </Card>
            )}

            {/* PUBLICACIONES QUE REQUIEREN REVISIÓN (Solo visible para SuperAdmin) */}
            {isSuperAdmin && requierenRevision.length > 0 && (
              <details className="group border rounded-lg overflow-hidden bg-amber-500/5 border-amber-500/20">
                <summary className="flex items-center gap-2 px-4 py-3 cursor-pointer select-none text-sm font-semibold text-amber-700 dark:text-amber-400 hover:bg-amber-500/10 transition-colors">
                  <AlertCircle className="h-4 w-4 shrink-0 text-amber-500" />
                  {requierenRevision.length} publicación(es) que requieren revisión manual (Auditoría Técnica)
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
