"""Pruebas de tools/generar_relieve.py (sin internet: solo las funciones de cálculo)."""

import numpy as np
from rasterio.transform import from_origin

from tools import generar_relieve as relieve


def test_consulta_overpass_pide_solo_los_tipos_de_via_acordados():
    consulta = relieve.consulta_overpass(zona=(-75.75, 6.0, -75.25, 6.52))
    assert '"^(motorway|trunk|primary|secondary|tertiary|residential)$"' in consulta
    assert "(6.0,-75.75,6.52,-75.25)" in consulta  # sur, oeste, norte, este
    assert "footway" not in consulta and "path" not in consulta
    assert consulta.endswith("out geom;")


def test_niveles_de_curva_cada_100_m():
    assert relieve.niveles_de_curva(1349.2, 1720.0) == [1400, 1500, 1600, 1700]


def test_curvas_maestras_cada_500_m():
    assert relieve.es_curva_maestra(1500)
    assert relieve.es_curva_maestra(2000)
    assert not relieve.es_curva_maestra(1600)


def test_curvas_de_nivel_en_coordenadas_geograficas():
    # Rampa que sube de oeste a este: 0, 100, 200, 300 m
    alturas = np.tile(np.array([0.0, 100.0, 200.0, 300.0]), (4, 1))
    transformacion = from_origin(-75.0, 6.0, 0.1, 0.1)
    curvas = relieve.curvas_de_nivel(alturas, transformacion, [150])
    assert len(curvas) == 1
    nivel, puntos = curvas[0]
    assert nivel == 150
    longitudes = {round(lon, 6) for lon, _ in puntos}
    assert longitudes == {-74.8}  # a medio camino entre la columna 1 y la 2


def test_vias_desde_overpass_lee_tipo_y_geometria():
    datos = {
        "elements": [
            {"tags": {"highway": "primary"}, "geometry": [{"lon": 1, "lat": 2}, {"lon": 3, "lat": 4}]},
            {"tags": {"highway": "residential"}, "geometry": [{"lon": 5, "lat": 6}]},  # un solo punto
            {"tags": {}, "geometry": [{"lon": 1, "lat": 1}, {"lon": 2, "lat": 2}]},  # sin tipo
        ]
    }
    assert relieve.vias_desde_overpass(datos) == [("primary", [(1, 2), (3, 4)])]


def test_consulta_overpass_rios_pide_rios_y_solo_el_canal_del_rio_medellin():
    consulta = relieve.consulta_overpass_rios(zona=(-75.75, 6.0, -75.25, 6.52))
    assert 'way["waterway"="river"](6.0,-75.75,6.52,-75.25)' in consulta
    assert 'way["waterway"="canal"]["name"~"^(Río Medellín|Río Aburrá)$"](6.0,-75.75,6.52,-75.25)' in consulta
    assert "stream" not in consulta
    assert consulta.endswith("out geom;")


def test_cauce_principal_solo_el_rio_medellin():
    assert relieve.es_cauce_principal({"waterway": "river", "name": "Río Medellín"})
    assert relieve.es_cauce_principal({"waterway": "river", "name": "Río Porce", "alt_name": "Río Aburrá"})
    assert not relieve.es_cauce_principal({"waterway": "river", "name": "Río Negro"})
    assert not relieve.es_cauce_principal({"waterway": "river", "name": "Quebrada La Iguaná"})
    assert not relieve.es_cauce_principal({"waterway": "stream", "name": "Río Medellín"})
    # Tramo canalizado por el centro de Medellín: sí; canales de quebradas: no
    assert relieve.es_cauce_principal({"waterway": "canal", "name": "Río Medellín"})
    assert not relieve.es_cauce_principal({"waterway": "canal", "name": "Quebrada La Mansión"})


def test_rio_desde_overpass_toma_solo_el_cauce_principal():
    datos = {
        "elements": [
            {
                "tags": {"waterway": "river", "name": "Río Medellín"},
                "geometry": [{"lon": 1, "lat": 2}, {"lon": 3, "lat": 4}],
            },
            {
                "tags": {"waterway": "river", "name": "Río Negro"},
                "geometry": [{"lon": 5, "lat": 6}, {"lon": 7, "lat": 8}],
            },
            {"tags": {"waterway": "river", "name": "Río Medellín"}, "geometry": [{"lon": 9, "lat": 9}]},
        ]
    }
    assert relieve.rio_desde_overpass(datos) == [[(1, 2), (3, 4)]]


def test_vias_principales():
    assert relieve.es_via_principal("trunk")
    assert relieve.es_via_principal("primary")
    assert not relieve.es_via_principal("residential")


def test_encuadre_pone_el_norte_arriba_y_respeta_el_ancho():
    encuadre = relieve.Encuadre(zona=(-75.75, 6.0, -75.25, 6.52), ancho=1600)
    assert encuadre.ancho == 1600
    assert 1500 < encuadre.alto < 1800  # la zona es casi cuadrada
    (x_so, y_so), (x_ne, y_ne) = encuadre.a_svg([(-75.75, 6.0), (-75.25, 6.52)])
    assert x_so < x_ne
    assert y_so > y_ne  # el sur queda abajo


def test_unir_tramos_que_se_tocan():
    unidas = relieve.unir_tramos([[(0, 0), (1, 0)], [(1, 0), (2, 0)], [(5, 5), (6, 6)]])
    assert len(unidas) == 2


def test_simplificar_y_recortar_al_marco():
    partes = relieve.simplificar_y_recortar(
        [(-10, 5), (0, 5), (5, 5.1), (20, 5)], ancho=10, alto=10, tolerancia=0.5, largo_minimo=1
    )
    assert len(partes) == 1
    xs = [x for x, _ in partes[0]]
    assert min(xs) >= 0 and max(xs) <= 10


def test_simplificar_descarta_lineas_cortas():
    assert relieve.simplificar_y_recortar([(1, 1), (2, 1)], 10, 10, 0.5, largo_minimo=3) == []


def test_trazo_svg_compacto_con_desplazamientos():
    assert relieve.trazo_svg([(10.2, 20.6), (13.4, 18.9), (13.4, 18.9), (11, 25)]) == "M10 21l3-2-2 6"
    assert relieve.trazo_svg([(1, 1), (1.2, 1.1)]) == ""  # se reduce a un punto


def test_grupo_y_svg_completos():
    grupo = relieve.grupo_svg('stroke="#fff"', ["M0 0l1 1", ""])
    assert grupo == '<g stroke="#fff"><path d="M0 0l1 1"/></g>'
    assert relieve.grupo_svg('stroke="#fff"', [""]) == ""
    svg = relieve.armar_svg(100, 50, [grupo])
    assert svg.startswith('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50"')
    assert "non-scaling-stroke" in svg
    assert svg.endswith("</svg>")
