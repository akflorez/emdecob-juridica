import { useState, useEffect, useMemo, Fragment } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, Calendar, Clock, FileText, Loader2, Filter, AlertCircle, 
  Download, User, Users, Building2, Hash, Paperclip, ChevronDown,
  FileDown, RefreshCw
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import { 
  getCaseByRadicado, 
  getCaseEvents, 
  downloadEventsExcel, 
  markCaseRead,
  getDocumentosActuacion,
  DocumentoActuacion
} from '@/services/api';

type DocsState = {
  items: any[];
  rawResponse: any;
  error?: string;
};

export default function CasoDetailPage() {
  const { radicado } = useParams<{ radicado: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [caseData, setCaseData] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingEvents, setIsLoadingEvents] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [searchText, setSearchText] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const [expandedDocs, setExpandedDocs] = useState<Record<number, DocsState>>({});
  const [loadingDocs, setLoadingDocs] = useState<Record<number, boolean>>({});

  const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';
  const cleanBaseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;

  useEffect(() => {
    if (!radicado) return;

    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      
      const decoded = decodeURIComponent(radicado);
      
      try {
        const result = await getCaseByRadicado(decoded);
        setCaseData(result);
        
        if (result.id && result.unread) {
          try { await markCaseRead(result.id); } catch {}
        }
        
        setIsLoadingEvents(true);
        try {
          const eventsResult = await getCaseEvents(decoded);
          setEvents(eventsResult.items || []);
        } catch (e: any) {
          console.error('Error cargando actuaciones:', e);
        } finally {
          setIsLoadingEvents(false);
        }
      } catch (e: any) {
        console.error('Error:', e);
        setError(e?.message || 'Error al cargar el caso');
        toast({
          title: 'Error al cargar el caso',
          description: e?.message || 'Error desconocido',
          variant: 'destructive',
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [radicado, toast]);

  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      if (searchText) {
        const search = searchText.toLowerCase();
        const title = (event.title || '').toLowerCase();
        const detail = (event.detail || '').toLowerCase();
        if (!title.includes(search) && !detail.includes(search)) return false;
      }
      if (dateFrom && event.event_date < dateFrom) return false;
      if (dateTo && event.event_date > dateTo) return false;
      return true;
    });
  }, [events, searchText, dateFrom, dateTo]);

  const actuacionesConDocumentos = useMemo(
    () => events.filter(e => e.con_documentos).length,
    [events]
  );

  const handleDownloadExcel = () => {
    if (!radicado) return;
    downloadEventsExcel(decodeURIComponent(radicado));
    toast({ title: 'Descargando...', description: 'El archivo Excel se descargará en unos segundos' });
  };

  const handleToggleDocumentos = async (event: any) => {
    const idReg: number = event.id_reg_actuacion;
    if (!idReg || !radicado) return;

    // Si ya está expandido → colapsar
    if (expandedDocs[idReg]) {
      setExpandedDocs(prev => {
        const copy = { ...prev };
        delete copy[idReg];
        return copy;
      });
      return;
    }

    setLoadingDocs(prev => ({ ...prev, [idReg]: true }));

    try {
      const decoded = decodeURIComponent(radicado);
      const result = await getDocumentosActuacion(decoded, idReg);

      setExpandedDocs(prev => ({
        ...prev,
        [idReg]: {
          items: result.items || [],
          rawResponse: result,
        },
      }));
    } catch (e: any) {
      console.error('Error cargando documentos:', e);
      setExpandedDocs(prev => ({
        ...prev,
        [idReg]: { items: [], rawResponse: null, error: e?.message || 'Error desconocido' },
      }));
      toast({
        title: 'Error al cargar documentos',
        description: e?.message || 'No se pudieron cargar los documentos',
        variant: 'destructive',
      });
    } finally {
      setLoadingDocs(prev => ({ ...prev, [idReg]: false }));
    }
  };

  const handleRefresh = async () => {
    if (!radicado) return;
    setIsLoading(true);
    setExpandedDocs({});
    const decoded = decodeURIComponent(radicado);
    try {
      const result = await getCaseByRadicado(decoded);
      setCaseData(result);
      const eventsResult = await getCaseEvents(decoded);
      setEvents(eventsResult.items || []);
      toast({ title: 'Actualizado', description: 'Información del caso actualizada' });
    } catch (e: any) {
      toast({ title: 'Error', description: e?.message || 'Error al actualizar', variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '—';
    try {
      const d = dateString.includes('T') ? dateString : `${dateString}T12:00:00`;
      return new Date(d).toLocaleDateString('es-CO', { year: 'numeric', month: 'long', day: 'numeric' });
    } catch { return dateString; }
  };

  const formatShortDate = (dateString: string) => {
    if (!dateString) return '—';
    try {
      const d = dateString.includes('T') ? dateString : `${dateString}T12:00:00`;
      return new Date(d).toLocaleDateString('es-CO', { year: 'numeric', month: 'short', day: 'numeric' });
    } catch { return dateString; }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error && !caseData) {
    return (
      <div className="space-y-6">
        <div className="flex items-start gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-2xl font-bold">Error</h1>
        </div>
        <Card className="border-red-500/50 bg-red-500/5">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <AlertCircle className="h-8 w-8 text-red-500" />
              <div>
                <h3 className="font-semibold">No se pudo cargar el caso</h3>
                <p className="text-sm text-muted-foreground mt-1">{error}</p>
              </div>
            </div>
            <div className="mt-4">
              <Button variant="outline" onClick={() => navigate(-1)}>Volver</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!caseData) return null;

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Detalle del Proceso</h1>
            <p className="font-mono text-primary text-sm mt-1">{caseData.radicado}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleRefresh} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualizar
          </Button>
          {events.length > 0 && (
            <Button onClick={handleDownloadExcel} variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Exportar Excel
            </Button>
          )}
        </div>
      </div>

      {/* Información General */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            Información General
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
            {[
              { icon: Hash,      label: 'RADICADO',          value: caseData.radicado,                    mono: true },
              { icon: User,      label: 'DEMANDANTE',        value: caseData.demandante || '—' },
              { icon: Users,     label: 'DEMANDADO',         value: caseData.demandado  || '—' },
              { icon: Building2, label: 'JUZGADO',           value: caseData.juzgado    || '—' },
              { icon: Calendar,  label: 'FECHA RADICACIÓN',  value: formatDate(caseData.fecha_radicacion) },
              { icon: Clock,     label: 'ÚLTIMA ACTUACIÓN',  value: formatDate(caseData.ultima_actuacion) },
            ].map(({ icon: Icon, label, value, mono }) => (
              <div key={label} className="space-y-1 p-3 rounded-lg bg-muted/30">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Icon className="h-3 w-3" />
                  {label}
                </div>
                <p className={`text-sm font-medium break-all ${mono ? 'font-mono' : ''}`}>{value}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Estadísticas */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-teal-500/10 border-teal-500/30">
          <CardContent className="pt-4 pb-4">
            <div className="text-2xl font-bold text-teal-500">{events.length}</div>
            <div className="text-xs text-muted-foreground">Total Actuaciones</div>
          </CardContent>
        </Card>
        <Card className="bg-blue-500/10 border-blue-500/30">
          <CardContent className="pt-4 pb-4">
            <div className="text-2xl font-bold text-blue-500">{actuacionesConDocumentos}</div>
            <div className="text-xs text-muted-foreground">Con Documentos</div>
          </CardContent>
        </Card>
        <Card className="bg-green-500/10 border-green-500/30">
          <CardContent className="pt-4 pb-4">
            <div className="text-2xl font-bold text-green-500 text-base">{formatShortDate(caseData.fecha_radicacion)}</div>
            <div className="text-xs text-muted-foreground">Inicio Proceso</div>
          </CardContent>
        </Card>
        <Card className="bg-orange-500/10 border-orange-500/30">
          <CardContent className="pt-4 pb-4">
            <div className="text-2xl font-bold text-orange-500 text-base">{formatShortDate(caseData.ultima_actuacion)}</div>
            <div className="text-xs text-muted-foreground">Última Actividad</div>
          </CardContent>
        </Card>
      </div>

      {/* Filtros */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <Filter className="h-5 w-5 text-primary" />
            Filtrar Actuaciones
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px]">
              <Input
                placeholder="Buscar en actuaciones..."
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
              />
            </div>
            <div className="w-[150px]">
              <label className="text-xs text-muted-foreground mb-1 block">Desde</label>
              <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
            </div>
            <div className="w-[150px]">
              <label className="text-xs text-muted-foreground mb-1 block">Hasta</label>
              <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
            </div>
            <Button variant="outline" onClick={() => { setSearchText(''); setDateFrom(''); setDateTo(''); }}>
              Limpiar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Tabla de Actuaciones */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              Actuaciones
            </CardTitle>
            <span className="text-sm text-muted-foreground bg-muted px-2 py-1 rounded">
              {filteredEvents.length} registros
            </span>
          </div>
        </CardHeader>
        <CardContent>
          {isLoadingEvents ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : filteredEvents.length === 0 ? (
            <div className="text-center py-12">
              <Calendar className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No hay actuaciones</p>
            </div>
          ) : (
            <div className="overflow-auto max-h-[600px] border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/50">
                    <TableHead className="w-[110px] sticky top-0 bg-muted z-10">Fecha</TableHead>
                    <TableHead className="w-[200px] sticky top-0 bg-muted z-10">Actuación</TableHead>
                    <TableHead className="sticky top-0 bg-muted z-10">Anotación</TableHead>
                    <TableHead className="w-[60px] sticky top-0 bg-muted z-10 text-center">Docs</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredEvents.map((event, i) => {
                    const idReg: number = event.id_reg_actuacion;
                    const isExpanded  = idReg ? !!expandedDocs[idReg] : false;
                    const isLoadingDoc = idReg ? loadingDocs[idReg]   : false;
                    const docsState: DocsState | undefined = idReg ? expandedDocs[idReg] : undefined;
                    const docs = docsState?.items || [];
                    const hasDocuments = event.con_documentos;

                    return (
                      <Fragment key={i}>
                        <TableRow className={isExpanded ? 'bg-primary/5' : ''}>

                          <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                            {formatShortDate(event.event_date)}
                          </TableCell>

                          <TableCell className="font-medium text-sm">{event.title || '—'}</TableCell>

                          <TableCell className="text-sm text-muted-foreground">
                            <p className="line-clamp-2">{event.detail || '—'}</p>
                          </TableCell>

                          {/* ── Clip clickeable (sin número) ── */}
                          <TableCell className="text-center">
                            {hasDocuments && idReg ? (
                              <button
                                onClick={() => handleToggleDocumentos(event)}
                                disabled={isLoadingDoc}
                                title="Ver documentos"
                                className="inline-flex items-center justify-center w-7 h-7 rounded bg-blue-500/10 text-blue-500 hover:bg-blue-500/25 transition-colors disabled:opacity-50"
                              >
                                {isLoadingDoc ? (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                ) : isExpanded ? (
                                  <ChevronDown className="h-3 w-3" />
                                ) : (
                                  <Paperclip className="h-3 w-3" />
                                )}
                              </button>
                            ) : (
                              <span className="text-muted-foreground text-xs">—</span>
                            )}
                          </TableCell>
                        </TableRow>

                        {/* ─── Fila expandida con documentos ─── */}
                        {isExpanded && docsState && (
                          <TableRow className="bg-primary/5 hover:bg-primary/5">
                            <TableCell colSpan={4} className="py-3">
                              <div className="pl-6">

                                <div className="text-xs font-medium text-muted-foreground mb-3 flex items-center gap-2">
                                  <Paperclip className="h-3 w-3" />
                                  DOCUMENTOS ADJUNTOS
                                </div>

                                {/* Error de red */}
                                {docsState.error && (
                                  <div className="flex items-center gap-2 text-sm text-red-500 p-3 bg-red-500/10 rounded-lg border border-red-500/30">
                                    <AlertCircle className="h-4 w-4 flex-shrink-0" />
                                    Error al consultar: {docsState.error}
                                  </div>
                                )}

                                {/* Sin documentos */}
                                {docs.length === 0 && !docsState.error && (
                                  <div className="flex items-center gap-2 text-sm text-muted-foreground p-3 bg-muted/30 rounded-lg border border-border">
                                    <AlertCircle className="h-4 w-4 flex-shrink-0" />
                                    No se encontraron documentos disponibles para esta actuación.
                                  </div>
                                )}

                                {/* Lista de documentos */}
                                {docs.length > 0 && (
                                  <div className="space-y-2">
                                    {docs.map((doc: any, j: number) => {
                                      const docId =
                                        doc.idRegDocumento       ??
                                        doc.idRegistroDocumento  ??
                                        doc.IdRegDocumento       ??
                                        doc.IdRegistroDocumento  ??
                                        doc.idDocumento          ??
                                        doc.id                   ??
                                        null;

                                      const docName =
                                        doc.nombre          ||
                                        doc.Nombre          ||
                                        doc.nombreDocumento ||
                                        doc.NombreDocumento ||
                                        doc.nombreArchivo   ||
                                        doc.NombreArchivo   ||
                                        `Documento ${j + 1}`;

                                      const docDate =
                                        doc.fechaCarga   ||
                                        doc.fechaCargue  ||
                                        doc.FechaCargue  ||
                                        doc.fechaRegistro ||
                                        doc.FechaRegistro ||
                                        doc.fecha        ||
                                        '';

                                      const downloadUrl = docId
                                        ? `${cleanBaseUrl}/documentos/${docId}/descargar`
                                        : null;

                                      return (
                                        <div
                                          key={j}
                                          className="flex items-center justify-between gap-4 p-3 rounded-lg bg-background border border-border shadow-sm"
                                        >
                                          <div className="flex items-center gap-3 min-w-0">
                                            <FileDown className="h-5 w-5 text-red-500 flex-shrink-0" />
                                            <div className="min-w-0">
                                              <p className="text-sm font-semibold truncate">{docName}</p>
                                              {docDate && (
                                                <p className="text-xs text-muted-foreground mt-0.5">
                                                  {formatShortDate(docDate)}
                                                </p>
                                              )}
                                            </div>
                                          </div>

                                          {downloadUrl ? (
                                            <a
                                              href={downloadUrl}
                                              target="_blank"
                                              rel="noopener noreferrer"
                                              className="inline-flex items-center gap-2 whitespace-nowrap rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 h-9 px-4 flex-shrink-0"
                                              onClick={() =>
                                                toast({
                                                  title: 'Descargando PDF',
                                                  description: 'El documento se abrirá en una nueva pestaña',
                                                })
                                              }
                                            >
                                              <Download className="h-4 w-4" />
                                              Descargar PDF
                                            </a>
                                          ) : (
                                            <Button disabled size="sm" variant="outline">
                                              No disponible
                                            </Button>
                                          )}
                                        </div>
                                      );
                                    })}
                                  </div>
                                )}

                              </div>
                            </TableCell>
                          </TableRow>
                        )}
                      </Fragment>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Línea de tiempo */}
      {filteredEvents.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Clock className="h-5 w-5 text-primary" />
              Últimas Actuaciones
            </CardTitle>
            <CardDescription>Las 5 actuaciones más recientes</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {filteredEvents.slice(0, 5).map((event, i) => (
                <div
                  key={i}
                  className="flex gap-4 p-3 rounded-lg bg-muted/30 border border-border/50"
                >
                  <div className="flex-shrink-0 w-2 h-2 mt-2 rounded-full bg-primary" />
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Calendar className="h-3 w-3" />
                        {formatDate(event.event_date)}
                      </div>
                      {event.con_documentos && (
                        <span className="inline-flex items-center gap-1 text-xs text-blue-500">
                          <Paperclip className="h-3 w-3" />
                          Docs
                        </span>
                      )}
                    </div>
                    <h4 className="font-medium text-sm">{event.title || 'Sin título'}</h4>
                    {event.detail && (
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{event.detail}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

    </div>
  );
}



