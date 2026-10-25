"""Genera img/relieve-valle.svg: curvas de nivel, río Medellín y malla vial del Valle de Aburrá.

Fuentes (datos abiertos):
- Relieve: Copernicus DEM GLO-30, tesela N06 W076, desde el repositorio oficial
  de datos abiertos de AWS (bucket copernicus-dem-30m).
- Vías y río: OpenStreetMap, por medio de la API Overpass.

Los datos crudos se guardan en datos/crudos/ (no se suben a GitHub). Si ya están
descargados, el script los reutiliza en lugar de volver a pedirlos.

Uso, desde la carpeta del proyecto:
    python3 tools/generar_relieve.py
"""

import json
from pathlib import Path

import numpy as np
import rasterio
import requests
from pyproj import Transformer
from rasterio.transform import xy
from rasterio.windows import from_bounds
from scipy.ndimage import gaussian_filter
from shapely.geometry import LineString, MultiLineString, box
from shapely.ops import linemerge
from skimage.measure import find_contours

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_CRUDOS = RAIZ / "datos" / "crudos"
ARCHIVO_DEM = CARPETA_CRUDOS / "dem_valle_aburra.tif"
ARCHIVO_VIAS = CARPETA_CRUDOS / "vias_osm.json"
ARCHIVO_RIOS = CARPETA_CRUDOS / "rios_osm.json"
ARCHIVO_SVG = RAIZ / "img" / "relieve-valle.svg"

# Zona de trabajo: (oeste, sur, este, norte) en grados
ZONA = (-75.75, 6.00, -75.25, 6.52)

URL_TESELA_DEM = (
    "https://copernicus-dem-30m.s3.amazonaws.com/"
    "Copernicus_DSM_COG_10_N06_00_W076_00_DEM/Copernicus_DSM_COG_10_N06_00_W076_00_DEM.tif"
)
URL_OVERPASS = "https://overpass-api.de/api/interpreter"
AGENTE = "portafolio-juliandpr10 (generador de relieve; uso único)"

TIPOS_PRINCIPALES = ("motorway", "trunk", "primary")
TIPOS_NORMALES = ("secondary", "tertiary", "residential")
# Cauce principal: en OpenStreetMap figura como "Río Medellín" (también llamado río Aburrá)
NOMBRES_RIO_PRINCIPAL = ("Río Medellín", "Río Aburrá")

INTERVALO_CURVAS_M = 100
INTERVALO_MAESTRAS_M = 500
SUAVIZADO_SIGMA_PX = 2.0

ANCHO_SVG = 1600
TOLERANCIA_CURVAS = 1.0  # unidades del SVG
TOLERANCIA_VIAS = 1.0
LARGO_MINIMO_CURVA = 10
LARGO_MINIMO_VIA = 5  # unos 175 m
TOLERANCIA_RIO = 0.6
LARGO_MINIMO_RIO = 3

# Estilos (ver DISENO.md). Las opacidades son el 40 % de las del diseño inicial
# (.16 / .30 / .10 / .18): con esas, donde una curva maestra cruza una vía principal
# detrás de un texto, el contraste bajaba de 4,5:1. Si las cambias, corre pytest:
# la prueba de contraste de la portada usa estos mismos valores.
ESTILO_CURVAS = 'stroke="#8FA6BF" stroke-opacity=".06" stroke-width=".8"'
ESTILO_MAESTRAS = 'stroke="#8FA6BF" stroke-opacity=".12" stroke-width="1.2"'
ESTILO_VIAS = 'stroke="#C9D1DA" stroke-opacity=".04" stroke-width=".6"'
ESTILO_PRINCIPALES = 'stroke="#C9D1DA" stroke-opacity=".07" stroke-width="1"'
# Río: visible pero sobrio. Atraviesa la portada por la mitad, también detrás del texto
# (decisión de diseño aprobada; ver DISENO.md).
ESTILO_RIO = 'stroke="#A9C7E8" stroke-opacity=".55" stroke-width="2.4"'


# ---------- Descarga ----------


def descargar_dem(destino=ARCHIVO_DEM, zona=ZONA):
    """Lee de la tesela oficial solo el recorte de la zona y lo guarda como GeoTIFF."""
    if destino.exists():
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(URL_TESELA_DEM) as fuente:
        ventana = from_bounds(*zona, transform=fuente.transform)
        alturas = fuente.read(1, window=ventana)
        perfil = fuente.profile.copy()
        perfil.update(
            driver="GTiff",
            height=alturas.shape[0],
            width=alturas.shape[1],
            transform=fuente.window_transform(ventana),
            compress="deflate",
        )
        for clave in ("blockxsize", "blockysize", "tiled", "interleave"):
            perfil.pop(clave, None)
    with rasterio.open(destino, "w", **perfil) as salida:
        salida.write(alturas, 1)
    return destino


def consulta_overpass(zona=ZONA, tipos=TIPOS_PRINCIPALES + TIPOS_NORMALES):
    """Texto de la consulta Overpass: vías de los tipos dados, con su geometría."""
    oeste, sur, este, norte = zona
    patron = "|".join(tipos)
    return f'[out:json][timeout:180];way["highway"~"^({patron})$"]({sur},{oeste},{norte},{este});out geom;'


def consulta_overpass_rios(zona=ZONA):
    """Consulta Overpass: ríos (waterway=river) de la zona y, además, el tramo canalizado
    del río Medellín por el centro de la ciudad, que OpenStreetMap marca como canal."""
    oeste, sur, este, norte = zona
    marco = f"({sur},{oeste},{norte},{este})"
    nombres = "|".join(NOMBRES_RIO_PRINCIPAL)
    return (
        f'[out:json][timeout:120];(way["waterway"="river"]{marco};'
        f'way["waterway"="canal"]["name"~"^({nombres})$"]{marco};);out geom;'
    )


def descargar_de_overpass(consulta, destino):
    """Hace la consulta a Overpass y guarda la respuesta tal cual (JSON)."""
    if destino.exists():
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    respuesta = requests.post(
        URL_OVERPASS, data={"data": consulta}, headers={"User-Agent": AGENTE}, timeout=300
    )
    respuesta.raise_for_status()
    destino.write_bytes(respuesta.content)
    return destino


def descargar_vias(destino=ARCHIVO_VIAS):
    return descargar_de_overpass(consulta_overpass(), destino)


def descargar_rios(destino=ARCHIVO_RIOS):
    return descargar_de_overpass(consulta_overpass_rios(), destino)


# ---------- Curvas de nivel ----------


def niveles_de_curva(altura_minima, altura_maxima, intervalo=INTERVALO_CURVAS_M):
    """Alturas redondas (múltiplos del intervalo) dentro del rango del terreno."""
    primero = int(np.ceil(altura_minima / intervalo) * intervalo)
    return list(range(primero, int(altura_maxima) + 1, intervalo))


def es_curva_maestra(nivel, intervalo_maestras=INTERVALO_MAESTRAS_M):
    return nivel % intervalo_maestras == 0


def curvas_de_nivel(alturas, transformacion, niveles):
    """Lista de (nivel, [(lon, lat), ...]) para cada curva encontrada."""
    curvas = []
    for nivel in niveles:
        for linea in find_contours(alturas, nivel):
            filas, columnas = linea[:, 0], linea[:, 1]
            lon, lat = xy(transformacion, filas, columnas, offset="center")
            curvas.append((nivel, list(zip(lon, lat, strict=True))))
    return curvas


# ---------- Vías ----------


def vias_desde_overpass(datos):
    """Lista de (tipo, [(lon, lat), ...]) a partir de la respuesta de Overpass."""
    vias = []
    for elemento in datos.get("elements", []):
        geometria = elemento.get("geometry") or []
        tipo = elemento.get("tags", {}).get("highway")
        if tipo and len(geometria) >= 2:
            vias.append((tipo, [(punto["lon"], punto["lat"]) for punto in geometria]))
    return vias


def es_via_principal(tipo):
    return tipo in TIPOS_PRINCIPALES


# ---------- Río ----------


def es_cauce_principal(etiquetas):
    """True si es el río Medellín (Aburrá), por su nombre o nombre alterno. Nada de quebradas.
    Se acepta "canal" porque así figura su tramo canalizado por el centro de Medellín
    (sin él, el río tendría un hueco de unos 13 km)."""
    nombres = (etiquetas.get(clave, "") for clave in ("name", "alt_name", "official_name"))
    return etiquetas.get("waterway") in ("river", "canal") and any(
        n in NOMBRES_RIO_PRINCIPAL for n in nombres
    )


def rio_desde_overpass(datos):
    """Tramos [(lon, lat), ...] del cauce principal a partir de la respuesta de Overpass."""
    tramos = []
    for elemento in datos.get("elements", []):
        geometria = elemento.get("geometry") or []
        if es_cauce_principal(elemento.get("tags", {})) and len(geometria) >= 2:
            tramos.append([(punto["lon"], punto["lat"]) for punto in geometria])
    return tramos


# ---------- Proyección y encuadre ----------


class Encuadre:
    """Convierte lon/lat a coordenadas del SVG (UTM zona 18N, norte arriba)."""

    def __init__(self, zona=ZONA, ancho=ANCHO_SVG):
        self.proyectar = Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True).transform
        oeste, sur, este, norte = zona
        esquinas_x, esquinas_y = self.proyectar([oeste, este, oeste, este], [sur, sur, norte, norte])
        self.x_min, self.x_max = min(esquinas_x), max(esquinas_x)
        self.y_min, self.y_max = min(esquinas_y), max(esquinas_y)
        self.escala = ancho / (self.x_max - self.x_min)
        self.ancho = ancho
        self.alto = round((self.y_max - self.y_min) * self.escala)

    def a_svg(self, puntos_lonlat):
        lon, lat = zip(*puntos_lonlat, strict=True)
        x, y = self.proyectar(list(lon), list(lat))
        return [
            ((xi - self.x_min) * self.escala, (self.y_max - yi) * self.escala)
            for xi, yi in zip(x, y, strict=True)
        ]


def unir_tramos(lineas):
    """Une en una sola línea los tramos que comparten extremos (menos trazos, SVG más liviano)."""
    unidas = linemerge(MultiLineString([LineString(puntos) for puntos in lineas if len(puntos) >= 2]))
    partes = getattr(unidas, "geoms", [unidas])
    return [list(p.coords) for p in partes if not p.is_empty]


def simplificar_y_recortar(puntos, ancho, alto, tolerancia, largo_minimo):
    """Simplifica la línea, la recorta al marco y descarta trozos muy cortos."""
    linea = LineString(puntos).simplify(tolerancia, preserve_topology=False)
    recortada = linea.intersection(box(0, 0, ancho, alto))
    partes = getattr(recortada, "geoms", [recortada])
    return [list(p.coords) for p in partes if p.geom_type == "LineString" and p.length >= largo_minimo]


# ---------- SVG ----------


def trazo_svg(puntos):
    """Trazo compacto: punto inicial absoluto y el resto como desplazamientos enteros."""
    enteros = [(round(x), round(y)) for x, y in puntos]
    limpios = [enteros[0]] + [p for anterior, p in zip(enteros, enteros[1:], strict=False) if p != anterior]
    if len(limpios) < 2:
        return ""
    x0, y0 = limpios[0]
    pasos = []
    for (xa, ya), (xb, yb) in zip(limpios, limpios[1:], strict=False):
        pasos.append(f"{xb - xa} {yb - ya}")
    return f"M{x0} {y0}l" + " ".join(pasos).replace(" -", "-")


def grupo_svg(estilo, trazos):
    trazos = [t for t in trazos if t]
    return f'<g {estilo}><path d="{"".join(trazos)}"/></g>' if trazos else ""


def armar_svg(ancho, alto, grupos):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" '
        'preserveAspectRatio="xMidYMid slice" fill="none" stroke-linejoin="round" stroke-linecap="round">'
        "<style>path{vector-effect:non-scaling-stroke}</style>" + "".join(grupos) + "</svg>"
    )


# ---------- Programa principal ----------


def trazos_de(lineas, encuadre, tolerancia, largo_minimo):
    proyectadas = unir_tramos([encuadre.a_svg(puntos) for puntos in lineas])
    trazos = []
    for puntos in proyectadas:
        for parte in simplificar_y_recortar(puntos, encuadre.ancho, encuadre.alto, tolerancia, largo_minimo):
            trazos.append(trazo_svg(parte))
    return trazos


def generar():
    descargar_dem()
    descargar_vias()
    descargar_rios()
    encuadre = Encuadre()

    with rasterio.open(ARCHIVO_DEM) as dem:
        alturas = gaussian_filter(dem.read(1).astype("float32"), SUAVIZADO_SIGMA_PX)
        transformacion = dem.transform
    curvas = curvas_de_nivel(alturas, transformacion, niveles_de_curva(alturas.min(), alturas.max()))
    vias = vias_desde_overpass(json.loads(ARCHIVO_VIAS.read_text(encoding="utf-8")))
    rio = rio_desde_overpass(json.loads(ARCHIVO_RIOS.read_text(encoding="utf-8")))

    # Orden de dibujo: relieve, río y encima las vías (los puentes pasan sobre el río)
    capas = [
        (
            ESTILO_CURVAS,
            [p for n, p in curvas if not es_curva_maestra(n)],
            TOLERANCIA_CURVAS,
            LARGO_MINIMO_CURVA,
        ),
        (
            ESTILO_MAESTRAS,
            [p for n, p in curvas if es_curva_maestra(n)],
            TOLERANCIA_CURVAS,
            LARGO_MINIMO_CURVA,
        ),
        (ESTILO_RIO, rio, TOLERANCIA_RIO, LARGO_MINIMO_RIO),
        (ESTILO_VIAS, [p for t, p in vias if not es_via_principal(t)], TOLERANCIA_VIAS, LARGO_MINIMO_VIA),
        (ESTILO_PRINCIPALES, [p for t, p in vias if es_via_principal(t)], TOLERANCIA_VIAS, LARGO_MINIMO_VIA),
    ]
    grupos = [
        grupo_svg(estilo, trazos_de(lineas, encuadre, tol, largo)) for estilo, lineas, tol, largo in capas
    ]
    ARCHIVO_SVG.write_text(armar_svg(encuadre.ancho, encuadre.alto, grupos), encoding="utf-8")

    print(f"Curvas: {len(curvas)}  Vías: {len(vias)}  Tramos del río: {len(rio)}")
    print(f"SVG: {ARCHIVO_SVG.relative_to(RAIZ)}  {ARCHIVO_SVG.stat().st_size // 1024} KB")


if __name__ == "__main__":
    generar()
