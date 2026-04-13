import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, FileQuestion, ArrowRight, Loader2 } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";

import { getCaseByRadicado } from "@/services/api";
import type { CaseByRadicadoResponse } from "@/services/api";
import { CaseCard } from "@/components/CaseCard";

export default function ConsultarPage() {
  const [radicado, setRadicado] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [cases, setCases] = useState<CaseByRadicadoResponse[] | null>(null);
  const [notFound, setNotFound] = useState(false);

  const { toast } = useToast();
  const navigate = useNavigate();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    const clean = radicado.trim();
    if (!clean) {
      toast({
        title: "Campo requerido",
        description: "Ingresa un número de radicado para buscar",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    setCases(null);
    setNotFound(false);

    try {
      const result = await getCaseByRadicado(clean);
      setCases(result);

      if (result.length > 0 && result[0].note) {
        toast({
          title: "Consulta realizada",
          description: result[0].note,
        });
      }
    } catch (error: any) {
      if (error?.status === 404) {
        setNotFound(true);
      } else {
        toast({
          title: "Error en la búsqueda",
          description: error?.message ? String(error.message) : "Error desconocido",
          variant: "destructive",
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const goToEvents = (c: CaseByRadicadoResponse) => {
    // Abrir detalle por ID para mayor precisión
    window.open(`/casos/id/${c.id}`, "_blank");
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Consultar Caso</h1>
        <p className="text-muted-foreground mt-2">
          Busca un caso por su número de radicado
        </p>
      </div>

      {/* Search Card */}
      <Card className="card-hover">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5 text-primary" />
            Buscador de Casos
          </CardTitle>
          <CardDescription>
            Ingresa el número de radicado completo para encontrar el caso
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSearch} className="flex gap-3">
            <Input
              placeholder="Ej: 11001418902720250002800"
              value={radicado}
              onChange={(e) => setRadicado(e.target.value)}
              className="flex-1"
            />
            <Button type="submit" disabled={isLoading}>
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Buscando...
                </span>
              ) : (
                <span className="flex items-center">
                  <Search className="mr-2 h-4 w-4" />
                  Buscar
                </span>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Result list */}
      {cases && (
        <div className="animate-fade-in space-y-6">
          {cases.length > 1 && (
            <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 mb-4">
              <p className="text-sm font-medium text-primary flex items-center gap-2">
                <FileQuestion className="h-4 w-4" />
                Se encontraron {cases.length} procesos para este radicado. Selecciona uno para ver el detalle:
              </p>
            </div>
          )}
          
          <div className="grid gap-6">
            {cases.map((c) => (
              <div key={c.id} className="space-y-3">
                <CaseCard caseData={c as any} />
                <Button onClick={() => goToEvents(c)} className="w-full sm:w-auto">
                  Ver Historial de Eventos
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Not Found */}
      {notFound && (
        <Card className="card-hover animate-fade-in border-warning/30 bg-warning/5">
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto rounded-full bg-warning/20 flex items-center justify-center mb-4">
                <FileQuestion className="h-8 w-8 text-warning" />
              </div>

              <h3 className="text-lg font-semibold mb-2">Caso No Encontrado</h3>
              <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                No se encontró ningún caso con el radicado "{radicado.trim()}".
                Verifica el número o intenta con otro.
              </p>

              <Button variant="outline" onClick={() => navigate("/importar")}>
                Ir a Importar
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}