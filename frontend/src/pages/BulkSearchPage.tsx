import { useState, useEffect, useRef } from "react";
import { 
  Upload, 
  FileSpreadsheet, 
  Search, 
  Loader2, 
  CheckCircle2, 
  AlertCircle, 
  ChevronRight, 
  History, 
  Trash2,
  Database
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { 
  uploadNamesSearch, 
  getSearchJob, 
  getLatestSearchJob,
  importSearchResults, 
  downloadSearchResultsExcel,
  type SearchJobResponse 
} from "@/services/api";

export default function BulkSearchPage() {
  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<number | null>(null);
  const [job, setJob] = useState<SearchJobResponse | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const { toast } = useToast();
  
  const pollInterval = useRef<NodeJS.Timeout | null>(null);

  // Cargar último trabajo al montar si existe y no ha sido importado
  useEffect(() => {
    const fetchLatest = async () => {
      try {
        const latestJob = await getLatestSearchJob();
        if (latestJob && (!latestJob.is_imported || latestJob.status === 'processing' || latestJob.status === 'pending')) {
          setJobId(latestJob.id);
          setJob(latestJob);
        }
      } catch (error) {
        console.error("Error fetching latest job:", error);
      }
    };
    fetchLatest();

    return () => {
      if (pollInterval.current) clearInterval(pollInterval.current);
    };
  }, []);

  // Polling de estado del trabajo
  useEffect(() => {
    if (jobId && (!job || (job.status === 'pending' || job.status === 'processing'))) {
      if (!pollInterval.current) {
        pollInterval.current = setInterval(async () => {
          try {
            const data = await getSearchJob(jobId);
            setJob(data);
            if (data.status === 'completed' || data.status === 'failed') {
              if (pollInterval.current) clearInterval(pollInterval.current);
              pollInterval.current = null;
            }
          } catch (error) {
            console.error("Error polling job:", error);
          }
        }, 3000);
      }
    } else if (pollInterval.current) {
      clearInterval(pollInterval.current);
      pollInterval.current = null;
    }
  }, [jobId, job]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    try {
      const { job_id } = await uploadNamesSearch(file, fromDate, toDate);
      setJobId(job_id);
      toast({ title: "Búsqueda iniciada", description: "Estamos consultando la Rama Judicial en segundo plano" });
    } catch (error: any) {
      toast({ title: "Error al subir archivo", description: error.message, variant: "destructive" });
    } finally {
      setIsUploading(false);
    }
  };

  const handleImport = async () => {
    if (!jobId || !job || job.status !== 'completed') return;
    setIsImporting(true);
    try {
      // Por ahora importamos todos los "selected" automáticos que tengan radicado
      const indices = job.results
        .filter(r => r.selected)
        .map(r => r.index);
        
      const res = await importSearchResults(jobId, indices);
      toast({ title: "Importación exitosa", description: `Se importaron ${res.imported} radicados nuevos` });
      // Limpiar estado
      setFile(null);
      setJobId(null);
      setJob(null);
    } catch (error: any) {
      toast({ title: "Error al importar", description: error.message, variant: "destructive" });
    } finally {
      setIsImporting(false);
    }
  };

  const handleExport = async () => {
    if (!jobId) return;
    setIsExporting(true);
    try {
      await downloadSearchResultsExcel(jobId);
      toast({ title: "Exportación exitosa", description: "El reporte Excel ha sido descargado" });
    } catch (error: any) {
      toast({ title: "Error al exportar", description: error.message, variant: "destructive" });
    } finally {
      setIsExporting(false);
    }
  };

  const progress = job ? Math.round((job.processed_items / (job.total_items || 1)) * 100) : 0;

  return (
    <div className="container p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Búsqueda Masiva de Procesos</h1>
        <p className="text-muted-foreground">
          Sube un archivo Excel para buscar radicados por nombre de demandado de forma automática y robusta.
        </p>
      </div>

      {!jobId ? (
        <Card className="border-dashed border-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5 text-primary" />
              Subir Excel de Búsqueda
            </CardTitle>
            <CardDescription>
              El archivo debe contener las columnas: DEPARTAMENTO, DEMANDADO 1, DEMANDADO 2 (opcional), CEDULA, ABOGADO.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-center w-full">
              <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer bg-accent/20 hover:bg-accent/40 transition-colors">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <FileSpreadsheet className="w-8 h-8 mb-3 text-muted-foreground" />
                  <p className="mb-2 text-sm">
                    <span className="font-semibold">{file ? file.name : "Click para seleccionar"}</span>
                  </p>
                  <p className="text-xs text-muted-foreground">XLSX, XLS (Máximo 1000 nombres)</p>
                </div>
                <input type="file" className="hidden" accept=".xlsx,.xls" onChange={handleFileChange} />
              </label>
            </div>

            <div className="flex gap-4 w-full">
              <div className="flex-1 space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Fecha Desde (Opcional)</label>
                <Input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
              </div>
              <div className="flex-1 space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Fecha Hasta (Opcional)</label>
                <Input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
              </div>
            </div>
            <Button 
              className="w-full h-12 text-lg" 
              disabled={!file || isUploading} 
              onClick={handleUpload}
            >
              {isUploading ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : <Search className="mr-2 h-5 w-5" />}
              {isUploading ? "Analizando archivo..." : "Iniciar Búsqueda Masiva"}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Loader2 className={`h-5 w-5 ${job?.status === 'processing' ? 'animate-spin text-primary' : ''}`} />
                  {job?.status === 'completed' ? "Búsqueda Finalizada" : "Buscando en Rama Judicial..."}
                </CardTitle>
                <CardDescription>
                  Procesando {job?.processed_items} de {job?.total_items} nombres
                </CardDescription>
              </div>
              <Badge variant={job?.status === 'completed' ? 'secondary' : 'outline'}>
                {job?.status?.toUpperCase()}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <div className="flex justify-between text-sm font-medium">
                <span>Progreso General</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>

            {job?.status === 'completed' && job.results && (
              <div className="space-y-4">
                <div className="rounded-md border overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-muted">
                      <tr>
                        <th className="p-3 text-left">Nombre Buscado</th>
                        <th className="p-3 text-left">Departamento</th>
                        <th className="p-3 text-left">Radicados Encontrados</th>
                        <th className="p-3 text-left">Seleccionado (Reciente)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {job.results.slice(0, 10).map((res: any, i: number) => (
                        <tr key={i} className="hover:bg-accent/10 transition-colors">
                          <td className="p-3 font-medium">{res.input_name1}</td>
                          <td className="p-3 text-muted-foreground">{res.id_depto}</td>
                          <td className="p-3 text-center">
                            <Badge variant="outline">{res.found_count}</Badge>
                          </td>
                          <td className="p-3">
                            {res.selected ? (
                              <div className="flex flex-col">
                                <span className="text-xs font-semibold">
                                  {res.selected.llaveProceso || res.selected.numero}
                                </span>
                                <span className="text-[10px] text-muted-foreground">{res.selected.fechaRadicacion}</span>
                              </div>
                            ) : (
                              <span className="text-xs text-destructive">No encontrado</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {job.results.length > 10 && (
                    <div className="p-3 text-center text-xs text-muted-foreground border-t">
                      Mostrando primeros 10 de {job.results.length} resultados.
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-4 w-full">
                  <Button variant="outline" className="flex-1" onClick={() => setJobId(null)}>
                    <Trash2 className="mr-2 h-4 w-4" /> Cancelar / Limpiar
                  </Button>
                  <Button variant="outline" className="flex-1 border-primary/50 text-primary hover:bg-primary/10" onClick={handleExport} disabled={isExporting}>
                    {isExporting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileSpreadsheet className="mr-2 h-4 w-4" />}
                    {isExporting ? "Exportando..." : "Exportar a Excel"}
                  </Button>
                  <Button className="flex-1" onClick={handleImport} disabled={isImporting}>
                    {isImporting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Database className="mr-2 h-4 w-4" />}
                    Importar {job.results.filter((r:any) => r.selected).length} Radicados
                  </Button>
                </div>
              </div>
            )}
            
            {job?.status === 'failed' && (
              <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center gap-3 text-destructive">
                <AlertCircle className="h-6 w-6" />
                <div>
                  <p className="font-semibold">Error en el proceso</p>
                  <p className="text-sm opacity-90">{job.error}</p>
                </div>
                <Button variant="outline" size="sm" className="ml-auto" onClick={() => setJobId(null)}>Reintentar</Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
