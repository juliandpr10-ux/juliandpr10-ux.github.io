# Guía de seguridad de este proyecto

## Qué protegemos
- Datos de personas (nombres, cédulas, teléfonos, direcciones): nunca en logs ni en mensajes de error.
- Credenciales: solo desde variables de entorno. Cualquier clave escrita en el código es un hallazgo crítico.

## Reglas de acceso
- Toda ruta que lea o cambie datos exige usuario autenticado.
- Toda ruta bajo /admin exige rol admin verificado en el servidor, nunca solo en el frontend.
- Un usuario solo puede ver o editar sus propios registros; revisar que cada consulta filtre por su id.

## Entradas
- Validar tipo, longitud y formato de todo lo que llega por formulario, URL o archivo antes de usarlo.
- Archivos subidos: solo extensiones permitidas, tamaño máximo definido, nunca ejecutarlos.
- Nunca construir consultas SQL ni comandos del sistema concatenando texto del usuario.

## Abuso
- Rutas públicas con límite de peticiones por IP.
- Login con límite de intentos y bloqueo temporal.

## Producción
- DEBUG desactivado, HTTPS obligatorio, cabeceras de seguridad activas.
- Si usa Firebase: ninguna regla con `if true`.
- Si usa Apps Script: claves en PropertiesService.
