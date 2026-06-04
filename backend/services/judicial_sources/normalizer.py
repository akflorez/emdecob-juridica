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
