# Manual de Administrador — Pronty Outlet

## 1. Objetivo
Describir las principales tareas administrativas de la plataforma.

## 2. Acceso
Los usuarios autorizados pueden ingresar al panel administrativo de Django y al módulo administrativo de Pronty Live.

## 3. Categorías
El administrador puede gestionar:
- nombre;
- slug;
- estado;
- orden;
- icono;
- aparición en menú;
- destacado.

## 4. Productos
El administrador puede:
- crear productos;
- editar productos;
- cambiar precios;
- actualizar inventario;
- gestionar imágenes;
- activar o desactivar productos.

## 5. Importación masiva
Se puede utilizar importación mediante:
- Excel;
- CSV.

Los productos pueden relacionarse mediante SKU.

## 6. Importación de imágenes
Se puede cargar un ZIP utilizando nombres basados en SKU.

Ejemplo:

```text
SKU.jpg
SKU-1.jpg
SKU-2.jpg
```

## 7. Inventario
Los movimientos deben utilizarse para mantener trazabilidad.

Evita modificar stock sin seguir el flujo definido por el sistema cuando exista una operación específica para ello.

## 8. Pedidos
El administrador debe revisar:
- cliente;
- productos;
- cantidades;
- estado;
- disponibilidad;
- confirmación comercial.

## 9. Pronty Live
El módulo permite:
- crear Live;
- programarlo;
- iniciarlo;
- finalizarlo;
- seleccionar plataforma;
- gestionar clientes;
- asignar productos;
- convertir asignaciones;
- liberar asignaciones;
- consultar reportes.

## 10. QR
Los QR se utilizan para identificar productos durante el Live.

La variable `QR_BASE_URL` debe apuntar a una URL accesible por el dispositivo que escanea.

## 11. Reportes
Los reportes Live incluyen indicadores comerciales como:
- ventas;
- costos;
- utilidad;
- margen;
- unidades;
- productos;
- clientes;
- pedidos;
- asignaciones.

## 12. Contenido público
Las páginas de ayuda y legales pueden requerir actualización si el negocio modifica sus políticas.

## 13. Seguridad
Nunca publiques:
- `.env`;
- contraseñas;
- tokens;
- claves secretas;
- credenciales de correo;
- credenciales de base de datos.