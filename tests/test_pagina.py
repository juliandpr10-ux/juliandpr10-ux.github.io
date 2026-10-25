"""Pruebas automáticas del portafolio.

Revisan que index.html y css/estilos.css cumplan las reglas de
ESPECIFICACION.md. Se corren con:  pytest
"""

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parent.parent
INDEX = RAIZ / "index.html"
ESTILOS = RAIZ / "css" / "estilos.css"

TITULO_ESPERADO = "Julián David Patiño Ramírez, geólogo MSc, riesgo y GIS"
TAMANOS_PERMITIDOS_PX = {16, 20, 25, 31, 39, 49}
DOMINIOS_PERMITIDOS = {"github.com", "juliandpr10-ux.github.io", "www.openstreetmap.org"}
PESO_MAXIMO_RELIEVE_BYTES = 300 * 1024
PALABRAS_PROHIBIDAS_EN_ENLACES = (
    "arcgis",
    "azure",
    "firebase",
    "amva",
    "metropol.gov",
    "web.app",
)


class LectorDePagina(HTMLParser):
    """Recorre el HTML y guarda las etiquetas con sus atributos, en orden."""

    def __init__(self):
        super().__init__()
        self.etiquetas = []
        self.titulo = ""
        self._dentro_de_title = False

    def handle_starttag(self, tag, attrs):
        self.etiquetas.append((tag, dict(attrs)))
        self._dentro_de_title = tag == "title"

    def handle_endtag(self, tag):
        if tag == "title":
            self._dentro_de_title = False

    def handle_data(self, data):
        if self._dentro_de_title:
            self.titulo += data


def leer_pagina(texto_html):
    lector = LectorDePagina()
    lector.feed(texto_html)
    return lector


def etiquetas_de_tipo(pagina, tipo):
    return [atributos for nombre, atributos in pagina.etiquetas if nombre == tipo]


def niveles_de_titulos(pagina):
    return [int(nombre[1]) for nombre, _ in pagina.etiquetas if re.fullmatch(r"h[1-6]", nombre)]


def enlaces_y_fuentes(pagina):
    """Todas las direcciones que la página enlaza o carga."""
    direcciones = []
    for _, atributos in pagina.etiquetas:
        direcciones += [atributos[clave] for clave in ("href", "src") if atributos.get(clave)]
        contenido = atributos.get("content") or ""
        if contenido.startswith("https://"):
            direcciones.append(contenido)
    return direcciones


def es_ruta_local(direccion):
    return not urlparse(direccion).scheme and not direccion.startswith("#")


def variables_de_color(css):
    bloque_root = re.search(r":root\s*{(.*?)}", css, re.S).group(1)
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", bloque_root))


def luminancia(color_hex):
    canales = [int(color_hex[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lineales = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canales]
    rojo, verde, azul = lineales
    return 0.2126 * rojo + 0.7152 * verde + 0.0722 * azul


def mezclar(color_arriba, opacidad, color_abajo):
    """Color que se ve al poner un color semitransparente sobre otro."""
    canales = []
    for i in (1, 3, 5):
        arriba, abajo = int(color_arriba[i : i + 2], 16), int(color_abajo[i : i + 2], 16)
        canales.append(round(arriba * opacidad + abajo * (1 - opacidad)))
    return "#" + "".join(f"{c:02x}" for c in canales)


def contraste(color_a, color_b):
    claro, oscuro = sorted((luminancia(color_a), luminancia(color_b)), reverse=True)
    return (claro + 0.05) / (oscuro + 0.05)


def medidas_webp(contenido):
    """Ancho y alto de una imagen WebP, leídos de su encabezado (sin librerías externas)."""
    if contenido[:4] != b"RIFF" or contenido[8:12] != b"WEBP":
        raise ValueError("No es un archivo WebP")
    tipo = contenido[12:16]
    if tipo == b"VP8X":
        ancho = int.from_bytes(contenido[24:27], "little") + 1
        alto = int.from_bytes(contenido[27:30], "little") + 1
    elif tipo == b"VP8 ":
        ancho = int.from_bytes(contenido[26:28], "little") & 0x3FFF
        alto = int.from_bytes(contenido[28:30], "little") & 0x3FFF
    elif tipo == b"VP8L":
        bits = int.from_bytes(contenido[21:25], "little")
        ancho = (bits & 0x3FFF) + 1
        alto = ((bits >> 14) & 0x3FFF) + 1
    else:
        raise ValueError(f"Tipo de WebP desconocido: {tipo!r}")
    return ancho, alto


def tamanos_de_letra_px(css):
    rems = re.findall(r"--t-\d+:\s*([\d.]+)rem", css)
    return {round(float(valor) * 16) for valor in rems}


# ---------- Pruebas de las funciones de apoyo ----------


def test_contraste_negro_sobre_blanco_es_21():
    assert round(contraste("#000000", "#ffffff"), 1) == 21.0


def test_mezclar_con_opacidad():
    assert mezclar("#ffffff", 0.5, "#000000") == "#808080"
    assert mezclar("#123456", 1, "#000000") == "#123456"
    assert mezclar("#123456", 0, "#abcdef") == "#abcdef"


def test_es_ruta_local_distingue_rutas_y_direcciones_web():
    assert es_ruta_local("img/foto.webp")
    assert not es_ruta_local("https://github.com/x")
    assert not es_ruta_local("#contacto")
    assert not es_ruta_local("mailto:a@b.co")


def test_medidas_webp_lee_los_tres_tipos_de_encabezado():
    inicio = b"RIFF\x00\x00\x00\x00WEBP"
    vp8x = inicio + b"VP8X" + bytes(8) + (1599).to_bytes(3, "little") + (772).to_bytes(3, "little")
    medidas_vp8 = (1600).to_bytes(2, "little") + (773).to_bytes(2, "little")
    vp8 = inicio + b"VP8 " + bytes(4) + bytes(3) + b"\x9d\x01\x2a" + medidas_vp8
    bits = (1599) | (772 << 14)
    vp8l = inicio + b"VP8L" + bytes(4) + b"\x2f" + bits.to_bytes(4, "little")
    assert medidas_webp(vp8x) == (1600, 773)
    assert medidas_webp(vp8) == (1600, 773)
    assert medidas_webp(vp8l) == (1600, 773)


def test_niveles_de_titulos_lee_el_orden():
    pagina = leer_pagina("<h1>a</h1><h2>b</h2><h3>c</h3>")
    assert niveles_de_titulos(pagina) == [1, 2, 3]


# ---------- Pruebas de la página ----------

PAGINA = leer_pagina(INDEX.read_text(encoding="utf-8"))
CSS = ESTILOS.read_text(encoding="utf-8")


def test_idioma_es_espanol():
    assert etiquetas_de_tipo(PAGINA, "html")[0].get("lang") == "es"


def test_titulo_de_la_pestana():
    assert PAGINA.titulo.strip() == TITULO_ESPERADO


def test_tiene_descripcion_open_graph_y_favicon():
    metas = etiquetas_de_tipo(PAGINA, "meta")
    nombres = {m.get("name") for m in metas} | {m.get("property") for m in metas}
    assert {"description", "og:title", "og:image"} <= nombres
    imagen_og = next(m["content"] for m in metas if m.get("property") == "og:image")
    assert imagen_og.endswith("img/escenarios-mapa.webp")
    assert any(e.get("rel") == "icon" for e in etiquetas_de_tipo(PAGINA, "link"))


def test_un_solo_h1():
    assert niveles_de_titulos(PAGINA).count(1) == 1


def test_titulos_no_saltan_niveles():
    niveles = niveles_de_titulos(PAGINA)
    for anterior, actual in zip(niveles, niveles[1:], strict=False):
        assert actual <= anterior + 1, f"Salto de h{anterior} a h{actual}"


def test_imagenes_tienen_alt_ancho_y_alto():
    for imagen in etiquetas_de_tipo(PAGINA, "img"):
        assert imagen.get("alt", "").strip(), imagen["src"]
        assert imagen.get("width") and imagen.get("height"), imagen["src"]


def test_solo_la_imagen_de_portada_carga_de_inmediato():
    imagenes = etiquetas_de_tipo(PAGINA, "img")
    assert imagenes[0]["src"] == "img/escenarios-mapa.webp"
    assert imagenes[0].get("loading") != "lazy"
    for imagen in imagenes[1:]:
        assert imagen.get("loading") == "lazy", imagen["src"]


def test_imagenes_son_webp_de_maximo_1600_px():
    for imagen in etiquetas_de_tipo(PAGINA, "img"):
        assert imagen["src"].endswith(".webp")
        assert int(imagen["width"]) <= 1600


def test_medidas_escritas_coinciden_con_cada_imagen():
    for imagen in etiquetas_de_tipo(PAGINA, "img"):
        ancho, alto = medidas_webp((RAIZ / imagen["src"]).read_bytes())
        assert (int(imagen["width"]), int(imagen["height"])) == (ancho, alto), imagen["src"]


def test_archivos_locales_enlazados_existen():
    for direccion in enlaces_y_fuentes(PAGINA):
        if es_ruta_local(direccion):
            assert (RAIZ / direccion).is_file(), f"No existe: {direccion}"


def test_sin_enlaces_a_servicios_en_vivo():
    for direccion in enlaces_y_fuentes(PAGINA):
        for palabra in PALABRAS_PROHIBIDAS_EN_ENLACES:
            assert palabra not in direccion.lower(), direccion


def test_enlaces_externos_solo_a_dominios_aprobados():
    for enlace in etiquetas_de_tipo(PAGINA, "a"):
        direccion = urlparse(enlace.get("href", ""))
        if direccion.scheme in ("http", "https"):
            assert direccion.hostname in DOMINIOS_PERMITIDOS, enlace["href"]


def test_politica_de_seguridad_solo_permite_sitio_y_google_fonts():
    metas = etiquetas_de_tipo(PAGINA, "meta")
    politica = next(m["content"] for m in metas if m.get("http-equiv") == "Content-Security-Policy")
    hosts = set(re.findall(r"https://([\w.-]+)", politica))
    assert hosts == {"fonts.googleapis.com", "fonts.gstatic.com"}
    assert "default-src 'self'" in politica
    assert "unsafe" not in politica


def test_sin_javascript():
    assert not etiquetas_de_tipo(PAGINA, "script")


def test_tamanos_de_letra_solo_de_la_escala():
    assert tamanos_de_letra_px(CSS) == TAMANOS_PERMITIDOS_PX
    todos_los_tamanos = re.findall(r"font-size:\s*([^;]+);", CSS)
    otros_tamanos = [t for t in todos_los_tamanos if not t.startswith("var(--t-")]
    assert not otros_tamanos, f"Tamaños fuera de la escala: {otros_tamanos}"


def test_contraste_minimo_de_textos():
    colores = variables_de_color(CSS)
    pares_texto_fondo = [
        ("tinta", "fondo"),
        ("tinta-2", "fondo"),
        ("apagado", "fondo"),
        ("apagado", "fondo-alterno"),
        ("tinta", "fondo-alterno"),
        ("acento", "fondo"),
        ("acento", "fondo-alterno"),
        ("acento-hover", "fondo"),
        ("fondo", "acento"),
        ("fondo", "acento-hover"),
        ("acento", "acento-suave"),
        ("verde-texto", "verde-fondo"),
        ("ambar-texto", "ambar-fondo"),
        ("pie-texto", "tinta"),
        ("pie-apagado", "tinta"),
    ]
    for texto, fondo in pares_texto_fondo:
        valor = contraste(colores[texto], colores[fondo])
        assert valor >= 4.5, f"{texto} sobre {fondo}: {valor:.2f}"


def capas_del_relieve(svg):
    """{(color, grosor): opacidad} de cada grupo de líneas del SVG del relieve."""
    patron = r'<g stroke="(#[0-9A-Fa-f]{6})" stroke-opacity="([\d.]+)" stroke-width="([\d.]+)"'
    return {
        (color.lower(), float(grosor)): float(opacidad) for color, opacidad, grosor in re.findall(patron, svg)
    }


def test_capas_del_relieve_lee_color_grosor_y_opacidad():
    svg = '<g stroke="#8FA6BF" stroke-opacity=".12" stroke-width="1.2"><path d=""/></g>'
    assert capas_del_relieve(svg) == {("#8fa6bf", 1.2): 0.12}


def test_contraste_en_la_portada_oscura_incluso_sobre_las_lineas():
    colores = variables_de_color(CSS)
    fondo = colores["portada-fondo"]
    capas = capas_del_relieve((RAIZ / "img" / "relieve-valle.svg").read_text(encoding="utf-8"))
    opacidad_maestras = capas[("#8fa6bf", 1.2)]
    opacidad_principales = capas[("#c9d1da", 1.0)]
    # Peor caso: texto encima de una curva maestra cruzada por una vía principal.
    # El río no entra aquí: por decisión de diseño pasa detrás del texto y, en esos
    # puntos, el contraste baja de 4,5:1 (aceptado; ver DISENO.md).
    maestra_y_via = mezclar("#c9d1da", opacidad_principales, mezclar("#8fa6bf", opacidad_maestras, fondo))
    textos = ("portada-titulo", "portada-texto", "portada-suave")
    for texto in textos:
        for fondo_real in (fondo, maestra_y_via):
            valor = contraste(colores[texto], fondo_real)
            assert valor >= 4.5, f"{texto} sobre {fondo_real}: {valor:.2f}"
    assert contraste(colores["tinta"], colores["portada-titulo"]) >= 4.5  # botón
    assert contraste(colores["tinta"], colores["portada-boton-hover"]) >= 4.5


def test_rio_con_el_estilo_acordado():
    capas = capas_del_relieve((RAIZ / "img" / "relieve-valle.svg").read_text(encoding="utf-8"))
    assert capas.get(("#a9c7e8", 2.4)) == 0.55


def test_encuadre_aprobado_del_fondo():
    # Un solo tamaño (ancho de pantalla, mínimo 1100 px) y dos alturas: general y celular
    assert "--ancho-relieve: max(100%, 1100px);" in CSS
    assert CSS.count("background-position: center calc(max(100vw, 1100px) * -0.27);") == 1
    assert CSS.count("background-position: center calc(max(100vw, 1100px) * -0.08);") == 1
    assert "--relieve-escala" not in CSS


def test_imagenes_del_css_existen():
    for ruta in re.findall(r'url\("?\.\./([^")]+)"?\)', CSS):
        assert (RAIZ / ruta).is_file(), f"No existe: {ruta}"


def test_relieve_pesa_menos_de_300_kb_y_no_tiene_codigo():
    relieve = RAIZ / "img" / "relieve-valle.svg"
    assert relieve.stat().st_size < PESO_MAXIMO_RELIEVE_BYTES
    texto = relieve.read_text(encoding="utf-8").lower()
    assert "<script" not in texto and "href=" not in texto


def test_creditos_de_datos_en_el_pie():
    texto = INDEX.read_text(encoding="utf-8")
    assert (
        "produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH "
        "2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved"
    ) in texto
    assert "colaboradores de OpenStreetMap" in texto


def test_sin_rutas_locales_del_equipo():
    texto = INDEX.read_text(encoding="utf-8") + CSS
    assert "/Users/" not in texto
    assert "file://" not in texto
