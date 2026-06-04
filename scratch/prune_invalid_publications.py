import os
import sys
import json
from sqlalchemy.orm import Session

# Add the project root to sys.path so we can import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.db import SessionLocal
from backend.models import Case, CasePublication

def prune_invalid_publications():
    db: Session = SessionLocal()
    try:
        publications = db.query(CasePublication).all()
        print(f"[cleanup] Found {len(publications)} total publication records.")
        
        updated_count = 0
        
        for pub in publications:
            case = db.query(Case).filter(Case.id == pub.case_id).first()
            if not case:
                print(f"[cleanup] Warning: Case ID {pub.case_id} not found for publication {pub.id}")
                continue
                
            radicado = case.radicado
            
            # 1. Parse and clean documentos_complementarios
            if not pub.documentos_complementarios:
                continue
                
            try:
                docs = json.loads(pub.documentos_complementarios)
            except Exception as e:
                print(f"[cleanup] Error parsing documents for pub {pub.id}: {e}")
                continue
                
            if not isinstance(docs, list):
                continue
                
            # Filter to keep only validated ones
            original_len = len(docs)
            valid_docs = [doc for doc in docs if doc.get("contiene_radicado") is True]
            
            # Check if url_providencia needs updating or clearing
            providencia_updated = False
            if pub.url_providencia:
                # If the URL is in the discarded documents list, we must clear/reset it
                is_providencia_valid = any(doc.get("url") == pub.url_providencia for doc in valid_docs)
                if not is_providencia_valid:
                    # Let's see if we can find a new valid providencia/auto in valid_docs
                    new_url = None
                    for doc in valid_docs:
                        doc_name = doc.get("nombre", "").lower()
                        if "providencia" in doc_name or "auto" in doc_name:
                            new_url = doc.get("url")
                            break
                    
                    print(f"[cleanup] Case {radicado} | Pub {pub.id}: providencia was {pub.url_providencia} (invalid). Resetting to {new_url}")
                    pub.url_providencia = new_url
                    providencia_updated = True
            
            if len(valid_docs) != original_len or providencia_updated:
                pub.documentos_complementarios = json.dumps(valid_docs)
                print(f"[cleanup] Case {radicado} | Pub {pub.id}: Pruned {original_len - len(valid_docs)} mismatching files.")
                updated_count += 1
                
        if updated_count > 0:
            db.commit()
            print(f"[cleanup] Success! Updated {updated_count} publication records.")
        else:
            print("[cleanup] No invalid documents or providencias found to prune.")
            
    except Exception as e:
        db.rollback()
        print(f"[cleanup] Fatal error during prune: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    prune_invalid_publications()
