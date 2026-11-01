# Guía de Despliegue a Producción — Pronty Outlet

## 1. Objetivo
Definir los pasos generales necesarios para publicar Pronty Outlet en Internet.

## 2. Antes de desplegar
Completar:
- pruebas funcionales;
- validación legal;
- revisión de seguridad;
- respaldo del proyecto;
- respaldo de datos.

## 3. Configuración
En producción:

```env
DEBUG=False
```

Configurar:
- `DJANGO_SECRET_KEY`;
- `ALLOWED_HOSTS`;
- `QR_BASE_URL`;
- base de datos;
- correo si se habilita;
- variables del proveedor de hosting.

## 4. Base de datos
Se recomienda PostgreSQL para producción.

## 5. Dominio
Definir el dominio comercial oficial de Pronty Outlet.

## 6. HTTPS
Todo el tráfico público debe utilizar HTTPS.

## 7. Archivos estáticos
Configurar correctamente:
- CSS;
- JavaScript;
- imágenes estáticas.

Ejecutar cuando corresponda:

```powershell
python manage.py collectstatic
```

## 8. Archivos media
Las imágenes de productos requieren almacenamiento persistente.

En producción se recomienda almacenamiento adecuado para media.

## 9. Migraciones

```powershell
python manage.py migrate
```

## 10. Usuario administrativo
Crear un superusuario de producción con credenciales seguras.

## 11. QR
`QR_BASE_URL` debe utilizar el dominio público HTTPS.

Ejemplo conceptual:

```env
QR_BASE_URL=https://www.dominio-pronty.com
```

## 12. Seguridad
Verificar:
- `DEBUG=False`;
- HTTPS;
- secretos fuera de Git;
- contraseñas seguras;
- backups;
- permisos;
- cookies seguras;
- configuración CSRF.

## 13. Backups
Definir:
- frecuencia;
- retención;
- prueba de restauración.

## 14. Monitoreo
Se recomienda registrar:
- errores;
- caídas;
- consumo;
- fallos de base de datos.

## 15. Checklist final
- [ ] Dominio configurado.
- [ ] HTTPS activo.
- [ ] Base de datos de producción.
- [ ] Migraciones aplicadas.
- [ ] Static configurado.
- [ ] Media persistente.
- [ ] Variables de entorno.
- [ ] `DEBUG=False`.
- [ ] Admin seguro.
- [ ] Backups.
- [ ] Pruebas finales.
- [ ] QR probado en celular.
- [ ] WhatsApp probado.
- [ ] Redes sociales probadas.
- [ ] Políticas legales aprobadas.