import os
import re

template_dir = r"c:\Users\emili\Documents\proyecto Matatucas\app\templates"

# Regex para detectar una etiqueta form con method="POST"
# que aún NO tenga csrf_token dentro (lo comprobaremos buscando csrf_token en el archivo).
# Pero mejor, reemplazamos en la etiqueta en todos lados, y si ya tiene la borramos o evitamos duplicidad.

for root, dirs, files in os.walk(template_dir):
    for f in files:
        if f.endswith(".html"):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
            
            # Si el archivo tiene la palabra POST
            if "POST" in content.upper() and "csrf_token" not in content:
                # Buscar todos los fomularios y añadir csrf_token()
                new_content = re.sub(
                    r'(<form[^>]*method=[\'"]?POST[\'"]?[^>]*>)',
                    r'\1\n        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>',
                    content,
                    flags=re.IGNORECASE
                )
                
                if new_content != content:
                    with open(path, "w", encoding="utf-8") as file:
                        file.write(new_content)
                    print(f"Injected CSRF in {f}")

print("CSRF injection complete.")
