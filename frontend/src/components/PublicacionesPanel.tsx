import React, { useEffect, useState } from 'react';
import { 
  FileDown, Download, Calendar, ExternalLink, 
  RefreshCw, Loader2, AlertCircle, FileText 
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { CasePublication, refreshCasePublications, refreshCasePublicationsById, getCaseByRadicado } from '@/services/api';
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

  // Polling para actualizar el progreso
  useEffect(() => {
    let interval: any;
    
    // Si hay progreso activo o acabamos de iniciar una búsqueda (isRefreshing)
    if ((syncProgress > 0 && syncProgress < 100) || isRefreshing) {
      interval = setInterval(async () => {
        try {
          const caseData = await getCaseByRadicado(radicado);
          if (caseData) {
            // Solo actualizamos si el servidor tiene un progreso válido
            if (caseData.sync_pub_status || (caseData.sync_pub_progress > 0)) {
              setSyncStatus(caseData.sync_pub_status);
              setSyncProgress(caseData.sync_pub_progress || 0);
            }
            
            // Si el servidor ya terminó (100% o status nulo pero ya teníamos progreso)
            if (caseData.sync_pub_progress === 100 || (syncProgress > 50 && !caseData.sync_pub_status)) {
              const result = caseId 
                ? await refreshCasePublicationsById(caseId)
                : await refreshCasePublications(radicado);
              if (result.ok && result.items) {
                onRefresh(result.items);
                setSyncProgress(0); // Ahora sí ocultamos
                setSyncStatus(null);
                setIsRefreshing(false);
                clearInterval(interval);
              }
            }
          }
        } catch (e) {
          console.error("Error polling progress:", e);
        }
      }, 2000); // Más frecuente (2 segundos) para mayor fluidez
    }

    return () => { if (interval) clearInterval(interval); };
  }, [syncProgress, isRefreshing, radicado, caseId, onRefresh]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    setSyncProgress(5); // Feedback inmediato
    setSyncStatus("Iniciando...");
    
    try {
      const result = caseId 
        ? await refreshCasePublicationsById(caseId)
        : await refreshCasePublications(radicado);
        
      if (result.ok && result.items) {
        // Si el backend respondió rápido con items
        onRefresh(result.items);
        setSyncProgress(0);
        setSyncStatus(null);
      } else if (result.ok) {
        toast({
          title: 'Sincronización iniciada',
          description: result.message || 'La búsqueda de publicaciones se está ejecutando en segundo plano.',
        });
        // El polling se activará porque syncProgress > 0
      }
    } catch (error: any) {
      setSyncProgress(0);
      setSyncStatus(null);
      toast({
        title: 'Error al sincronizar',
        description: error.message || 'No se pudo conectar con el portal de publicaciones.',
        variant: 'destructive',
      });
    } finally {
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

  if (initialLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* BARRA DE PROGRESO SENIOR */}
      {syncProgress > 0 && (
        <Card className="bg-muted/30 border-primary/20 animate-in fade-in slide-in-from-top-2 duration-500">
          <CardContent className="pt-6 pb-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-primary flex items-center gap-2">
                <RefreshCw className="h-4 w-4 animate-spin" />
                {syncStatus || 'Buscando publicaciones...'}
              </span>
              <span className="text-sm font-bold text-primary">{syncProgress}%</span>
            </div>
            <Progress value={syncProgress} className="h-2" />
            <p className="text-[10px] text-muted-foreground mt-2 italic text-center">
              Estamos escaneando el portal judicial y validando archivos unificados según tu radicado.
            </p>
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
        <Button 
          variant="outline" 
          size="sm" 
          onClick={handleRefresh} 
          disabled={isRefreshing || (syncProgress > 0 && syncProgress < 100)}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing || (syncProgress > 0 && syncProgress < 100) ? 'animate-spin' : ''}`} />
          {isRefreshing || (syncProgress > 0 && syncProgress < 100) ? 'Buscando...' : 'Sincronizar ahora'}
        </Button>
      </div>

      {publications.length === 0 && (syncProgress === 0 || syncProgress === 100) ? (
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
      ) : (
        (publications.length > 0) && (
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead className="w-[120px]">Fecha</TableHead>
                  <TableHead className="w-[150px]">Tipo</TableHead>
                  <TableHead>Descripción</TableHead>
                  <TableHead className="w-[160px] text-right">Acción</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {publications.map((pub) => (
                  <TableRow key={pub.id} className="hover:bg-muted/30 transition-colors">
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-3 w-3 text-muted-foreground" />
                        {formatDate(pub.fecha_publicacion)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-secondary text-secondary-foreground">
                        {pub.tipo_publicacion || 'Estado'}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {pub.descripcion || 'Sin descripción disponible'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex flex-col items-end gap-2">
                        {pub.documento_url ? (
                          <a 
                            href={pub.documento_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 text-sm text-blue-500 hover:text-blue-700 font-medium"
                          >
                            <Download className="h-4 w-4" />
                            Ver Documento
                          </a>
                        ) : (
                          <span className="text-xs text-muted-foreground italic">Doc. no disponible</span>
                        )}
                        
                        {pub.source_url && (
                          <a 
                            href={pub.source_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 text-xs text-muted-foreground hover:text-primary transition-colors"
                          >
                            <ExternalLink className="h-3 w-3" />
                            Ver en Portal Original
                          </a>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )
      )}

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
