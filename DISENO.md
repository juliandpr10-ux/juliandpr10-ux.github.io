# Sistema de diseño del portafolio

Copia de la sección 3 de ESPECIFICACION.md. Respetarlo siempre.

## Colores
| Nombre | Hex | Uso |
|---|---|---|
| tinta | #16191D | texto principal, fondo del pie |
| tinta-2 | #374151 | párrafos |
| apagado | #4B5563 | texto secundario, pies de imagen |
| línea | #D5D9DE | bordes de tarjetas e imágenes |
| línea-suave | #E3E6EA | separadores de secciones |
| fondo | #FFFFFF | fondo general |
| fondo-alterno | #F5F6F4 | sección "Más proyectos" |
| acento | #2F4B7C | botón principal, enlaces, rótulos |
| acento-hover | #1E3459 | hover de enlaces y botón |
| acento-suave | #EEF1F6 | etiqueta de plataforma |
| verde-fondo / verde-texto | #E6F2EA / #1D5B33 | etiquetas "En producción", "Usado en emergencia" |
| ámbar-fondo / ámbar-texto | #FBF1DC / #7A4B00 | etiqueta "En construcción" |
| pie-texto / pie-apagado | #F5F6F4 / #C9CED5 | textos del pie |
| portada-fondo | #1C2733 | fondo del encabezado y la portada |
| portada-titulo | #F5F6F4 | título y nombre en la portada; fondo del botón de la portada |
| portada-texto | #C9D1DA | párrafo y navegación en la portada |
| portada-suave | #9FB0C3 | línea de formación y pie de imagen de la portada |

Definir todo como variables CSS en `:root`. Contraste mínimo 4,5:1 en texto normal; verificarlo.

## Portada oscura con relieve
- Encabezado y portada comparten el fondo `portada-fondo` con `img/relieve-valle.svg` de lado a lado, detrás del texto. El resto de la página sigue clara.
- Líneas del relieve (grosor fijo aunque la imagen se escale):

  | Capa | Color | Opacidad | Grosor |
  |---|---|---|---|
  | Curvas cada 100 m | #8FA6BF | 0,06 | 0,8 px |
  | Curvas cada 500 m | #8FA6BF | 0,12 | 1,2 px |
  | Río Medellín (cauce principal) | #A9C7E8 | 0,55 | 2,4 px (sin brillo ni sombra) |
  | Vías secundarias, terciarias y residenciales | #C9D1DA | 0,04 | 0,6 px |
  | Vías principales (motorway, trunk, primary) | #C9D1DA | 0,07 | 1 px |

  Las opacidades son el 40 % de las del primer diseño (0,16 / 0,30 / 0,10 / 0,18). Con aquellas, donde una curva de 500 m cruza una vía principal detrás de un texto, el contraste bajaba a 2,7:1 (línea de formación) y 3,9:1 (párrafo). Con las actuales todo texto de la portada cumple 4,5:1 incluso en ese cruce.

  Encuadre del fondo: el SVG mide el ancho de la pantalla (mínimo 1100 px) y se sube un 27 % de ese ancho para centrar el valle (8 % en pantallas de menos de 640 px). Así el río atraviesa la portada por la mitad.

  El río pasa detrás del título, del párrafo y, según el ancho, de la imagen: es una decisión de diseño aprobada por Julián. Donde el río cruza detrás de un texto, el contraste de ese punto baja de 4,5:1; se acepta para que el río se vea atravesando la portada. Orden de dibujo: curvas, río y encima las vías.
- Botón "Ver proyectos" en la portada: fondo `portada-titulo`, texto `tinta` (hover: fondo blanco).
- Imagen de la portada: borde de 1 px blanco al 18 % y sombra suave.
- Foco de teclado en la zona oscura: contorno de 2 px en `portada-titulo`.

## Tipografía
- Una sola familia: IBM Plex Sans.
- Escala fija (proporción 1,25). Solo estos tamaños: **16, 20, 25, 31, 39, 49 px**.
  - 49: título de la portada (31 en pantallas < 640 px).
  - 39: títulos de sección y de proyecto destacado; también cifras grandes (31 en móvil).
  - 31: cifras de tarjetas; "Hablemos" del pie.
  - 25: subtítulos de grupo y títulos de tarjetas anchas.
  - 20: párrafo de introducción, subtítulos pequeños, nombre en el encabezado.
  - 16: todo lo demás (cuerpo, etiquetas, pies de imagen). Nada por debajo de 16.
- Pesos: 400 cuerpo, 500 énfasis suave, 600 títulos.
- Interlineado: 1,6 en cuerpo; 1,1–1,2 en títulos.
- Largo de línea del texto corrido: máximo ~65 caracteres (`max-width` en `em`).
- Sin mayúsculas sostenidas, sin letra monoespaciada, sin palabras sueltas resaltadas en otro color dentro de un título.
- Listas de tecnologías separadas por comas (no con puntos medios).

## Espacios y estructura
- Contenedor: `max-width: 1200px`, relleno lateral 32 px (16 px en móvil).
- Relleno vertical de sección: 64 px (48 px en móvil), igual en todas las secciones; sin márgenes extra que se sumen.
- Radio de esquinas: 8 px en tarjetas e imágenes, 6 px en botones, 999 px en etiquetas.
- Texto alineado a la izquierda siempre.

## Botones y enlaces
- Un solo botón principal por vista: relleno `acento`, texto blanco, 600, alto mínimo 48 px, relleno horizontal 28 px.
- Acciones secundarias: enlace de texto (no segundo botón relleno), con área táctil de al menos 44 px de alto.
- Textos de botón: verbo + sustantivo ("Ver proyectos", "Descargar hoja de vida").
- Foco visible en teclado en todo lo interactivo (contorno de 2 px en `acento`).

## Movimiento
- Ninguna animación automática. Respetar `prefers-reduced-motion`.

