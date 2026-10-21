# Pronty Outlet

Plataforma de comercio electrónico desarrollada con Django para **Pronty Outlet**, orientada a la venta de productos de belleza, Kawaii, cuidado facial y corporal, accesorios y Moda SHEIN.

El sistema integra comercio electrónico tradicional, gestión de clientes, inventario, pedidos, ventas mayoristas y un módulo especializado denominado **Pronty Live**, diseñado para administrar ventas realizadas durante transmisiones en vivo.

---

# Estado del proyecto

**Estado actual:** Desarrollo avanzado / etapa de cierre funcional.

Estimación general del proyecto:

- Plataforma funcional: aproximadamente 90 %
- Proyecto completo, documentación y preparación para producción: aproximadamente 80 %

Actualmente la aplicación funciona en entorno local y puede ser utilizada desde otros dispositivos conectados a la misma red local.

La publicación definitiva en Internet todavía requiere configuración de producción, dominio, HTTPS, servidor, base de datos de producción y revisión final de seguridad.

---

# Funcionalidades implementadas

## Tienda pública

La tienda cuenta actualmente con:

- Página de inicio responsive.
- Identidad visual de Pronty Outlet.
- Menú dinámico de categorías.
- Iconos configurables por categoría.
- Categorías destacadas administrables desde Django.
- Buscador de productos.
- Catálogo de productos.
- Filtros por:
  - categoría;
  - marca;
  - precio mínimo;
  - precio máximo;
  - promociones.
- Ordenamiento de productos.
- Página de detalle de producto.
- Imagen principal.
- Galería de imágenes.
- Navegación responsive.
- Menú hamburguesa para dispositivos móviles y tablet.
- Botón flotante de WhatsApp.
- Sección de contacto.
- Modal de correo con apertura automática de Gmail.

---

# Categorías

Las categorías se administran desde Django.

Cada categoría puede definir:

- nombre;
- slug;
- estado activo;
- visualización en el menú;
- orden del menú;
- icono;
- condición de categoría destacada.

La página principal utiliza automáticamente la misma configuración del menú.

---

# Gestión de productos

Los productos cuentan con información como:

- SKU;
- nombre;
- categoría;
- marca;
- descripción;
- descripción corta;
- precio al detal;
- precio mayorista;
- costo;
- inventario;
- imagen principal;
- galería de imágenes;
- estado activo;
- promociones.

---

# Importación masiva de productos

El sistema incluye herramientas administrativas para importar productos mediante archivos:

- Excel;
- CSV.

La importación permite:

- crear productos;
- actualizar productos existentes mediante SKU;
- validar información;
- ajustar inventario;
- generar reportes de resultados.

---

# Importación masiva de imágenes

El administrador puede importar imágenes mediante archivos ZIP.

Convención utilizada:

```text
SKU.jpg
SKU-1.jpg
SKU-2.jpg
SKU-3.jpg
```

Reglas principales:

- `SKU.jpg` puede utilizarse como imagen principal.
- `SKU-1` tiene prioridad como imagen principal.
- `SKU-2`, `SKU-3`, etc. se utilizan como galería.
- Las imágenes se relacionan automáticamente mediante el SKU.
- Los productos inexistentes son omitidos e informados.
- Se realizan validaciones básicas de los archivos de imagen.

---

# Carrito y pedidos

La plataforma cuenta con flujo de compra para clientes.

Incluye:

- carrito de compras;
- cantidades;
- generación de pedidos;
- reserva de inventario;
- seguimiento desde la cuenta del cliente;
- flujo comercial mediante WhatsApp.

Los pagos actualmente se gestionan de forma manual.

Medios inicialmente contemplados:

- Nequi;
- Llave Bancolombia.

---

# Inventario

El inventario se controla mediante movimientos.

El modelo utiliza movimientos de inventario para registrar entradas y salidas y mantener actualizado el stock disponible.

El stock mostrado representa inventario disponible para venta.

Las reservas de productos afectan el inventario disponible.

---

# Clientes

La plataforma incluye:

- registro;
- inicio de sesión;
- cuenta de cliente;
- historial y seguimiento;
- acceso a Pronty Live.

Los usuarios administrativos cuentan con acceso independiente al panel administrativo y al módulo de gestión de Lives.

---

# Venta mayorista

La plataforma contempla reglas comerciales para clientes mayoristas.

Reglas comerciales definidas durante el desarrollo:

- compra de referencia para beneficio mayorista: $300.000;
- envío gratis desde $1.000.000.

Las reglas comerciales definitivas deben ser validadas por Pronty Outlet antes del despliegue en producción.

---

# Pronty Live

Pronty Live es el módulo especializado para administrar ventas durante transmisiones en vivo.

Actualmente permite trabajar con:

- TikTok;
- Instagram;
- Facebook;
- transmisiones multiplataforma.

---

## Sesiones de Live

Cada Live puede registrar:

- nombre;
- plataforma;
- fecha programada;
- fecha real de inicio;
- fecha real de finalización;
- estado;
- observaciones.

Estados disponibles:

```text
Programado
En vivo
Finalizado
Cancelado
```

---

## Live dinámico en el Home

La página principal consulta automáticamente los Lives existentes.

La prioridad es:

1. Live con estado `En vivo`.
2. Próximo Live con estado `Programado`.
3. Mensaje indicando que no existe una transmisión programada.

El Home muestra automáticamente:

- nombre del Live;
- plataforma;
- estado;
- fecha programada;
- contador regresivo.

---

# Clientes de Pronty Live

Cada cliente puede contar con un código permanente.

Ejemplo:

```text
PRY-C000001
```

La participación en Pronty Live puede activarse o reactivarse.

Valor de activación configurado actualmente:

```text
$20.000
```

---

# QR de productos

Los productos pueden contar con un QR permanente para utilización durante transmisiones Live.

El sistema permite:

- generar QR;
- imprimir o visualizar QR;
- escanear QR desde un dispositivo;
- identificar el producto;
- asociarlo a un Live;
- asignarlo a un cliente.

La URL utilizada por los códigos QR puede configurarse mediante variables de entorno.

---

# Asignaciones durante Lives

Durante un Live, el administrador puede:

- seleccionar un cliente;
- escanear un producto;
- asignar unidades;
- registrar precio;
- reservar inventario;
- convertir asignaciones en pedido;
- liberar productos.

Estados de asignación:

```text
Asignado
Convertido en pedido
Liberado
```

---

# Reportes de Pronty Live

Cada sesión de Live cuenta con su propio reporte.

Los reportes incluyen, entre otros:

- ventas;
- costo;
- utilidad bruta;
- margen bruto;
- unidades vendidas;
- pedidos;
- clientes;
- productos;
- asignaciones convertidas;
- asignaciones pendientes;
- asignaciones liberadas.

También existen desgloses por:

- producto;
- cliente.

---

# Ayuda y contenido

La plataforma incluye páginas de:

- Cómo comprar.
- Contáctanos.
- Envíos.
- Cambios y devoluciones.
- Preguntas frecuentes.

---

# Información legal

Actualmente existen páginas base para:

- Términos y condiciones.
- Política de privacidad.
- Tratamiento de datos.
- Política de cookies.

> **Importante:** estos contenidos deben ser revisados y aprobados por Pronty Outlet antes de la publicación definitiva. Si la empresa dispone de documentos legales propios, deberán sustituir o complementar los textos actuales.

---

# Redes sociales

La plataforma contempla integración con:

- Instagram;
- Facebook;
- TikTok;
- WhatsApp.

WhatsApp ya se encuentra conectado.

Los enlaces oficiales de Instagram, Facebook y TikTok están pendientes de confirmación por parte de Pronty Outlet.

---

# Tecnologías

## Backend

- Python 3.10+
- Django 5
- SQLite en desarrollo
- Pillow
- python-dotenv
- QRCode
- openpyxl

## Frontend

- HTML5
- CSS3
- SASS / SCSS
- JavaScript
- Lucide Icons
- Font Awesome

## Herramientas

- Git
- GitHub
- Node.js
- npm
- Visual Studio Code

---

# Requisitos

Se recomienda:

```text
Python 3.10+
Node.js 20+
npm
Git
```

---

# Instalación local

Clonar el repositorio:

```powershell
git clone https://github.com/carloscifuentesingsoft1560-cyber/pronty-outlet.git
```

Entrar al proyecto:

```powershell
cd pronty-outlet
```

Crear entorno virtual:

```powershell
python -m venv venv
```

Activarlo en PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Instalar dependencias de Python:

```powershell
pip install -r requirements.txt
```

Instalar dependencias de Node:

```powershell
npm install
```

Aplicar migraciones:

```powershell
python manage.py migrate
```

Verificar Django:

```powershell
python manage.py check
```

---

# Variables de entorno

El proyecto utiliza un archivo:

```text
.env
```

Este archivo **no debe subirse a GitHub**.

Ejemplo de configuración:

```env
DJANGO_SECRET_KEY=tu-clave-secreta

ALLOWED_HOSTS=127.0.0.1,localhost

QR_BASE_URL=http://127.0.0.1:8000
```

Para utilizar la plataforma desde otro dispositivo de la misma red local puede agregarse la IP local del equipo.

Ejemplo:

```env
ALLOWED_HOSTS=127.0.0.1,localhost,192.168.1.X

QR_BASE_URL=http://192.168.1.X:8000
```

Nunca deben publicarse claves reales dentro del repositorio.

---

# Compilar SASS

Compilación única:

```powershell
npm run sass
```

Modo automático durante desarrollo:

```powershell
npm run sass:watch
```

---

# Ejecutar Django

Uso únicamente desde el computador:

```powershell
python manage.py runserver
```

Para permitir acceso desde otros dispositivos de la red local:

```powershell
python manage.py runserver 0.0.0.0:8000
```

---

# Acceso local

Página principal:

```text
http://127.0.0.1:8000/
```

Productos:

```text
http://127.0.0.1:8000/productos/
```

Administración:

```text
http://127.0.0.1:8000/admin/
```

Pronty Live:

```text
http://127.0.0.1:8000/live/
```

---

# Estructura principal

```text
pronty-outlet/
│
├── accounts/
│
├── cart/
│
├── catalog/
│
├── config/
│
├── content/
│
├── live_sales/
│
├── static/
│   ├── css/
│   ├── images/
│   ├── js/
│   └── scss/
│
├── templates/
│   ├── accounts/
│   ├── catalog/
│   ├── content/
│   ├── live_sales/
│   ├── base.html
│   └── home.html
│
├── media/
│
├── manage.py
├── requirements.txt
├── package.json
├── package-lock.json
├── README.md
├── .env
└── .gitignore
```

El archivo `.env` debe permanecer excluido del repositorio.

---

# Verificación antes de subir cambios

Activar entorno virtual:

```powershell
.\venv\Scripts\Activate.ps1
```

Comprobar Django:

```powershell
python manage.py check
```

Compilar estilos:

```powershell
npm run sass
```

Consultar cambios:

```powershell
git status
```

---

# Pendientes antes de producción

Antes de publicar Pronty Outlet en Internet todavía se recomienda completar:

- validación final de todos los flujos de compra;
- revisión completa de Pronty Live;
- pruebas automáticas principales;
- revisión de seguridad;
- configuración de correo transaccional si se desea envío directo;
- validación de textos legales;
- enlaces oficiales de redes sociales;
- hosting;
- dominio;
- HTTPS;
- base de datos de producción;
- manejo de archivos media;
- copias de seguridad;
- configuración de `DEBUG=False`;
- gestión segura de variables de entorno;
- pruebas desde dispositivos reales.

---

# Documentación pendiente

Para completar formalmente el proyecto se desarrollarán:

- SRS / Especificación de Requisitos de Software.
- Manual de usuario.
- Manual de administrador.
- Manual de instalación.
- Documento de arquitectura.
- Documento de pruebas.
- Guía de despliegue en producción.

---

# Seguridad

Nunca deben almacenarse públicamente:

- contraseñas;
- claves secretas;
- credenciales de correo;
- credenciales de bases de datos;
- tokens;
- contenido real del archivo `.env`.

Toda información sensible debe administrarse mediante variables de entorno.

---

# Estado de la documentación

| Documento | Estado |
|---|---|
| README técnico | Actualizado |
| SRS | Pendiente |
| Manual de usuario | Pendiente |
| Manual de administrador | Pendiente |
| Manual de instalación | Pendiente |
| Arquitectura | Pendiente |
| Pruebas | Pendiente |
| Guía de producción | Pendiente |
| Políticas legales | Borrador sujeto a validación |

---

# Autor del desarrollo

Carlos Cifuentes

---

# Proyecto

**Pronty Outlet**

**Calidad · Tendencia · Precio**
