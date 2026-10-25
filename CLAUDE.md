# Reglas de este proyecto

## Calidad
- Código claro antes que corto. Nombres que se entienden solos. Funciones pequeñas que hacen una sola cosa.
- Cada función nueva trae su prueba en tests/. Nada se da por terminado con pruebas en rojo.
- Solo cambia lo que se pidió. No toques lo que ya funciona.
- Antes de escribir código nuevo, explica el plan en 3-5 líneas y espera mi "ejecuta".

## Seguridad
- Nunca escribas claves, contraseñas ni tokens en el código. Léelas siempre de variables de entorno (.env).
- Valida todo lo que entra desde fuera (formularios, URLs, archivos) antes de usarlo.
- Toda página o API que muestre datos privados exige inicio de sesión.
- Todo lo que está en el navegador (HTML/JS) es público: nada secreto ahí.
- Rutas públicas con límite de peticiones por IP; login con límite de intentos.
- Contraseñas siempre con hash; datos personales nunca en logs.
- Sigue .claude/claude-security-guidance.md si existe.

## Verificación
- Antes de cada commit corre: ruff, bandit, pip-audit, gitleaks, pytest. Si algo falla, arréglalo y vuelve a correr.
- Al terminar, resume en 1-3 líneas qué revisaste y qué riesgo queda.
