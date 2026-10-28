# Diseño: publicación del dashboard en GitHub

## Propósito

Entregar únicamente el dashboard de mortalidad en Colombia 2019 como un repositorio público, claro y reproducible, con documentación académica, datos, capturas e instrucciones de ejecución y despliegue.

## Alcance y restricciones

- Único proyecto autorizado: `/home/billy/Descargas/tradajo_dash_app`.
- No inicializar, vincular, modificar ni publicar ningún otro proyecto.
- Crear un solo repositorio en la cuenta de GitHub que autorice el usuario.
- Nombre propuesto: `mortalidad-colombia-2019-dash`.
- No copiar ni publicar llaves SSH, credenciales, archivos `.env`, entornos virtuales, cachés ni respaldos.
- GitHub CLI se instalará solo dentro de `.tools/` en este proyecto, sin `sudo` ni instalación global; ese directorio quedará excluido de Git.

## Alternativas consideradas

1. **Preparar solo el repositorio local:** evita autenticación, pero no entrega la URL solicitada.
2. **Preparar y publicar este proyecto:** entrega el repositorio y su URL; requiere autenticación del usuario mediante el flujo oficial de GitHub.

Se eligió la segunda alternativa, limitada expresamente a este proyecto.

## Trabajo acordado

- Actualizar `README.md` con introducción, objetivo, estructura, requisitos, software, instalación, despliegue y visualizaciones comentadas.
- Documentar el despliegue real en AWS EC2 y, por separado, el procedimiento alternativo en Render.
- Conservar los datos procesados necesarios para ejecutar la aplicación y los Excel originales necesarios para regenerarlos; su tamaño total es compatible con GitHub sin LFS.
- Añadir capturas del dashboard y de la experiencia móvil en `docs/images/`.
- Incorporar hallazgos calculados desde los datos y aclarar que el gráfico de menor mortalidad usa conteos, no tasas poblacionales.
- Añadir `.gitignore` y retirar del alcance de Git respaldos, cachés, herramientas locales y secretos.
- Revisar que las versiones documentadas correspondan a un entorno de ejecución verificado.
- Inicializar Git únicamente en la raíz indicada, crear un commit y publicar la rama principal en el nuevo repositorio.

## Validación

- Ejecutar todas las pruebas y la compilación de `app.py`.
- Comprobar que los datos y geometrías requeridos estén incluidos.
- Verificar los enlaces e imágenes del README y las instrucciones de instalación.
- Revisar los archivos versionados para impedir la inclusión de secretos o de otro proyecto.
- Confirmar que el repositorio remoto contiene el commit local y entregar su URL pública.
