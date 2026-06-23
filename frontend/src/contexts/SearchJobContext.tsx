import React, { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react';
import { useToast } from "@/hooks/use-toast";
import { getLatestSearchJob, getSearchJob, type SearchJobResponse } from "@/services/api";

interface SearchJobContextType {
  activeJob: SearchJobResponse | null;
  startPolling: (jobId: number) => void;
  clearJob: () => void;
}

const SearchJobContext = createContext<SearchJobContextType | undefined>(undefined);

export function SearchJobProvider({ children }: { children: ReactNode }) {
  const { toast } = useToast();
  const [activeJob, setActiveJob] = useState<SearchJobResponse | null>(null);
  const pollInterval = useRef<NodeJS.Timeout | null>(null);

  // Intentar recuperar trabajo activo al iniciar la app
  useEffect(() => {
    const fetchLatest = async () => {
      try {
        const latestJob = await getLatestSearchJob();
        if (latestJob && (!latestJob.is_imported || latestJob.status === 'processing' || latestJob.status === 'pending')) {
          setActiveJob(latestJob);
          if (latestJob.status === 'processing' || latestJob.status === 'pending') {
            startPolling(latestJob.id);
          }
        }
      } catch (error) {
        console.error("Error fetching latest job:", error);
      }
    };
    fetchLatest();
    
    return () => stopPolling();
  }, []);

  const stopPolling = () => {
    if (pollInterval.current) {
      clearInterval(pollInterval.current);
      pollInterval.current = null;
    }
  };

  const startPolling = async (jobId: number) => {
    stopPolling();
    
    // Fetch immediately so UI updates instantly
    try {
      const data = await getSearchJob(jobId);
      setActiveJob(data);
      if (data.status === 'completed' || data.status === 'failed') {
         // Si por alguna razón ya terminó, manejamos el toast aquí también y no iniciamos polling
         if (data.status === 'completed') {
           toast({ 
             title: "Búsqueda Finalizada", 
             description: `La búsqueda masiva ha terminado. Se procesaron ${data.processed_items} radicados.`,
             duration: 8000
           });
         } else if (data.status === 'failed') {
           toast({ 
             title: "Error en Búsqueda", 
             description: data.error || "La búsqueda masiva falló.",
             variant: "destructive"
           });
         }
         return;
      }
    } catch (e) {
      console.error(e);
    }

    pollInterval.current = setInterval(async () => {
      try {
        const data = await getSearchJob(jobId);
        setActiveJob(data);
        
        if (data.status === 'completed' || data.status === 'failed') {
          stopPolling();
          
          if (data.status === 'completed') {
            toast({ 
              title: "Búsqueda Finalizada", 
              description: `La búsqueda masiva ha terminado. Se procesaron ${data.processed_items} radicados.`,
              duration: 8000
            });
          } else if (data.status === 'failed') {
            toast({ 
              title: "Error en Búsqueda", 
              description: data.error || "La búsqueda masiva falló.",
              variant: "destructive"
            });
          }
        }
      } catch (error) {
        console.error("Error polling job:", error);
      }
    }, 10000); // Polling cada 10 seg
  };

  const clearJob = () => {
    stopPolling();
    setActiveJob(null);
  };

  return (
    <SearchJobContext.Provider value={{ activeJob, startPolling, clearJob }}>
      {children}
    </SearchJobContext.Provider>
  );
}

export function useSearchJob() {
  const context = useContext(SearchJobContext);
  if (context === undefined) {
    throw new Error('useSearchJob must be used within a SearchJobProvider');
  }
  return context;
}
