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