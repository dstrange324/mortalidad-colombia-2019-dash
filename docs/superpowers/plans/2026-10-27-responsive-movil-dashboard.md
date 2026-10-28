# Responsive móvil para dashboard de mortalidad Colombia 2019

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (recommended) o superpowers:subagent-driven-development para implementar este plan tarea por tarea.

**Goal:** Hacer que el dashboard Dash se adapte a pantallas móviles manteniendo el diseño actual de escritorio.

**Architecture:** Se añaden media queries CSS en `app.index_string` y se reestructura `app.layout` para usar un contenedor principal que, por encima de 900 px, mantiene el mapa a pantalla completa con paneles flotantes laterales; por debajo de 900 px, apila el mapa y las seis gráficas en una sola columna vertical. El botón hamburguesa controla la visibilidad del menú de filtros mediante un clientside callback de Dash.

**Tech Stack:** Python, Dash (`dash==4.4.1`), Plotly, CSS puro, clientside callback (`app.clientside_callback`).

**Spec:** docs/superpowers/specs/2026-10-27-responsive-movil-dashboard.md (diseño corto aprobado por el usuario: barra superior siempre visible, hamburguesa solo con filtros, mapa arriba y gráficas apiladas debajo en móvil, escritorio sin cambios).

## Global Constraints

- No instalar nuevas dependencias; usar solo CSS + Dash nativo.
- Mantener el diseño de escritorio tal cual está aprobado.
- Punto de quiebre: 900 px (`max-width: 900px`).
- Los KPIs y el selector de cartografía deben permanecer visibles; solo los filtros van dentro del menú hamburguesa.

## Review Focus

- Vista móvil real (ancho ≤900 px): el menú hamburguesa abre/cierra, los filtros se alcanzan, no hay scroll horizontal.
- Vista escritorio (ancho >900 px): el layout actual no se rompe ni cambia de posición.
- Recarga en móvil: el estado inicial del menú es cerrado.
- Filtros aplicados desde el menú hamburguesa: actualizan el dashboard igual que en escritorio.
- Selector de cartografía sigue visible y funcional sobre el mapa en ambas vistas.

---

## File Structure

- `app.py` (modificar): contiene el CSS en `app.index_string`, el `app.layout` y el clientside callback.

## Task 1: Reestructurar el layout para soportar modo escritorio y móvil

**Files:**
- Modify: `app.py:565-700`

**Interfaces:**
- Consumes: funciones `seccion(...)` y figuras iniciales existentes.
- Produces: estructura DOM con clases `.contenedor-dashboard`, `.columna-izquierda`, `.columna-derecha`, `.panel-movil` y `#menu-filtros`.

- [ ] **Step 1: Inspeccionar el layout actual y confirmar estructura**

Leer `app.py` líneas 565-700 y verificar que los IDs de los filtros son: `filtro-departamento`, `filtro-mes`, `filtro-causa`, `filtro-sexo`.

- [ ] **Step 2: Reemplazar paneles laterales absolutos por columnas dentro de un contenedor relativo**

Cambiar `app.layout` para que tenga:
1. `dcc.Graph` del mapa con id `mapa-departamentos` y clase `mapa-principal`.
2. `html.Header` con clase `encabezado`, que incluya un botón hamburguesa (`html.Button` con id `boton-menu`, clase `boton-menu`) visible solo en móvil.
3. Un `html.Div` con clase `contenedor-dashboard` que contenga:
   - `.columna-izquierda` con las 3 gráficas izquierdas.
   - `.mapa-envoltorio` envolviendo el mapa (para controlar altura en móvil).
   - `.columna-derecha` con las 3 gráficas derechas.
4. Un `html.Div` con id `menu-filtros` y clase `menu-filtros` que contenga los 4 filtros desplegables.
5. El selector de cartografía sigue siendo un `html.Div` flotante dentro del `.mapa-envoltorio`.

En escritorio, el contenedor usará flex/grid para colocar columnas laterales alrededor del mapa a pantalla completa; en móvil, el contenedor se vuelve flujo de bloques (mapa primero, columnas debajo).

- [ ] **Step 3: Verificar que el layout renderiza sin errores**

Run: `python3 -c "from app import app; print('layout OK')"`
Expected: `layout OK`

- [ ] **Step 4: Confirmar que los IDs de filtros no cambian**

Run: `python3 -c "from app import app; s=str(app.layout); print(all(x in s for x in ['filtro-departamento','filtro-mes','filtro-causa','filtro-sexo']))"`
Expected: `True`

## Task 2: Añadir CSS responsive y estilos del menú hamburguesa

**Files:**
- Modify: `app.py:457-532` (bloque `<style>` dentro de `app.index_string`)

**Interfaces:**
- Consumes: clases DOM introducidas en Task 1.
- Produces: reglas CSS que hacen el diseño responsive sin romper escritorio.

- [ ] **Step 1: Definir estilos base del contenedor y columnas (escritorio)**

Añadir:
```css
.contenedor-dashboard {
    position: fixed; top: 82px; left: 0; right: 0; bottom: 0;
    display: flex; justify-content: space-between; pointer-events: none;
}
.columna-izquierda, .columna-derecha {
    width: 440px; pointer-events: auto;
    display: flex; flex-direction: column; gap: 10px;
    padding: 14px; box-sizing: border-box;
    height: calc(100vh - 112px); overflow: hidden;
}
.mapa-envoltorio {
    flex: 1; position: relative; pointer-events: auto;
}
.mapa-principal {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
}
```

- [ ] **Step 2: Añadir media query para móvil (≤900px)**

Añadir `@media (max-width: 900px)` que:
- Oculte `.columna-izquierda` y `.columna-derecha` como columnas laterales.
- Muestre `.contenedor-dashboard` como bloque, con `position: relative; top: auto; height: auto; overflow-y: auto;`.
- `.mapa-envoltorio` tenga altura fija, p. ej. `height: 55vh`.
- Las columnas se vuelvan `width: 100%; height: auto; padding: 10px;` y se apilen verticalmente.
- Cada `.grafica` tenga altura adecuada para móvil, p. ej. `height: 320px`.
- El botón hamburguesa se muestre (`display: block`).
- El menú de filtros se posicione fijo por encima del header, ocupando todo el ancho, con fondo blanco y sombra; inicialmente oculto (`transform: translateY(-100%)`) o `display: none`.

- [ ] **Step 3: Estilizar botón hamburguesa y menú de filtros**

Añadir:
```css
.boton-menu {
    display: none; background: transparent; border: none;
    font-size: 22px; cursor: pointer; color: #16324f;
}
.menu-filtros {
    position: fixed; top: 0; left: 0; right: 0;
    background: rgba(255,255,255,0.98); z-index: 3000;
    padding: 18px; box-shadow: 0 4px 20px rgba(15,35,60,0.15);
    transform: translateY(-110%); transition: transform .25s ease;
}
.menu-filtros.abierto { transform: translateY(0); }
@media (max-width: 900px) { .boton-menu { display: block; } }
```

- [ ] **Step 4: Verificar que el CSS no produce errores de sintaxis**

Run: `python3 -c "from app import app; print('CSS parseado por Dash')"`
Expected: `CSS parseado por Dash`

## Task 3: Implementar clientside callback para el menú hamburguesa

**Files:**
- Modify: `app.py` (después del callback principal)

**Interfaces:**
- Consumes: clics en `#boton-menu`.
- Produces: clase CSS `abierto` en `#menu-filtros`.

- [ ] **Step 1: Añadir clientside callback**

Añadir después del callback principal:
```python
app.clientside_callback(
    """
    function(n_clicks, className) {
        if (!n_clicks) return '';
        return className ? '' : 'abierto';
    }
    """,
    Output('menu-filtros', 'className'),
    Input('boton-menu', 'n_clicks'),
    State('menu-filtros', 'className')
)
```

- [ ] **Step 2: Verificar que el clientside callback se registra sin error**

Run: `python3 -c "from app import app; print('callbacks:', len(app.callback_map))"`
Expected: número mayor que el inicial (confirmar que aumentó en 1).

## Task 4: Prueba visual en escritorio y móvil

**Files:**
- Modify: ninguno (solo verificación).

**Interfaces:**
- Consumes: aplicación Dash corriendo.
- Produces: confirmación de que ambas vistas se ven correctamente.

- [ ] **Step 1: Levantar servidor local**

Run: `.venv/bin/python app.py` (background) y esperar a que responda.

- [ ] **Step 2: Verificar escritorio**

Abrir `http://localhost:8050` y comprobar que el layout es igual al actual: mapa a pantalla completa, columnas laterales, filtros en la barra superior.

- [ ] **Step 3: Verificar móvil**

Usar el navegador en modo responsive (ancho ≤900 px, p. ej. iPhone SE) y comprobar:
- Barra superior visible con botón ☰.
- Al tocar ☰ se abre el menú con los 4 filtros.
- Al cerrar el menú los filtros desaparecen.
- El mapa ocupa la parte superior y las 6 gráficas están apiladas debajo.
- No aparece scroll horizontal.
- El selector de cartografía está sobre el mapa.

- [ ] **Step 4: Verificar que los filtros siguen funcionando**

Seleccionar un departamento y un sexo desde el menú móvil y confirmar que los KPIs y gráficas se actualizan.

## Task 5: Desplegar en EC2

**Files:**
- Modify: `app.py` en servidor remoto (vía scp).

**Interfaces:**
- Consumes: `app.py` local actualizado.
- Produces: aplicación reiniciada y accesible en `http://34.203.223.230:8050`.

- [ ] **Step 1: Subir `app.py` al servidor**

Run:
```bash
scp -i "/home/billy/Documentos/Maestria_IA_SALLE/APLICACIONES/tarea_dash.pem" app.py ubuntu@ec2-34-203-223-230.compute-1.amazonaws.com:/home/ubuntu/dash_app/app.py
```
Expected: `SCP OK`

- [ ] **Step 2: Reiniciar servicio y verificar**

Run:
```bash
ssh -i "/home/billy/Documentos/Maestria_IA_SALLE/APLICACIONES/tarea_dash.pem" ubuntu@ec2-34-203-223-230.compute-1.amazonaws.com 'sudo systemctl restart dashapp && sleep 8 && systemctl is-active dashapp && curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8050/'
```
Expected: `active` y `HTTP 200`.

- [ ] **Step 3: Verificar acceso público**

Run:
```bash
curl -s -o /dev/null -w "Publico -> HTTP %{http_code}\n" http://34.203.223.230:8050/
```
Expected: `Publico -> HTTP 200`.

---

## Self-Review

1. **Spec coverage:** cada requerimiento del diseño corto tiene tarea(s): barra visible (Task 1/2), hamburguesa con filtros (Task 1/2/3), mapa arriba y gráficas apiladas (Task 1/2), escritorio sin cambios (Task 1/2), sin nuevas dependencias (Global Constraints). OK.
2. **Step scan:** cada paso describe una acción concreta y verificable. OK.
3. **Type consistency:** IDs de filtros y figuras no cambian; los callbacks existentes no se tocan. OK.
4. **Review Focus:** cada riesgo listado se verifica en Task 4 (vistas móvil/escritorio, recarga, filtros, cartografía). OK.
5. **Proporción:** el plan es más corto que el cambio de código; no transcribe el cuerpo de las funciones de figuras. OK.
