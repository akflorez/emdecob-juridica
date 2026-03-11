import { useState, useRef } from 'react';
import { Upload, FileSpreadsheet, CheckCircle2, AlertTriangle, Loader2, Download, XCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { importExcel, downloadInvalidReport, type ImportExcelResponse } from '@/services/api';

export default function ImportarPage() {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<ImportExcelResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      await uploadFile(files[0]);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      await uploadFile(files[0]);
    }
  };

  const uploadFile = async (file: File) => {
    const validExtensions = ['.xlsx', '.xls', '.csv'];
    const ext = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
    
    if (!validExtensions.includes(ext)) {
      toast({
        title: 'Archivo inválido',
        description: 'Solo se permiten archivos .xlsx, .xls o .csv',
        variant: 'destructive',
      });
      return;
    }

    setIsUploading(true);
    setResult(null);
    
    try {
      const response = await importExcel(file);
      setResult(response);
      
      if (response.created > 0) {
        toast({
          title: 'Importación exitosa',
          description: `Se crearon ${response.created} caso(s)`,
        });
      } else if (response.invalid_count > 0) {
        toast({
          title: 'Importación con advertencias',
          description: `${response.invalid_count} radicado(s) no se encontraron en Rama Judicial`,
          variant: 'destructive',
        });
      } else {
        toast({
          title: 'Sin cambios',
          description: 'Todos los radicados ya existen en el sistema',
        });
      }
    } catch (error: any) {
      toast({
        title: 'Error al importar',
        description: error?.message || 'Error desconocido',
        variant: 'destructive',
      });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDownloadInvalid = async () => {
    if (!result?.invalid_list || result.invalid_list.length === 0) return;
    
    try {
      await downloadInvalidReport(result.invalid_list);
      toast({
        title: 'Descarga completada',
        description: 'Se descargó el reporte de radicados no encontrados',
      });
    } catch (error: any) {
      toast({
        title: 'Error al descargar',
        description: error?.message || 'Error desconocido',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Importar Casos</h1>
        <p className="text-muted-foreground mt-2">
          Sube un archivo Excel con los radicados de los casos a monitorear
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5 text-primary" />
            Subir Archivo
          </CardTitle>
          <CardDescription>
            El archivo debe tener una columna llamada "Radicado" con los números de radicado de 23 dígitos.
            Solo se importarán casos que existan en la Rama Judicial.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className={`
              border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer
              ${isDragging ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'}
              ${isUploading ? 'pointer-events-none opacity-50' : ''}
            `}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={handleFileSelect}
              className="hidden"
            />
            
            {isUploading ? (
              <div className="space-y-4">
                <Loader2 className="h-12 w-12 mx-auto text-primary animate-spin" />
                <p className="text-muted-foreground">Importando casos...</p>
                <p className="text-xs text-muted-foreground">
                  Validando cada radicado en la Rama Judicial, esto puede tomar unos minutos
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <FileSpreadsheet className="h-12 w-12 mx-auto text-muted-foreground" />
                <div>
                  <p className="font-medium">Arrastra un archivo aquí</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    o haz clic para seleccionar
                  </p>
                </div>
                <p className="text-xs text-muted-foreground">
                  Formatos: .xlsx, .xls, .csv
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Resultado de la Importación</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="flex items-center gap-3 p-4 rounded-lg bg-green-500/10">
                <CheckCircle2 className="h-8 w-8 text-green-500" />
                <div>
                  <p className="text-2xl font-bold text-green-500">{result.created}</p>
                  <p className="text-sm text-muted-foreground">Casos creados</p>
                </div>
              </div>
              
              <div className="flex items-center gap-3 p-4 rounded-lg bg-yellow-500/10">
                <AlertTriangle className="h-8 w-8 text-yellow-500" />
                <div>
                  <p className="text-2xl font-bold text-yellow-500">{result.skipped}</p>
                  <p className="text-sm text-muted-foreground">Ya existían</p>
                </div>
              </div>
              
              <div className="flex items-center gap-3 p-4 rounded-lg bg-red-500/10">
                <XCircle className="h-8 w-8 text-red-500" />
                <div>
                  <p className="text-2xl font-bold text-red-500">{result.invalid_count}</p>
                  <p className="text-sm text-muted-foreground">No encontrados</p>
                </div>
              </div>
            </div>

            {result.invalid_count > 0 && result.invalid_list && (
              <div className="mt-6 p-4 rounded-lg bg-destructive/5 border border-destructive/20">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-destructive">
                      {result.invalid_count} radicado(s) no se encontraron en Rama Judicial
                    </h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      Estos radicados no fueron importados porque no existen en la página de la Rama
                    </p>
                  </div>
                  <Button onClick={handleDownloadInvalid} variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    Descargar lista
                  </Button>
                </div>
                
                {result.invalid_list.length <= 10 && (
                  <div className="mt-4 space-y-2">
                    {result.invalid_list.map((item, i) => (
                      <div key={i} className="flex items-center gap-2 text-sm">
                        <XCircle className="h-4 w-4 text-destructive" />
                        <span className="font-mono">{item.radicado}</span>
                        <span className="text-muted-foreground">- {item.motivo}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Formato del Archivo</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            El archivo debe contener al menos la columna "Radicado". Ejemplo:
          </p>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm border border-border rounded-lg">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-4 py-2 text-left border-b">Radicado</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="px-4 py-2 font-mono border-b">11001400302120250005200</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 font-mono border-b">11001400304020240144500</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 font-mono">05001400300120230001234</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}