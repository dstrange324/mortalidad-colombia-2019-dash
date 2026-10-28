# Publicación del dashboard en GitHub — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publicar únicamente este dashboard en un repositorio público de GitHub, con datos, documentación, capturas e instrucciones verificadas.

**Architecture:** La aplicación permanece igual; se empaquetan sus archivos existentes y sus fuentes de datos. Git y GitHub CLI se configuran solo en la raíz del proyecto, y la validación se realiza sobre una copia clonada antes de publicar.

**Tech Stack:** Python 3.12, Dash, Plotly, pandas, Git, GitHub CLI, AWS EC2/Gunicorn.

**Spec:** `docs/superpowers/specs/2026-10-28-repositorio-github-design.md`

## Global Constraints

- Única raíz autorizada: `/home/billy/Descargas/tradajo_dash_app`.
- Único repositorio remoto propuesto: `mortalidad-colombia-2019-dash`; si ya existe, detenerse y solicitar otro nombre, sin sobrescribirlo.
- No modificar configuración global, usar `sudo`, publicar otro proyecto ni incluir credenciales.
- GitHub CLI y las comprobaciones temporales se guardan en `.tools/` y `.verification/`, ambos ignorados por Git.
- Conservar los Excel originales, los Parquet y los dos GeoJSON para permitir ejecución y regeneración.

## Review Focus

- Una copia clonada sin archivos locales ocultos debe arrancar y responder HTTP 200: Task 3.
- Ningún respaldo, entorno, llave o herramienta local debe quedar versionado: Tasks 1 y 4.
- Las rutas relativas de capturas del README deben existir y funcionar en GitHub: Tasks 2 y 4.
- Las cifras narrativas deben calcularse desde `data/mortalidad_2019.parquet`; menor mortalidad significa menor conteo, no tasa: Task 2.
- La URL remota debe ser pública y su rama `main` debe coincidir con el commit local: Task 4.

---

### Task 1: Aislamiento e higiene del repositorio

**Files:**
- Create: `.gitignore`
- Existing: `docs/superpowers/specs/2026-10-28-repositorio-github-design.md`, `docs/superpowers/plans/2026-10-28-repositorio-github.md`

**Interfaces:**
- Produces: raíz Git aislada y exclusiones que usan Tasks 3 y 4.

- [ ] **Step 1: Inicializar solo esta raíz**

Run: `git init` en la raíz autorizada, `git rev-parse --show-toplevel`, `git config --get user.name` y `git config --get user.email`.
Expected: la raíz es exactamente `/home/billy/Descargas/tradajo_dash_app` y existe identidad de autor. Si falta alguno de los dos valores, obtener primero el usuario y el ID mediante `gh api user` y configurar `user.name` y el correo `ID+USUARIO@users.noreply.github.com` solo con `git config --local`; nunca cambiar la configuración global.

- [ ] **Step 2: Crear exclusiones**

Incluir `.venv/`, `.tools/`, `.verification/`, `__pycache__/`, `*.py[cod]`, `.env`, `.env.*`, `*.pem`, `*.key`, `*.bak`, `*.bak.*` y `.DS_Store`.

- [ ] **Step 3: Verificar exclusiones**

Run: `git check-ignore .venv .tools .verification app.py.bak.20261027 tarea_dash.pem`.
Expected: todas las rutas son reconocidas como ignoradas; `git status --short` no muestra esos elementos.

- [ ] **Step 4: Commit de alcance**

Run: `git add .gitignore docs/superpowers` y `git commit -m "chore: definir alcance del repositorio"`.
Expected: commit creado solo con esos archivos.

### Task 2: README y evidencia visual

**Files:**
- Modify: `README.md`
- Create: `docs/images/dashboard-general.png`
- Create: `docs/images/mapa-municipios-movil.png`
- Create: `docs/images/menu-movil.png`

**Interfaces:**
- Consumes: aplicación pública `http://34.203.223.230:8050/` y datos de `data/`.
- Produces: documentación académica y tres imágenes referenciadas con rutas relativas.

- [ ] **Step 1: Calcular hallazgos**

Usar `.venv/bin/python` y pandas para obtener totales nacionales, departamentos destacados, extremos mensuales, cinco ciudades X95, diez causas principales, distribución por sexo y categorías de edad. No copiar cifras sin calcularlas.

- [ ] **Step 2: Copiar y verificar la evidencia final**

Copiar desde `/home/billy/.kimi-code/sessions/wd_tradajo_dash_app_e5390748a097/session_24b4191b-8da2-493f-8ac5-029924861a16/media/` estos PNG ya inspeccionados: `f_mcp_db05633df9cd9489391838aa8ab89bd352620d8726294ae38603da1fbd86ef8f.png` como `dashboard-general.png`, `f_mcp_068ef54c41dbb2ec68bf86af69c3e01b394ab86ca46be67bc54062cc66a0d645.png` como `mapa-municipios-movil.png` y `f_mcp_19d60ac7688381a7592fb9983847d3008e6e11467feeefd96700140df8120375.png` como `menu-movil.png`. Inspeccionar los tres archivos destino con lectura visual.

- [ ] **Step 3: Reescribir el README**

Incluir exactamente: Introducción, Objetivo, Estructura del proyecto, Requisitos, Despliegue, Software, Instalación y Visualizaciones con explicaciones de los resultados. Añadir fuente DANE, URL de la aplicación, cuatro filtros, AWS EC2 real, Render alternativo, pruebas y la aclaración conteo/tasa. Insertar las tres capturas junto a los hallazgos calculados.

- [ ] **Step 4: Verificar documentación**

Comprobar que todas las rutas Markdown de imágenes existen, que los ocho encabezados están presentes y que no quedan marcadores pendientes. Ejecutar `git diff --check`.
Expected: sin rutas faltantes, marcadores ni errores de espacios.

- [ ] **Step 5: Commit documental**

Run: `git add README.md docs/images` y `git commit -m "docs: documentar visualizaciones y ejecución"`.

### Task 3: Validación de una copia reproducible

**Files:**
- Add: `app.py`, `prep_data.py`, `requirements.txt`, `Procfile`, `tests/test_responsive.py`, los tres Excel y los cuatro archivos de `data/`.

**Interfaces:**
- Consumes: Tasks 1 y 2.
- Produces: commit local completo listo para publicar.

- [ ] **Step 1: Ejecutar la suite del proyecto**

Run: `.venv/bin/python -m unittest discover -s tests -p 'test*.py' -v && .venv/bin/python -m py_compile app.py`.
Expected: 7 pruebas OK y compilación sin errores.

- [ ] **Step 2: Crear el commit de la aplicación**

Agregar explícitamente los archivos anteriores, sin `git add .`, y crear `git commit -m "feat: entregar dashboard de mortalidad 2019"`.
Expected: `git ls-files` contiene todos los archivos necesarios y ninguna exclusión.

- [ ] **Step 3: Clonar y preparar un entorno limpio**

Clonar en `.verification/clone`, crear `.verification/venv` e instalar el `requirements.txt` del clon. Regenerar allí los Parquet con `prep_data.py`.
Expected: 244.355 registros de mortalidad y catálogos/geometrías disponibles.

- [ ] **Step 4: Ejecutar el clon**

Ejecutar `.verification/venv/bin/python -m unittest discover -s tests -p 'test*.py' -v` y `.verification/venv/bin/python -m py_compile app.py` en el clon, iniciar Gunicorn en `127.0.0.1:8061`, consultar `/` y `/_dash-layout`, y detener ese proceso temporal.
Expected: 7 pruebas OK, compilación sin errores, HTTP 200 y layout con cuatro filtros y mapa satelital.

### Task 4: Autenticación y publicación limitada

**Files:**
- Modify: `README.md` con la URL real de clonación.
- Local ignored: `.tools/` y `.verification/`.

**Interfaces:**
- Consumes: commit verificado de Task 3.
- Produces: repositorio público y URL entregable.

- [ ] **Step 1: Instalar GitHub CLI localmente**

Descargar el release oficial de `cli/cli` para la arquitectura detectada en `.tools/`, verificar su checksum oficial y ejecutar `.tools/.../gh --version`. No instalar globalmente.

- [ ] **Step 2: Autorizar la cuenta del usuario**

Ejecutar `gh auth status`; si es necesario, usar `gh auth login --hostname github.com --git-protocol https --web`. Obtener usuario e ID con `gh api user`. Configurar identidad Git solo en este repositorio si aún no existe.

- [ ] **Step 3: Incorporar la URL y auditar el contenido**

Construir la URL con el usuario autenticado y el nombre aprobado, actualizar las instrucciones de clonación y hacer commit. Comprobar con `git ls-files` que no hay rutas prohibidas y con `git rev-parse --show-toplevel` que la raíz sigue siendo la autorizada. Buscar con Grep en los archivos versionables de texto los patrones `-----BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY-----|AKIA[0-9A-Z]{16}|tarea_dash`; ninguno debe aparecer. Si hay una coincidencia real, detener la publicación y retirar el secreto sin exponerlo en la salida.

- [ ] **Step 4: Crear un único remoto**

Comprobar primero que el nombre no existe. Crear el repositorio público con `gh repo create`, fijar `origin`, renombrar la rama a `main` y ejecutar `git push -u origin main`. No modificar ningún repositorio existente.

- [ ] **Step 5: Verificar la entrega pública**

Comprobar HTTP 200 del repositorio y de las imágenes, y que `git ls-remote origin refs/heads/main` coincide con `git rev-parse HEAD`. Entregar la URL del repositorio, la URL del dashboard y el resultado de las validaciones.
