# Arquitectura — Pronty Outlet

## 1. Visión general
Pronty Outlet utiliza una arquitectura web basada en Django y separación funcional por aplicaciones.

## 2. Componentes principales

```text
pronty-outlet/
├── accounts/
├── cart/
├── catalog/
├── config/
├── content/
├── live_sales/
├── static/
├── templates/
├── media/
├── manage.py
├── requirements.txt
├── package.json
└── README.md
```

## 3. Aplicaciones

### accounts
Responsable de:
- autenticación;
- registro;
- cuenta de cliente;
- acceso del cliente a Pronty Live.

### cart
Responsable de:
- carrito;
- operaciones de compra relacionadas con carrito.

### catalog
Responsable de:
- categorías;
- marcas;
- productos;
- catálogo;
- filtros;
- Home;
- inventario relacionado con productos.

### content
Responsable de:
- Cómo comprar.
- Contacto.
- Envíos.
- Cambios y devoluciones.
- FAQ.
- Términos.
- Privacidad.
- Tratamiento de datos.
- Cookies.

### live_sales
Responsable de:
- sesiones Live;
- clientes Live;
- activaciones;
- QR;
- asignaciones;
- pedidos derivados del Live;
- reportes.

### config
Contiene configuración global del proyecto Django.

## 4. Frontend
La interfaz utiliza:
- templates Django;
- SCSS;
- CSS compilado;
- JavaScript;
- Lucide Icons;
- Font Awesome.

## 5. Persistencia
En desarrollo se utiliza SQLite.

Para producción se recomienda utilizar una base de datos de mayor robustez, por ejemplo PostgreSQL.

## 6. Variables de entorno
Los secretos se cargan mediante `.env`.

Variables conocidas:
- `DJANGO_SECRET_KEY`
- `ALLOWED_HOSTS`
- `QR_BASE_URL`

## 7. Inventario
El sistema utiliza movimientos para conservar trazabilidad de entradas, salidas y reservas.

## 8. Pronty Live
Flujo conceptual:

```text
Live
  ↓
Cliente activado
  ↓
Escaneo QR
  ↓
Asignación
  ↓
Reserva de inventario
  ↓
Conversión a pedido o liberación
  ↓
Reporte
```

## 9. Seguridad
Principios:
- secretos fuera del repositorio;
- control de acceso por autenticación;
- separación de cliente y staff;
- HTTPS en producción;
- `DEBUG=False` en producción.

## 10. Evolución recomendada
- PostgreSQL.
- almacenamiento externo de media;
- correo transaccional;
- pruebas automatizadas;
- monitoreo;
- backups;
- CI/CD.

## 11. Arquitectura objetivo de producción

La arquitectura definida para la primera etapa de producción busca minimizar costos fijos sin sacrificar seguridad ni capacidad de crecimiento.

```text
Internet
   |
 HTTPS
   |
Google Cloud Run
Django / Pronty Outlet
   |
   +---- Neon PostgreSQL
   |
   +---- Cloudflare R2 (media)
```

### Componentes

- **Google Cloud Run:** ejecución de la aplicación Django mediante contenedor.
- **Neon PostgreSQL:** base de datos PostgreSQL administrada para producción.
- **Cloudflare R2:** almacenamiento persistente para imágenes y archivos media.
- **GitHub:** código fuente, historial de cambios y validaciones automáticas.
- **WhiteNoise:** entrega de archivos estáticos del proyecto.
- **Gunicorn:** servidor WSGI de producción.

### Estrategia de costos

En la etapa inicial se priorizan los niveles gratuitos de Cloud Run, Neon y Cloudflare R2. El costo mensual esperado puede mantenerse cercano a **$0 COP** mientras el uso permanezca dentro de los límites gratuitos de cada proveedor.

El principal costo fijo previsto al inicio es el dominio comercial, estimado de forma orientativa entre **$60.000 y $100.000 COP al año**, según extensión y proveedor.

Los límites, precios y condiciones de los proveedores pueden cambiar; antes del despliegue definitivo deben verificarse nuevamente.

### Escalabilidad

Cloud SQL no se utilizará en la primera etapa. Se evaluará posteriormente si el volumen de tráfico, pedidos o requerimientos operativos justifican asumir una infraestructura de base de datos con mayor costo fijo.
