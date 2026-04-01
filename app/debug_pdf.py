import pdfplumber
import io

# Usa EXACTAMENTE tu PDF
with pdfplumber.open('/home/ignacio/Escritorio/migrate/6995.pdf') as pdf:
    print(f"📄 PÁGINAS: {len(pdf.pages)}")
    
    for i, page in enumerate(pdf.pages[:2]):  # Primeras 2 páginas
        print(f"\n--- PÁGINA {i+1} ---")
        print("TEXTO (primeros 500 chars):")
        text = page.extract_text()
        print(repr(text[:500]) if text else "¡VACÍO! (es imagen)")
        
        print("\nTABLAS con lines:")
        tables1 = page.extract_tables({"vertical_strategy": "lines", "horizontal_strategy": "lines"})
        print(f"→ {len(tables1)} tablas")
        if tables1: print("Primera tabla:", tables1[0][:2])  # 2 primeras filas
        
        print("\nTABLAS sin settings:")
        tables2 = page.extract_tables()
        print(f"→ {len(tables2)} tablas")
        
        print("\nPALABRAS:")
        words = page.extract_words()
        print(f"→ {len(words)} palabras detectadas")
