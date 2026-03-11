// Case and Event types for EMDECOB Consultas

export interface Case {
  id: number;
  radicado: string;
  demandante: string;
  demandado: string;
  juzgado: string;
  alias: string | null;
  created_at: string;
}

export interface CaseEvent {
  event_date: string;
  title: string;
  detail: string;
  created_at: string;
}

export interface CasesResponse {
  items: Case[];
  page: number;
  page_size: number;
  total: number;
}

export interface EventsResponse {
  items: CaseEvent[];
}

export interface ImportResponse {
  ok: boolean;
  procesados: number;
  insertados: number;
  actualizados: number;
  errores: string[];
}

export interface CasesQueryParams {
  search?: string;
  juzgado?: string;
  page?: number;
  page_size?: number;
}
