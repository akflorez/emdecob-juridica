import { useState, useEffect, useMemo, Fragment } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, Calendar, Clock, FileText, Loader2, Filter, AlertCircle, 
  Download, User, Users, Building2, Hash, Paperclip, ChevronDown,
  FileDown, RefreshCw, ArrowRight, UserCheck, Edit3, ChevronRight
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
  getCaseById, 
  getCaseEventsById, 
  getCasePublicationsById,
  getCaseTasks,
  getTasks,
  getUsers,
  type User,
  type Task as TaskType
} from '@/services/api';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PublicacionesPanel } from '@/components/PublicacionesPanel';
import { CheckCircle2, ListPlus, MoreVertical, MessageSquare, Plus } from 'lucide-react';
import { TaskDrawer } from '@/components/TaskDrawer';

type DocsState = {
  items: any[];
  rawResponse: any;
  error?: string;
};

export default function CasoDetailPage() {
  const { radicado, id } = useParams<{ radicado: string, id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [caseData, setCaseData] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [publications, setPublications] = useState<CasePublication[]>([]);
  const [tasks, setTasks] = useState<TaskType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingEvents, setIsLoadingEvents] = useState(false);
  const [isLoadingPubs, setIsLoadingPubs] = useState(false);
  const [isLoadingTasks, setIsLoadingTasks] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [multipleCases, setMultipleCases] = useState<any[] | null>(null);
  const [selectedTask, setSelectedTask] = useState<TaskType | null>(null);
  const [systemUsers, setSystemUsers] = useState<User[]>([]);
  const [clickupToken, setClickupToken] = useState<string | null>(null);
  
  const [searchText, setSearchText] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const [expandedDocs, setExpandedDocs] = useState<Record<number, DocsState>>({});
  const [loadingDocs, setLoadingDocs] = useState<Record<number, boolean>>({});

  const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';
  const cleanBaseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;

  useEffect(() => {
    const token = localStorage.getItem('clickup_token');
    if (token) setClickupToken(token);
  }, []);

  useEffect(() => {
    if (!radicado && !id) return;

    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      setMultipleCases(null);
      
      try {
        let result: any = null;
        let activeRadicado = '';

        if (id) {
          result = await getCaseById(Number(id));
          activeRadicado = result.radicado;
          
          setIsLoadingEvents(true);
          setIsLoadingPubs(true);
          try {
            const [eventsResult, pubsResult] = await Promise.all([
              getCaseEventsById(Number(id)),
              getCasePublicationsById(Number(id))
            ]);
            setEvents(eventsResult.items || []);
            setPublications(pubsResult.items || []);
          } catch (e) {
            console.error('Error cargando adicionales por ID:', e);
          } finally {
            setIsLoadingEvents(false);
            setIsLoadingPubs(false);
          }
        } else if (radicado) {
          const decoded = decodeURIComponent(radicado);
          const results = await getCaseByRadicado(decoded);
          
          if (results.length === 1) {
            result = results[0];
            activeRadicado = result.radicado;
            
            setIsLoadingEvents(true);
            setIsLoadingPubs(true);
            try {
              const [eventsResult, pubsResult] = await Promise.all([
                getCaseEventsById(result.id),
                getCasePublicationsById(result.id)
              ]);
              setEvents(eventsResult.items || []);
              setPublications(pubsResult.items || []);
            } catch (e) {
              console.error('Error cargando adicionales por radicado:', e);
            } finally {
              setIsLoadingEvents(false);
              setIsLoadingPubs(false);
            }
          } else if (results.length > 1) {
            setMultipleCases(results);
            setIsLoading(false);
            return;
          } else {
            throw new Error("No se encontró el caso");
          }
        }

        if (!result) return;
        
        setCaseData(result);
        
        // Cargar tareas relacionadas
        setIsLoadingTasks(true);
        try {
          const tResult = await getTasks({ radicado: activeRadicado });
          setTasks(tResult);
        } catch (e) {
          console.error("Error cargando tareas:", e);
        } finally {
          setIsLoadingTasks(false);
        }

        if (result.id && result.unread) {
          try { await markCaseRead(result.id); } catch {}
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
    getUsers().then(setSystemUsers).catch(console.error);
  }, [radicado, id, toast]);

  const handleUpdateLawyer = async (newLawyer: string) => {
    if (!caseData?.id) return;
    try {
      const res = await updateCaseLawyer(caseData.id, newLawyer);
      setCaseData({ ...caseData, abogado: res.abogado, user_id: res.user_id } as any);
      toast({ title: 'Abogado actualizado', description: `Asignado a: ${res.abogado}` });
    } catch (e) {
      toast({ title: 'Error', description: 'No se pudo actualizar el abogado', variant: 'destructive' });
    }
  };

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
    if (id || caseData?.id) {
      downloadEventsByIdExcel(Number(id || caseData?.id));
    } else if (radicado || caseData?.radicado) {
      const r = radicado || caseData?.radicado;
      if (r) downloadEventsExcel(decodeURIComponent(r));
    } else {
      return;
    }
    toast({ title: 'Descargando...', description: 'El archivo Excel se descargará en unos segundos' });
  };

  const handleToggleDocumentos = async (event: any) => {
    const idReg: number = event.id_reg_actuacion;
    const r = radicado || caseData?.radicado;
    if (!idReg || !r) return;

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
    const r = radicado || caseData?.radicado;
    if (!r) return;
    setIsLoading(true);
    setExpandedDocs({});
    const decoded = decodeURIComponent(r);
    try {
      // Si tenemos ID, usamos ID para ser precisos
      if (id || caseData?.id) {
        const result = await getCaseById(Number(id || caseData?.id));
        setCaseData(result);
        
        const [eventsResult, pubsResult, tasksResult] = await Promise.all([
          getCaseEventsById(result.id),
          getCasePublicationsById(result.id),
          getCaseTasks(result.id)
        ]);
        
        setEvents(eventsResult.items || []);
        setPublications(pubsResult.items || []);
        setTasks(tasksResult || []);
      } else {
        // Fallback a radicado (solo si no hay ID, ej. búsqueda inicial)
        const results = await getCaseByRadicado(decoded);
        if (results.length === 1) {
          setCaseData(results[0]);
          const [eventsResult, pubsResult, tasksResult] = await Promise.all([
            getCaseEventsById(results[0].id),
            getCasePublicationsById(results[0].id),
            getCaseTasks(results[0].id)
          ]);
          setEvents(eventsResult.items || []);
          setPublications(pubsResult.items || []);
          setTasks(tasksResult || []);
        } else if (results.length > 1) {
          setMultipleCases(results);
        } else {
          throw new Error("No se encontró el caso");
        }
      }
      
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

  const handleCreateTask = () => {
    if (!caseData) return;
    
    let assigneeId: number | undefined = undefined;
    if (caseData.abogado && systemUsers.length > 0) {
      const match = systemUsers.find(u => 
        u.nombre?.toLowerCase().includes(caseData.abogado!.toLowerCase()) || 
        caseData.abogado!.toLowerCase().includes(u.nombre?.toLowerCase() || '')
      );
      if (match) assigneeId = match.id;
    }

    const newTaskStub = {
      title: '',
      description: `Gestión para Radicado: ${caseData.radicado}`,
      status: 'to do',
      priority: 'normal',
      case_id: caseData.id,
      assignee_id: assigneeId,
      list_id: 1
    } as any;

    setSelectedTask(newTaskStub);
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

  if (multipleCases) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-2xl font-bold">Múltiples procesos encontrados</h1>
        </div>
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="pt-6">
            <p className="mb-6">El radicado <strong>{radicado}</strong> tiene varios procesos registrados. Por favor selecciona el que deseas ver:</p>
            <div className="grid gap-4">
              {multipleCases.map(c => (
                <Card key={c.id} className="cursor-pointer hover:bg-muted/50 transition-colors border-primary/20" onClick={() => navigate(`/casos/id/${c.id}`)}>
                  <CardContent className="p-4 flex justify-between items-center">
                    <div>
                      <p className="font-semibold text-primary">{c.juzgado || 'Juzgado no especificado'}</p>
                      <p className="text-sm text-muted-foreground">ID Proceso: {c.id_proceso || 'N/A'}</p>
                      <p className="text-sm text-muted-foreground">{c.demandante} vs {c.demandado}</p>
                    </div>
                    <ArrowRight className="h-5 w-5 text-muted-foreground" />
                  </CardContent>
                </Card>
              ))}
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
            
            {/* ABOGADO SELECTOR */}
            <div className="space-y-1 p-3 rounded-lg bg-primary/5 border border-primary/10">
              <div className="flex items-center gap-2 text-xs text-primary font-semibold">
                <UserCheck className="h-3 w-3" />
                ABOGADO RESPONSABLE
              </div>
              <select 
                className="w-full bg-transparent text-sm font-bold border-none focus:ring-0 cursor-pointer text-primary"
                value={caseData.abogado || ''}
                onChange={(e) => handleUpdateLawyer(e.target.value)}
              >
                <option value="">Sin asignar</option>
                {systemUsers.map(u => (
                  <option key={u.id} value={u.nombre || u.username}>{u.nombre || u.username}</option>
                ))}
              </select>
            </div>

            {/* ID PROCESO (MANUAL OVERRIDE) - SENIOR FEATURE */}
            <div className="space-y-1 p-3 rounded-lg bg-orange-500/5 border border-orange-500/10">
              <div className="flex items-center gap-2 text-xs text-orange-600 font-semibold">
                <ChevronRight className="h-3 w-3" />
                ID PROCESO (RAMA)
              </div>
              <div className="flex items-center gap-2">
                <input 
                  type="text"
                  placeholder="Sin ID"
                  className="w-full bg-transparent text-sm font-mono font-bold border-none focus:ring-0 p-0 text-orange-700"
                  defaultValue={caseData.id_proceso || ''}
                  onBlur={(e) => {
                    if (e.target.value !== caseData.id_proceso) {
                      updateCaseIdProceso(caseData.id, e.target.value)
                        .then(() => toast.success("ID Judicial actualizado"))
                        .catch(() => toast.error("Error al actualizar ID"));
                    }
                  }}
                />
                <Edit3 className="h-3 w-3 text-orange-400" />
              </div>
            </div>
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

      {/* Contenido con Tabs */}
      <Tabs defaultValue="actuaciones" className="w-full">
        <TabsList className="grid w-full max-w-[600px] grid-cols-3 mb-4">
          <TabsTrigger value="actuaciones" className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Actuaciones
          </TabsTrigger>
          <TabsTrigger value="publicaciones" className="flex items-center gap-2">
            <FileDown className="h-4 w-4" />
            Publicaciones
          </TabsTrigger>
          <TabsTrigger value="tareas" className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            Tareas de Gestión
          </TabsTrigger>
        </TabsList>

        <TabsContent value="actuaciones">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary" />
                  Historial de Actuaciones
                </CardTitle>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-muted-foreground bg-muted px-2 py-1 rounded">
                    {filteredEvents.length} registros
                  </span>
                </div>
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

                            {isExpanded && docsState && (
                              <TableRow className="bg-primary/5 hover:bg-primary/5">
                                <TableCell colSpan={4} className="py-3">
                                  <div className="pl-6">

                                    <div className="text-xs font-medium text-muted-foreground mb-3 flex items-center gap-2">
                                      <Paperclip className="h-3 w-3" />
                                      DOCUMENTOS ADJUNTOS
                                    </div>

                                    {docsState.error && (
                                      <div className="flex items-center gap-2 text-sm text-red-500 p-3 bg-red-500/10 rounded-lg border border-red-500/30">
                                        <AlertCircle className="h-4 w-4 flex-shrink-0" />
                                        Error al consultar: {docsState.error}
                                      </div>
                                    )}

                                    {docs.length === 0 && !docsState.error && (
                                      <div className="flex items-center gap-2 text-sm text-muted-foreground p-3 bg-muted/30 rounded-lg border border-border">
                                        <AlertCircle className="h-4 w-4 flex-shrink-0" />
                                        No se encontraron documentos disponibles para esta actuación.
                                      </div>
                                    )}

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
        </TabsContent>

        <TabsContent value="publicaciones">
          <Card>
            <CardContent className="pt-6">
              <PublicacionesPanel 
                radicado={caseData?.radicado || decodeURIComponent(radicado || '')} 
                caseId={caseData?.id}
                publications={publications}
                isLoading={isLoadingPubs}
                onRefresh={(newPubs) => setPublications(newPubs)}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tareas">
          <Card className="border-primary/20">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-lg flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-primary" />
                  Tareas Vinculadas
                </CardTitle>
                <CardDescription>Seguimiento de gestión para este radicado</CardDescription>
              </div>
              <Button size="sm" onClick={handleCreateTask} className="bg-primary hover:bg-primary/90 shadow-lg shadow-primary/20 transition-all">
                <ListPlus className="h-4 w-4 mr-2" />
                Lanzar Tarea
              </Button>
            </CardHeader>
            <CardContent>
              {isLoadingTasks ? (
                <div className="flex justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : tasks.length === 0 ? (
                <div className="text-center py-12 border-2 border-dashed rounded-xl bg-muted/10">
                  <CheckCircle2 className="h-12 w-12 mx-auto text-muted-foreground opacity-20 mb-4" />
                  <p className="text-muted-foreground font-medium">No hay tareas de gestión vinculadas.</p>
                  <Button variant="outline" className="mt-4 rounded-full" onClick={handleCreateTask}>
                    <Plus className="h-4 w-4 mr-2" />
                    Crear primera tarea
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {(() => {
                    const parents = tasks.filter(t => !t.parent_id);
                    const subs = tasks.reduce((acc, t) => {
                      if (t.parent_id) {
                        if (!acc[t.parent_id]) acc[t.parent_id] = [];
                        acc[t.parent_id].push(t);
                      }
                      return acc;
                    }, {} as Record<number, TaskType[]>);

                    return parents.map(task => (
                      <div key={task.id} className="space-y-2">
                        <TaskItem task={task} onSelect={setSelectedTask} />
                        {subs[task.id] && (
                          <div className="ml-10 space-y-2 border-l-2 border-dashed border-primary/20 pl-4 py-1">
                            {subs[task.id].map(sub => (
                              <TaskItem key={sub.id} task={sub} onSelect={setSelectedTask} isSubtask />
                            ))}
                          </div>
                        )}
                      </div>
                    ));
                  })()}
                </div>
              )}
            </CardContent>
          </Card>
          
          <TaskDrawer 
            task={selectedTask} 
            open={!!selectedTask} 
            onOpenChange={(open) => !open && setSelectedTask(null)}
            onTaskUpdate={(updated) => {
              setTasks(prev => prev.map(t => t.id === updated.id ? updated : t));
              setSelectedTask(updated); // refrescar drawer data en vivo
            }}
            clickupToken={clickupToken || undefined}
            allAssignees={Array.from(new Set([...tasks.map(t => t.assignee_name), ...systemUsers.map(u => u.nombre || u.username)].filter(Boolean))) as string[]}
          />
        </TabsContent>
      </Tabs>

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

function TaskItem({ task, onSelect, isSubtask }: { task: TaskType; onSelect: (t: TaskType) => void; isSubtask?: boolean }) {
  const { toast } = useToast();
  
  return (
    <div 
      onClick={() => onSelect(task)}
      className={`group relative flex items-center justify-between transition-all duration-200 cursor-pointer border rounded-xl overflow-hidden shadow-sm hover:shadow-md ${
        isSubtask 
          ? 'p-2 bg-background/50 hover:bg-background border-dashed ml-2' 
          : 'p-4 bg-card hover:bg-muted/30 border-border/60'
      }`}
    >
      <div className={`absolute left-0 top-0 bottom-0 w-1 ${
        task.status === 'complete' ? 'bg-green-500' : 
        task.priority === 'urgent' ? 'bg-red-500' : 
        'bg-primary'
      }`} />

      <div className="flex items-center gap-4 min-w-0">
        <div className={`flex-shrink-0 ${isSubtask ? 'h-6 w-6' : 'h-8 w-8'} flex items-center justify-center rounded-full bg-muted/50 text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary transition-colors`}>
          <CheckCircle2 className={`${isSubtask ? 'h-3 w-3' : 'h-4 w-4'}`} />
        </div>
        <div className="flex flex-col min-w-0">
          <h4 className={`font-semibold ${isSubtask ? 'text-xs' : 'text-sm'} truncate max-w-[300px]`}>
            {task.title || 'Sin título'}
          </h4>
          <div className="flex items-center gap-3 mt-0.5">
            <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded-md ${
              task.status === 'complete' ? 'bg-green-500/10 text-green-600' : 'bg-primary/10 text-primary'
            }`}>
              {task.status}
            </span>
            {task.due_date && (
              <span className="flex items-center gap-1 text-[10px] text-muted-foreground font-medium">
                <Calendar className="h-3 w-3" />
                {new Date(task.due_date).toLocaleDateString('es-CO', {day: 'numeric', month: 'short'})}
              </span>
            )}
            {task.assignee_name && (
              <span className="flex items-center gap-1 text-[10px] text-muted-foreground font-medium">
                <User className="h-3 w-3" />
                {task.assignee_name}
              </span>
            )}
            <span className="flex items-center gap-1 text-[10px] text-muted-foreground font-medium">
              <Clock className="h-3 w-3" />
              {task.priority || 'Normal'}
            </span>
            {task.tags && task.tags.length > 0 && (
              <div className="flex gap-1 ml-1">
                {task.tags.map(tag => (
                  <div 
                    key={tag.id} 
                    className="h-1 w-3 rounded-full" 
                    style={{ backgroundColor: tag.color || '#3b82f6' }}
                    title={tag.name}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 pr-2">
        <ChevronRight className="h-4 w-4 text-muted-foreground/40 group-hover:text-primary transition-colors" />
      </div>
    </div>
  );
}



