# SRS — Pronty Outlet

## 1. Introducción

### 1.1 Propósito
Este documento define los requisitos funcionales y no funcionales de **Pronty Outlet**, una plataforma de comercio electrónico desarrollada con Django para la venta de productos al detal y al por mayor, con soporte para catálogo, clientes, carrito, pedidos, inventario y el módulo especializado **Pronty Live**.

### 1.2 Alcance
El sistema permite:

- publicar y administrar productos;
- organizar productos por categorías y marcas;
- registrar clientes;
- gestionar compras al detal y mayoristas;
- manejar carrito y pedidos;
- controlar inventario y reservas;
- administrar sesiones de Pronty Live;
- generar y utilizar códigos QR;
- asignar productos a clientes durante Lives;
- convertir asignaciones en pedidos;
- consultar reportes de Lives;
- mostrar contenido de ayuda, contacto y páginas legales;
- integrar WhatsApp y redes sociales.

### 1.3 Usuarios del sistema
- Visitante.
- Cliente registrado.
- Cliente mayorista.
- Cliente participante de Pronty Live.
- Administrador.
- Usuario staff.

---

## 2. Descripción general

### 2.1 Producto
Pronty Outlet es una aplicación web responsive desarrollada con Django.

### 2.2 Entorno actual
- Python 3.10+
- Django 5
- SQLite en desarrollo
- HTML5
- SCSS / CSS
- JavaScript
- Node.js / npm
- Pillow
- python-dotenv
- qrcode
- openpyxl

### 2.3 Restricciones actuales
- Los pagos se confirman de forma manual.
- El correo de contacto abre Gmail desde el navegador.
- La aplicación aún no está desplegada en producción.
- Los textos legales están sujetos a validación del negocio.

---

## 3. Requisitos funcionales

### RF-01. Página de inicio
El sistema deberá mostrar una página de inicio con:
- hero comercial;
- categorías;
- próximo Live o Live activo;
- proceso de compra;
- redes sociales;
- contacto;
- footer.

### RF-02. Categorías
El administrador deberá poder:
- crear categorías;
- activar o desactivar categorías;
- definir orden;
- definir icono;
- definir si aparece en menú;
- destacar categorías.

### RF-03. Catálogo
El usuario deberá poder:
- listar productos;
- buscar productos;
- filtrar por categoría;
- filtrar por marca;
- filtrar por precio;
- visualizar promociones;
- ordenar resultados.

### RF-04. Producto
El sistema deberá mostrar:
- nombre;
- SKU;
- descripción;
- precio;
- precio mayorista cuando aplique;
- stock;
- imagen principal;
- galería.

### RF-05. Importación masiva
El administrador deberá poder importar productos mediante Excel o CSV.

### RF-06. Imágenes masivas
El administrador deberá poder importar imágenes por archivo ZIP relacionándolas mediante SKU.

### RF-07. Registro e inicio de sesión
El sistema deberá permitir:
- registro de clientes;
- inicio de sesión;
- cierre de sesión;
- acceso a cuenta personal.

### RF-08. Carrito
El cliente deberá poder:
- agregar productos;
- modificar cantidades;
- retirar productos;
- consultar subtotal.

### RF-09. Pedidos
El sistema deberá permitir:
- generar pedidos;
- reservar inventario;
- consultar pedidos desde la cuenta;
- continuar la gestión comercial por WhatsApp.

### RF-10. Inventario
El sistema deberá controlar entradas, salidas y reservas mediante movimientos de inventario.

### RF-11. Mayoristas
El sistema deberá contemplar reglas comerciales mayoristas configuradas por el negocio.

### RF-12. Pronty Live
El administrador deberá poder:
- crear Lives;
- programar fecha y hora;
- seleccionar plataforma;
- cambiar estado;
- iniciar y finalizar un Live.

### RF-13. Estados de Live
Los estados disponibles deberán incluir:
- Programado.
- En vivo.
- Finalizado.
- Cancelado.

### RF-14. Live en Home
El Home deberá mostrar:
1. Live activo;
2. próximo Live programado;
3. mensaje neutral si no existe Live.

### RF-15. Clientes Live
El sistema deberá poder identificar clientes de Pronty Live mediante código permanente.

### RF-16. Activación Live
El sistema deberá permitir registrar activación o reactivación del cliente para participar.

### RF-17. QR
El sistema deberá permitir generar y utilizar códigos QR permanentes asociados a productos.

### RF-18. Asignaciones Live
Durante un Live se deberá poder:
- seleccionar cliente;
- escanear producto;
- asignar producto;
- registrar cantidad;
- registrar precio;
- reservar inventario.

### RF-19. Estados de asignación
Las asignaciones deberán soportar:
- Asignado.
- Convertido en pedido.
- Liberado.

### RF-20. Conversión a pedido
El sistema deberá permitir convertir asignaciones Live en pedidos.

### RF-21. Liberación
El sistema deberá permitir liberar productos y devolver disponibilidad al inventario cuando corresponda.

### RF-22. Reportes Live
El sistema deberá mostrar reportes con:
- ventas;
- costos;
- utilidad;
- margen;
- unidades;
- pedidos;
- clientes;
- productos;
- asignaciones.

### RF-23. Ayuda
El sistema deberá disponer de páginas para:
- Cómo comprar.
- Contacto.
- Envíos.
- Cambios y devoluciones.
- Preguntas frecuentes.

### RF-24. Información legal
El sistema deberá disponer de páginas para:
- Términos y condiciones.
- Política de privacidad.
- Tratamiento de datos.
- Política de cookies.

### RF-25. Redes sociales
El sistema deberá enlazar:
- Instagram;
- Facebook;
- TikTok;
- WhatsApp.

---

## 4. Requisitos no funcionales

### RNF-01. Responsive
La interfaz deberá adaptarse a computador, tablet y móvil.

### RNF-02. Seguridad
Las claves, secretos y credenciales deberán manejarse mediante variables de entorno.

### RNF-03. Mantenibilidad
El código deberá organizarse en aplicaciones Django independientes por dominio funcional.

### RNF-04. Usabilidad
Las principales acciones deberán ser visibles y comprensibles para usuarios no técnicos.

### RNF-05. Integridad
Los cambios de inventario deberán conservar trazabilidad mediante movimientos.

### RNF-06. Compatibilidad
La aplicación deberá funcionar en navegadores modernos.

### RNF-07. Accesibilidad básica
Los enlaces, botones e imágenes relevantes deberán contar con textos o etiquetas accesibles cuando corresponda.

### RNF-08. Rendimiento
Las páginas principales deberán cargar de forma adecuada bajo condiciones normales de uso.

### RNF-09. Respaldo
En producción deberá existir una estrategia de copias de seguridad.

### RNF-10. Producción
El despliegue deberá utilizar HTTPS, `DEBUG=False` y configuración segura.

---

## 5. Reglas comerciales conocidas

- Beneficio mayorista de referencia desde $300.000.
- Envío gratis de referencia desde $1.000.000.
- Activación Pronty Live configurada actualmente en $20.000.
- Pagos iniciales: Nequi y Llave Bancolombia.
- Las reglas definitivas deben ser validadas por Pronty Outlet antes de producción.

---

## 6. Integraciones actuales

- WhatsApp.
- Instagram.
- Facebook.
- TikTok.
- Gmail mediante apertura de composición desde navegador.

---

## 7. Pendientes antes de producción

- validación integral del flujo de compra;
- validación integral de Pronty Live;
- pruebas automáticas;
- revisión de seguridad;
- despliegue;
- dominio;
- HTTPS;
- base de datos de producción;
- estrategia de backups;
- validación de textos legales;
- configuración opcional de correo transaccional.

---

## 8. Estado del documento

Versión inicial basada en el estado funcional actual del proyecto.

**Proyecto:** Pronty Outlet  
**Autor del desarrollo:** Carlos Cifuentes