# Pronty Outlet

Pronty Outlet es una plataforma de comercio electrónico desarrollada con Django para la venta de productos Beauty, Kawaii, cuidado facial y corporal y Moda SHEIN, con funcionalidades para clientes al detal, clientes mayoristas y ventas realizadas durante lives.

## Estado actual

Proyecto en desarrollo.

### Funcionalidades implementadas hasta el momento

- Estructura base con Django.
- Frontend responsive con HTML y SASS.
- Identidad visual de Pronty Outlet.
- Header con buscador y navegación.
- Barra comercial.
- Home con:
  - hero principal;
  - categorías;
  - próximo live con contador;
  - cómo comprar;
  - redes sociales;
  - contacto;
  - footer.
- Página de catálogo.
- Filtros visuales de productos.
- Tarjetas de productos.
- Página de detalle de producto.
- Sistema de iconos con Lucide y Font Awesome.
- Botón flotante de WhatsApp.

## Funcionalidades planificadas

- Registro e inicio de sesión.
- Clientes al detal y mayoristas.
- Reglas de precios mayoristas.
- Carrito de compras.
- Checkout.
- Pedidos.
- Inventario.
- Proveedores.
- Cupones.
- Comprobantes de pago.
- Reportes de ventas y rentabilidad.
- Exportación a Excel.
- Panel administrativo personalizado.
- Integración futura con pagos electrónicos.
- Sistema Pronty Live.
- QR permanente por prenda o unidad.
- Escaneo de productos durante lives.
- Pedidos Live en tiempo real.
- Activación y reactivación de códigos para lives.
- Reportes individuales por live.
- Control de utilidad por live.
- Devolución automática al inventario de productos vencidos.

## Tecnologías

- Python
- Django
- HTML5
- SASS / SCSS
- JavaScript
- Node.js
- Lucide Icons
- Font Awesome

## Requisitos actuales

- Python 3.10+
- Node.js 20+
- npm

## Instalación local

Crear y activar entorno virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install django pillow python-dotenv
npm install
python manage.py migrate


## Ejecución del proyecto
En una terminal ejecutar SASS:
npm run sass:watch
En una segunda terminal activar el entorno virtual:
python manage.py runserver 

La aplicación estará disponible en:

http://127.0.0.1:8000/

Catálogo:

http://127.0.0.1:8000/productos/

Producto de ejemplo:

http://127.0.0.1:8000/productos/producto-ejemplo/

Panel administrativo:

http://127.0.0.1:8000/admin/
Estructura principal
pronty-outlet/
│
├── accounts/
├── catalog/
├── config/
├── content/
├── static/
│   ├── css/
│   ├── images/
│   ├── js/
│   └── scss/
├── templates/
│   ├── catalog/
│   ├── base.html
│   └── home.html
├── manage.py
├── package.json
├── package-lock.json
├── README.md
└── .gitignore
Reglas comerciales definidas
Compra mínima para activar condición mayorista: $300.000.
Recompra mínima para mantener condición mayorista: $50.000 dentro de 30 días.
Periodo de gracia posterior: 30 días adicionales.
Reactivación en periodo de gracia: compra mínima de $150.000.
Descuento mayorista desde $600.000: 2%.
Descuento mayorista desde $1.000.000: 5%.
Envío gratis desde $1.000.000.
Medios de pago iniciales: Nequi y Llave Bancolombia.
Reserva de pedidos: 3 días calendario.
Cupones: descuento fijo en pesos.
Pronty Live

Pronty Live permitirá administrar ventas durante lives de TikTok, Instagram y Facebook.

Características previstas:

Cada cliente conserva un código o identidad permanente.
Cada live requiere activación o reactivación con abono de $20.000.
El abono se descuenta del pedido del live.
Si el abono no se utiliza dentro de 5 días hábiles, vence y queda a favor de Pronty Outlet.
Si el cliente compra durante el live, tiene 3 días calendario para completar el pago.
Cada prenda o unidad física tendrá un QR único y permanente.
El administrador podrá escanear QR desde un celular.
Cada producto escaneado se asignará en tiempo real a la cuenta del cliente.
El cliente podrá ver en su cuenta los productos asignados durante el live.
Los productos de pedidos vencidos regresarán automáticamente al inventario.
Cada live tendrá su propio reporte.
Los reportes incluirán ventas, costos, utilidad, margen, productos vendidos, códigos activados, pagos pendientes, vencimientos y conversiones.
Estado aproximado del proyecto
Planeación funcional: avanzada.
Identidad visual: avanzada.
Home frontend: avanzado.
Catálogo frontend: en desarrollo.
Ficha de producto: en desarrollo.
Backend comercial: pendiente.
Usuarios y mayoristas: pendiente.
Inventario: pendiente.
Pedidos: pendiente.
Reportes: pendiente.
Pronty Live: definido funcionalmente, pendiente de implementación.
GitHub: configuración inicial.
Autor

Carlos Cifuentes

Marca

Pronty Outlet
Calidad · Tendencia · Precio
