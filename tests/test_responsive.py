import unittest

import app


def _find_id(layout, id_):
    """Recorre el layout de Dash buscando un componente por id."""
    if isinstance(layout, str):
        return None
    if not isinstance(layout, dict):
        layout = layout.to_plotly_json()
    if layout.get("props", {}).get("id") == id_:
        return layout
    children = layout.get("props", {}).get("children") or []
    if not isinstance(children, list):
        children = [children]
    for child in children:
        if child is None or isinstance(child, str):
            continue
        found = _find_id(child, id_)
        if found:
            return found
    return None


def _dump(layout):
    """Devuelve una representación recursiva en texto del layout."""
    if isinstance(layout, str):
        return layout
    if not isinstance(layout, dict):
        layout = layout.to_plotly_json()
    props = layout.get("props", {})
    text = f"type={layout.get('type', '')} id={props.get('id')} class={props.get('className')}"
    children = props.get("children", [])
    if not isinstance(children, list):
        children = [children]
    return " ".join([text] + [_dump(c) for c in children if c is not None])


class ResponsiveLayoutTests(unittest.TestCase):
    def test_layout_tiene_boton_menu_hamburguesa(self):
        btn = _find_id(app.app.layout, "boton-menu")
        self.assertIsNotNone(btn, "Falta el botón hamburguesa (#boton-menu)")
        self.assertIn("boton-menu", btn["props"].get("className", ""))

    def test_layout_tiene_menu_de_filtros(self):
        menu = _find_id(app.app.layout, "menu-filtros")
        self.assertIsNotNone(menu, "Falta el contenedor de filtros (#menu-filtros)")
        for fid in ["filtro-departamento", "filtro-mes", "filtro-causa", "filtro-sexo"]:
            self.assertIsNotNone(
                _find_id(menu, fid),
                f"Falta filtro {fid} dentro del menú"
            )

    def test_layout_tiene_contenedor_responsive(self):
        dumped = _dump(app.app.layout)
        for cls in ["contenedor-dashboard", "columna-izquierda", "columna-derecha", "mapa-envoltorio"]:
            self.assertIn(cls, dumped, f"Falta clase {cls} en el layout")

    def test_css_incluye_media_query_movil(self):
        css = app.app.index_string
        self.assertIn("@media (max-width: 900px)", css, "Falta media query para móvil")

    def test_callback_menu_esta_registrado(self):
        outputs = [str(cb["output"]) for cb in app.app.callback_map.values()]
        self.assertTrue(
            any("menu-filtros" in out and "className" in out for out in outputs),
            "Falta callback que controle la clase de #menu-filtros"
        )

    def test_alternar_menu_preserva_clase_base(self):
        self.assertEqual(app.alternar_menu(0, "menu-filtros"), "menu-filtros")
        self.assertEqual(app.alternar_menu(1, "menu-filtros"), "menu-filtros abierto")
        self.assertEqual(app.alternar_menu(2, "menu-filtros abierto"), "menu-filtros")

    def test_selector_cartografia_queda_bajo_menu_movil(self):
        contenedor = app.app.layout.children[1]
        mapa = contenedor.children[0]
        selector = mapa.children[1]
        self.assertIn("selector-cartografia", selector.className)
        self.assertLess(
            selector.style["zIndex"],
            2000,
            "El selector de cartografía no debe tapar el menú del encabezado",
        )


if __name__ == "__main__":
    unittest.main()
