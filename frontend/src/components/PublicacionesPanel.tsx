import React from 'react';
import { 
  FileDown, Download, Calendar, ExternalLink, 
  RefreshCw, Loader2, AlertCircle, FileText 
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { CasePublication, refreshCasePublications, refreshCasePublicationsById } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface PublicacionesPanelProps {
  radicado: string;
  caseId?: number;
  publications: CasePublication[];
  onRefresh: (newPubs: CasePublication[]) => void;
  isLoading?: boolean;
}

export function PublicacionesPanel({ radicado, caseId, publications, onRefresh, isLoading: initialLoading }: PublicacionesPanelProps) {
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const { toast } = useToast();

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const result = caseId 
        ? await refreshCasePublicationsById(caseId)
        : await refreshCasePublications(radicado);
        
      if (result.ok || (result as any).items) {
        onRefresh(result.items);
        toast({
          title: 'Sincronización completa',
          description: `Se encontraron ${result.items.length} publicaciones.`,
        });
      }
    } catch (error: any) {
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
          disabled={isRefreshing}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
          {isRefreshing ? 'Buscando...' : 'Sincronizar ahora'}
        </Button>
      </div>

      {publications.length === 0 ? (
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
                <TableRow key={pub.id}>
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
