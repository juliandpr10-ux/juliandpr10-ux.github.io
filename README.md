# Portafolio de Julián David Patiño Ramírez

Sitio personal publicado en **https://juliandpr10-ux.github.io**.
Es una sola página hecha con HTML y CSS, sin programas ni bases de datos detrás.

---

## Qué es cada archivo

| Archivo o carpeta | Para qué sirve |
|---|---|
| `index.html` | La página: todos los textos, imágenes y enlaces. |
| `css/estilos.css` | El diseño: colores, letras, espacios. Los colores y tamaños están arriba del todo, en `:root`. |
| `img/` | Las capturas ya optimizadas (formato WebP, livianas). |
| `img/originales/` | Los PNG originales. **No se suben a internet** (están en `.gitignore`). |
| `img/relieve-valle.svg` | El fondo de la portada: curvas de nivel y vías del Valle de Aburrá. Lo genera `tools/generar_relieve.py`. |
| `tools/generar_relieve.py` | Script que descarga el relieve y las vías y dibuja `img/relieve-valle.svg` (ver más abajo). |
| `datos/crudos/` | Relieve y vías descargados por el script. **No se suben** (están en `.gitignore`); se pueden volver a descargar. |
| `favicon.svg` | El ícono pequeño que sale en la pestaña del navegador. |
| `DISENO.md` | Las reglas de diseño (colores, tamaños, espacios). |
| `ESPECIFICACION.md` | Documento de trabajo interno con todo el contenido aprobado. Está solo en tu equipo: **no se sube** (está en `.gitignore`). |
| `tests/test_pagina.py` | Prueba automática que revisa la página (un solo título principal, imágenes con descripción, sin enlaces prohibidos, contraste de colores…). |
| `tests/test_generar_relieve.py` | Prueba automática del script del relieve (no necesita internet). |
| `pyproject.toml`, `requirements.txt`, `.pre-commit-config.yaml` | Configuración de las revisiones automáticas y lista de librerías del entorno. No hace falta tocarlos. |
| `.venv/` | Entorno de Python del proyecto (librerías del script y de las pruebas). **No se sube**; ver "Entorno de Python del proyecto". |
| `CLAUDE.md`, `.claude/` | Instrucciones para Claude Code. |

---

## Cómo cambiar un texto

1. Abre `index.html` con un editor de texto (por ejemplo, VS Code o TextEdit en modo texto plano).
2. Busca el texto que quieres cambiar con `Cmd + F`.
3. Cámbialo **solo entre las etiquetas**. Ejemplo: en
   `<p>Organizo datos de riesgo para decidir.</p>`
   cambia únicamente lo que está entre `<p>` y `</p>`.
4. Guarda y revisa en local (ver más abajo) antes de publicar.

Las cifras grandes están así: `<dt>escenarios registrados</dt><dd>377</dd>`.
`dt` es la frase y `dd` es el número.

---

## Cómo agregar un proyecto nuevo

1. **Prepara la imagen.** Guarda el PNG original en `img/originales/` y conviértelo a WebP
   (máximo 1600 px de ancho, calidad 80) con este comando en la Terminal, desde la carpeta del proyecto:

   ```
   cwebp -q 80 -resize 1600 0 img/originales/mi-proyecto.png -o img/mi-proyecto.webp
   ```

   Si la imagen mide menos de 1600 px de ancho, quita `-resize 1600 0`.
   Para saber su tamaño final: `sips -g pixelWidth -g pixelHeight img/mi-proyecto.webp`.

2. **Copia un bloque de tarjeta.** En `index.html`, dentro de la sección "Más proyectos",
   cada proyecto empieza con `<article class="tarjeta` y termina con `</article>`.
   Copia uno completo y pégalo debajo, dentro del grupo que corresponda.
   - Tarjeta normal: `class="tarjeta"`.
   - Tarjeta ancha (toda la fila): `class="tarjeta tarjeta--ancha"`.
   - Ancha con imagen a la izquierda: `class="tarjeta tarjeta--ancha tarjeta--dividida"`.
   - Ancha con imagen a la derecha: agrega también `tarjeta--imagen-derecha`.

3. **Cambia los textos y la imagen** del bloque copiado:
   - `src="img/mi-proyecto.webp"`
   - `width` y `height` con las medidas que te dio `sips`.
   - `alt="..."`: una frase que describa lo que se ve en la captura.
   - Deja `loading="lazy"`.

4. **Etiquetas de estado:** verde `etiqueta--verde` ("En producción", "En uso"),
   ámbar `etiqueta--ambar` ("En construcción"), azul claro `etiqueta--plataforma`.

5. Corre las revisiones (`pytest`) y mira el resultado en local.

> Regla del sitio: nunca enlazar a tableros o servicios en vivo (AMVA, Azure, ArcGIS, Firebase).
> La prueba automática falla si alguien lo hace.

---

## Cómo activar la hoja de vida y LinkedIn

Están escritos en `index.html` pero "dormidos" dentro de comentarios (`<!-- ... -->`),
que el navegador no muestra.

**Hoja de vida**
1. Crea la carpeta `cv/` y guarda ahí el PDF con el nombre exacto `Julian_Patino_hoja_de_vida.pdf`.
2. En `index.html` busca `HOJA DE VIDA`. Aparece dos veces (portada y pie).
3. En cada una, borra la línea que empieza con `<!-- HOJA DE VIDA` y la línea `FIN HOJA DE VIDA -->`.
   Deja la línea del medio (la del enlace).

**LinkedIn**
1. En `index.html` busca `LINKEDIN`.
2. Cambia `https://www.linkedin.com/in/TU-PERFIL` por tu dirección real.
3. Borra la línea que empieza con `<!-- LINKEDIN` y la línea `FIN LINKEDIN -->`.
4. Abre `tests/test_pagina.py`, busca `DOMINIOS_PERMITIDOS` y agrega `"www.linkedin.com"` a la lista;
   si no, la prueba avisará de un enlace no aprobado.

---

## El fondo de la portada (relieve, río y vías)

El fondo oscuro de la portada es un dibujo hecho con datos abiertos:

- **Relieve:** modelo de elevación Copernicus DEM GLO-30 (30 m), de la Unión Europea y la ESA,
  descargado del repositorio oficial de datos abiertos de AWS. Del relieve salen curvas de nivel
  cada 100 m, más marcadas cada 500 m.
- **Río Medellín (Aburrá):** OpenStreetMap, solo el cauce principal (`waterway=river` con nombre
  "Río Medellín", más su tramo canalizado por el centro de la ciudad, que figura como canal);
  nada de quebradas ni otros ríos. Atraviesa la portada por la mitad, detrás del texto
  (decisión de diseño, ver DISENO.md).
- **Vías:** OpenStreetMap, por medio de la API Overpass. Solo vías principales, secundarias,
  terciarias y residenciales (nada de senderos ni caminos peatonales).

Las capas usan la misma proyección y el mismo encuadre, y van en un solo archivo:
`img/relieve-valle.svg` (menos de 300 KB).

**Para volver a generarlo** (por ejemplo, para cambiar colores u opacidades), en la Terminal,
desde la carpeta del proyecto y con el entorno del proyecto activado (ver la sección siguiente):

```
python tools/generar_relieve.py
```

- La primera vez descarga los datos a `datos/crudos/` (unos 45 MB); después los reutiliza.
  Para descargarlos de nuevo, borra esa carpeta.
- Colores, opacidades y grosores están arriba en el script, en `ESTILO_CURVAS`, `ESTILO_MAESTRAS`,
  `ESTILO_RIO`, `ESTILO_VIAS` y `ESTILO_PRINCIPALES`. Después de cambiarlos corre `pytest`: una
  prueba revisa que el texto de la portada siga leyéndose bien (contraste de 4,5:1) sobre las líneas.

**Créditos obligatorios:** el pie de la página lleva la nota de Copernicus (en inglés, tal como la
exige su licencia) y "© colaboradores de OpenStreetMap". No los borres mientras uses este fondo.

---

## Entorno de Python del proyecto (.venv)

El script del relieve y las pruebas usan librerías de Python (numpy, scipy, rasterio,
scikit-image, shapely, pyproj, requests y pytest). Viven en una carpeta propia del proyecto,
`.venv`, para no mezclarse con el Python del sistema. Esa carpeta **no se sube** a GitHub.

**Activarlo** (cada vez que abras una Terminal nueva para trabajar en el proyecto):

```
source .venv/bin/activate
```

Sabrás que está activo porque la línea de la Terminal empieza con `(.venv)`.
Con eso, `pytest` y `python` usan las librerías del proyecto. Para salir: `deactivate`.

**Crearlo desde cero** (por ejemplo, en otro computador o si se daña). Desde la carpeta del proyecto:

```
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Las versiones exactas están en `requirements.txt`. El "portero" que revisa antes de cada commit
(`.pre-commit-config.yaml`) corre las pruebas con `.venv/bin/pytest`, así que el entorno debe existir.

**Créditos obligatorios:** el pie de la página lleva la nota de Copernicus (en inglés, tal como la
exige su licencia) y "© colaboradores de OpenStreetMap". No los borres mientras uses este fondo.

---

## Cómo ver el sitio en local antes de publicar

En la Terminal, dentro de la carpeta del proyecto:

```
python3 -m http.server 8000
```

Abre **http://localhost:8000** en Chrome. Para verlo como en un celular:
`Cmd + Option + I` y luego el ícono de celular (o `Cmd + Shift + M`).
Para apagar el servidor: `Ctrl + C` en la Terminal.

Para correr las revisiones: `pytest` con el entorno activado, o `.venv/bin/pytest` sin activarlo
(debe decir "passed" y nada en rojo).

---

## Si algo se daña

Cada publicación queda guardada como un "commit" (una foto del sitio en ese momento).
Siempre se puede volver a una foto anterior.

**Opción A, desde la Terminal**

```
git log --oneline          # lista de cambios, el más reciente arriba
git revert HEAD            # deshace el último cambio (crea uno nuevo que lo anula)
git push                   # publica la corrección
```

Para deshacer un cambio más viejo, copia su código de la lista (por ejemplo `a1b2c3d`) y usa `git revert a1b2c3d`.
`git revert` no borra la historia: solo agrega un cambio que anula el anterior, así que es seguro.

**Opción B, desde la página de GitHub**

1. Entra a https://github.com/juliandpr10-ux/juliandpr10-ux.github.io
2. Haz clic en **Commits** (arriba de la lista de archivos) para ver la historia.
3. Abre el archivo que se dañó, botón **History**, elige la versión buena, copia su contenido
   y pégalo con el lápiz de editar (**Edit**) en la versión actual. Guarda con **Commit changes**.

**Cómo saber si GitHub Pages terminó de publicar**

1. En el repositorio, pestaña **Actions**: el último trabajo "pages build and deployment"
   debe tener un círculo verde ✓. Amarillo = todavía publicando; rojo = falló (ábrelo para ver por qué).
2. También en **Settings → Pages** aparece "Your site is live at…".
3. Los cambios tardan de 1 a 3 minutos. Si no ves el cambio, recarga con `Cmd + Shift + R`.

> El otro sitio, `juliandpr10-ux.github.io/pmetrgrd-amva/`, vive en su propio repositorio.
> Nada de lo que hagas aquí lo afecta, siempre que **no** crees una carpeta llamada `pmetrgrd-amva` en este proyecto.
