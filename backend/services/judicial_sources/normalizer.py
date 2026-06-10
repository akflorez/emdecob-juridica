def normalize_case(source_name: str, raw_data: dict) -> dict:
    """Standardizes case detail metadata."""
    return {
        "radicado": raw_data.get("radicado", ""),
        "source": source_name,
        "despacho": raw_data.get("despacho", "No especificado"),
        "juez": raw_data.get("juez", "No especificado"),
        "clase_proceso": raw_data.get("clase_proceso", "No especificado"),
        "tipo_proceso": raw_data.get("tipo_proceso", "No especificado"),
        "demandante": raw_data.get("demandante", "No especificado"),
        "demandado": raw_data.get("demandado", "No especificado"),
        "fecha_radicacion": raw_data.get("fecha_radicacion", None),
        "ultima_actuacion": raw_data.get("ultima_actuacion", None),
        "estado": raw_data.get("estado", "desconocido"),
        "metadata": raw_data.get("metadata", {})
    }

def normalize_case_result(source_result: dict, source_name: str = None) -> dict:
    """
    Normalizes case details from any source into a unified structure.
    """
    raw_data = source_result.get("data", {}) if "data" in source_result else source_result
    
    # Calculate match/confidence
    radicado = raw_data.get("radicado", "")
    confianza = raw_data.get("confianza_busqueda", raw_data.get("confianza", 90))
    encontrado_en_alt = raw_data.get("encontrado_en_fuente_alternativa", True)
    req_revision = raw_data.get("requiere_revision", False)
    
    return {
        "radicado": radicado,
        "despacho": raw_data.get("despacho") or raw_data.get("juzgado") or "No especificado",
        "departamento": raw_data.get("departamento") or "No especificado",
        "municipio": raw_data.get("municipio") or "No especificado",
        "clase_proceso": raw_data.get("clase_proceso") or "No especificado",
        "tipo_proceso": raw_data.get("tipo_proceso") or "No especificado",
        "fecha_radicacion": raw_data.get("fecha_radicacion"),
        "fecha_ultima_actuacion": raw_data.get("fecha_ultima_actuacion") or raw_data.get("ultima_actuacion"),
        "demandante": raw_data.get("demandante") or "No especificado",
        "demandado": raw_data.get("demandado") or "No especificado",
        "estado": raw_data.get("estado") or "activo",
        "ubicacion": raw_data.get("ubicacion") or "No especificado",
        "ponente_juez": raw_data.get("ponente_juez") or raw_data.get("juez") or "No especificado",
        "origen_fuente": source_name or raw_data.get("origen_fuente") or "fuente_alternativa",
        "url_fuente": raw_data.get("url_fuente") or source_result.get("url") or "",
        "fuente_principal": raw_data.get("fuente_principal") or "Rama Judicial (Alternativa)",
        "confianza_busqueda": confianza,
        "encontrado_en_fuente_alternativa": encontrado_en_alt,
        "requiere_revision": req_revision
    }

def normalize_event(source_name: str, raw_event: dict) -> dict:
    """Standardizes case events/actuaciones."""
    return {
        "radicado": raw_event.get("radicado", ""),
        "source": source_name,
        "fecha_actuacion": raw_event.get("fecha_actuacion", None),
        "actuacion": raw_event.get("actuacion", "No especificado"),
        "anotacion": raw_event.get("anotacion", "Sin anotación"),
        "fecha_registro": raw_event.get("fecha_registro", None),
        "instancia": raw_event.get("instancia", "Primera"),
        "documentos": raw_event.get("documentos", []),
        "metadata": raw_event.get("metadata", {})
    }

def normalize_document(source_name: str, raw_doc: dict) -> dict:
    """Standardizes case documents/annexes."""
    return {
        "radicado": raw_doc.get("radicado", ""),
        "source": source_name,
        "tipo_documento": raw_doc.get("tipo_documento", "Otros"),
        "nombre_archivo": raw_doc.get("nombre_archivo", "archivo.pdf"),
        "url_documento": raw_doc.get("url_documento", ""),
        "fecha_publicacion": raw_doc.get("fecha_publicacion", None),
        "despacho": raw_doc.get("despacho", "No especificado"),
        "estado_validacion": raw_doc.get("estado_validacion", "pendiente"),
        "match_score": raw_doc.get("match_score", 0.0),
        "texto_bloque_match": raw_doc.get("texto_bloque_match", ""),
        "metadata": raw_doc.get("metadata", {})
    }
