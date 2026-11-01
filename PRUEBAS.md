# Plan de Pruebas — Pronty Outlet

## 1. Objetivo
Validar que los principales flujos funcionen antes de producción.

## 2. Pruebas de Home
- Carga correctamente.
- Categorías visibles.
- Categorías respetan orden.
- Live activo aparece.
- Próximo Live aparece.
- Contador funciona.
- Redes sociales abren.
- WhatsApp funciona.
- Modal de correo abre Gmail.

## 3. Catálogo
- Búsqueda.
- Filtro por categoría.
- Filtro por marca.
- Precio mínimo.
- Precio máximo.
- Promociones.
- Ordenamiento.
- Producto sin stock.

## 4. Registro y autenticación
- Registro correcto.
- Login correcto.
- Logout correcto.
- Acceso denegado cuando corresponde.
- Staff redirigido al área administrativa.

## 5. Carrito
- Agregar producto.
- Modificar cantidad.
- Eliminar producto.
- Evitar cantidad superior al stock.
- Persistencia esperada.

## 6. Pedidos
- Crear pedido.
- Reservar inventario.
- Consultar pedido.
- Confirmar que el stock cambia correctamente.

## 7. Importación
- Archivo válido.
- SKU existente.
- SKU nuevo.
- Datos inválidos.
- Archivo vacío.
- ZIP de imágenes.
- Imagen principal.
- Galería.

## 8. Pronty Live
- Crear Live.
- Programar Live.
- Iniciar Live.
- Finalizar Live.
- Cancelar Live.
- Seleccionar cliente.
- Escanear QR.
- Asignar producto.
- Validar inventario.
- Convertir asignación.
- Liberar asignación.
- Revisar reporte.

## 9. Responsive
Probar al menos:
- escritorio;
- tablet;
- móvil.

## 10. Seguridad
- `.env` no está versionado.
- páginas privadas requieren login.
- páginas staff no permiten clientes.
- `DEBUG=False` en producción.
- secretos no aparecen en GitHub.

## 11. Comandos de cierre

```powershell
python manage.py check
npm run sass
git status
```

## 12. Criterio de aprobación
El sistema puede considerarse candidato a producción cuando:
- los flujos críticos pasan;
- no hay errores de Django;
- no hay pérdida de inventario;
- no existen secretos publicados;
- se valida la configuración de producción.