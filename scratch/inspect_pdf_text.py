import os
import sys
import asyncio
import httpx
import re
from typing import List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from backend.service.publicaciones import (
    extract_text_content, MatchResult, only_digits, normalize_text, HEADERS
)

def test_validate_strong_match(text: str, radicado_completo: str, demandante: str = "", demandado: str = "") -> MatchResult:
    if not text:
        return MatchResult(False, None, "Texto vacío")
        
    digits = only_digits(radicado_completo)
    if len(digits) != 23:
        return MatchResult(False, None, "Radicado incompleto")
        
    # A. Radicado completo sin guiones
    if digits in text.replace(" ", "").replace("-", ""):
        pattern_flex = "".join([c + r"[\s-]*" for c in digits[:-1]]) + digits[-1]
        if re.search(pattern_flex, text):
            return MatchResult(True, "radicado_completo", f"Coincidencia con radicado completo {digits}")
            
    # B. Radicado completo con guiones
    rad_hyphenated = f"{digits[:5]}-{digits[5:7]}-{digits[7:9]}-{digits[9:12]}-{digits[12:16]}-{digits[16:21]}-{digits[21:]}"
    if rad_hyphenated in text:
        return MatchResult(True, "radicado_completo_con_guiones", f"Coincidencia con radicado con guiones {rad_hyphenated}")
        
    # C. Radicado completo separado por espacios
    rad_spaces = f"{digits[:5]} {digits[5:7]} {digits[7:9]} {digits[9:12]} {digits[12:16]} {digits[16:21]} {digits[21:]}"
    if rad_spaces in text:
        return MatchResult(True, "radicado_completo_con_espacios", f"Coincidencia con radicado con espacios {rad_spaces}")

    # D. Despacho + número interno
    despacho = digits[:12]
    year = digits[12:16]
    consecutivo = digits[16:21]
    internal_num_no_dash = f"{year}{consecutivo}"
    internal_num_dash = f"{year}-{consecutivo}"
    
    despacho_consecutivo = despacho + internal_num_no_dash
    pattern_d = "".join([c + r"[\s-]*" for c in despacho_consecutivo[:-1]]) + despacho_consecutivo[-1]
    if re.search(pattern_d, text):
        return MatchResult(True, "despacho_consecutivo_junto", f"Coincidencia con despacho + consecutivo: {despacho_consecutivo}")
        
    # E. Despacho con guiones + número interno con guion
    despacho_hyphenated = f"{digits[:5]}-{digits[5:7]}-{digits[7:9]}-{digits[9:12]}"
    if despacho_hyphenated in text and internal_num_dash in text:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned_text = "\n".join(lines)
        idx_desp = [m.start() for m in re.finditer(re.escape(despacho_hyphenated), cleaned_text)]
        idx_num = [m.start() for m in re.finditer(re.escape(internal_num_dash), cleaned_text)]
        for id_d in idx_desp:
            for id_n in idx_num:
                if abs(id_d - id_n) < 200:
                    return MatchResult(True, "despacho_interno_proximidad", f"Despacho ({despacho_hyphenated}) cerca de número interno ({internal_num_dash})")

    # F. Búsqueda por contexto cercano
    patterns = [internal_num_dash, internal_num_no_dash]
    for pattern in patterns:
        for match in re.finditer(re.escape(pattern), text):
            start_pos = max(0, match.start() - 1000)
            end_pos = min(len(text), match.end() + 1000)
            context = text[start_pos:end_pos]
            
            # Check despacho
            if despacho in context or despacho_hyphenated in context or f"{digits[:5]} {digits[5:7]} {digits[7:9]} {digits[9:12]}" in context:
                return MatchResult(True, "interno_con_despacho_en_contexto", f"Número interno ({pattern}) encontrado con despacho en ventana de contexto")
                
            # Check full radicado
            if digits in context.replace(" ", "").replace("-", ""):
                return MatchResult(True, "interno_con_radicado_en_contexto", f"Número interno ({pattern}) encontrado con radicado completo en ventana de contexto")
                
            # Check demandante / demandado tokens
            def get_party_tokens(name: str) -> List[str]:
                if not name: return []
                name_clean = normalize_text(name).upper()
                for suffix in ["S.A.S.", "SAS", "S.A.", "LIMITADA", "LTDA", "E.S.P.", "ESP", "COOPERATIVA", "MULTIACTIVA", "NACIONAL", "FIDUCIARIA", "BANCO"]:
                    name_clean = name_clean.replace(suffix, "")
                blacklist = {"del", "los", "las", "con", "sin", "por", "para", "sus", "una", "uno", "mas", "que", "les", "sus"}
                tokens = [t.lower() for t in name_clean.split() if len(t) >= 3 and t.lower() not in blacklist]
                return tokens

            dante_tokens = get_party_tokens(demandante)
            dado_tokens = get_party_tokens(demandado)
            all_party_tokens = dante_tokens + dado_tokens
            
            if all_party_tokens:
                context_norm = normalize_text(context)
                matched_tokens = [t for t in all_party_tokens if t in context_norm]
                if matched_tokens:
                    return MatchResult(True, "interno_con_partes_en_contexto", f"Número interno ({pattern}) encontrado cerca de partes matched: {matched_tokens}")

    # G. Proximidad en texto plano
    text_flat = " ".join(text.split())
    consecutivo_short = str(int(consecutivo)) if consecutivo.isdigit() else consecutivo
    
    prox_patterns = [
        r'\b' + re.escape(consecutivo) + r'\b.{0,50}\b' + re.escape(year) + r'\b',
        r'\b' + re.escape(year) + r'\b.{0,50}\b' + re.escape(consecutivo) + r'\b',
        r'\b' + re.escape(consecutivo_short) + r'\b.{0,50}\b' + re.escape(year) + r'\b',
        r'\b' + re.escape(year) + r'\b.{0,50}\b' + re.escape(consecutivo_short) + r'\b'
    ]
    
    for pat in prox_patterns:
        for match in re.finditer(pat, text_flat, re.IGNORECASE):
            start_pos = max(0, match.start() - 1000)
            end_pos = min(len(text_flat), match.end() + 1000)
            context = text_flat[start_pos:end_pos]
            
            desp_last3 = digits[9:12]
            desp_last3_short = str(int(desp_last3)) if desp_last3.isdigit() else desp_last3
            
            has_despacho = (
                despacho in context.replace(" ", "")
                or digits[:5] in context
                or (desp_last3 in context and digits[:5] in context)
                or (desp_last3_short in context and digits[:5] in context)
            )
            
            if has_despacho:
                return MatchResult(
                    True, 
                    "proximidad_plana_con_despacho", 
                    f"Consecutivo ({consecutivo}) y año ({year}) encontrados cerca de componentes de despacho ({digits[:5]}, {desp_last3})"
                )
                
            def get_party_tokens(name: str) -> List[str]:
                if not name: return []
                name_clean = normalize_text(name).upper()
                for suffix in ["S.A.S.", "SAS", "S.A.", "LIMITADA", "LTDA", "E.S.P.", "ESP", "COOPERATIVA", "MULTIACTIVA", "NACIONAL", "FIDUCIARIA", "BANCO"]:
                    name_clean = name_clean.replace(suffix, "")
                blacklist = {"del", "los", "las", "con", "sin", "por", "para", "sus", "una", "uno", "mas", "que", "les", "sus"}
                tokens = [t.lower() for t in name_clean.split() if len(t) >= 3 and t.lower() not in blacklist]
                return tokens

            dante_tokens = get_party_tokens(demandante)
            dado_tokens = get_party_tokens(demandado)
            all_party_tokens = dante_tokens + dado_tokens
            
            if all_party_tokens:
                context_norm = normalize_text(context)
                matched_tokens = [t for t in all_party_tokens if t in context_norm]
                if len(matched_tokens) >= 1:
                    return MatchResult(
                        True, 
                        "proximidad_plana_con_partes", 
                        f"Consecutivo ({consecutivo}) y año ({year}) encontrados cerca de partes matched: {matched_tokens}"
                    )
                    
    return MatchResult(False, None, "No se encontró coincidencia fuerte para el radicado o sus variantes dentro de la ventana de contexto")

async def main():
    url = "https://publicacionesprocesales.ramajudicial.gov.co/documents/6098902/214936744/Estado+041-26.pdf/ae48f1df-c5ee-5569-afb5-fc91482dbaed?t=1776463197133"
    radicado = "63001311000320250043600"
    
    print(f"Downloading from {url}...")
    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True, verify=False) as client:
        text = await extract_text_content(url, client)
        
    print(f"Extracted text length: {len(text)}")
    
    # Run validation
    match = test_validate_strong_match(text, radicado, "GENGIS WOLFGANG LOSADA GONZALEZ", "PATRICIA PAREJA GONZALEZ")
    print(f"Validation Result: is_valid={match.is_valid}, match_type={match.match_type}, reasons={match.reasons}")

if __name__ == "__main__":
    asyncio.run(main())



