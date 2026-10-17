from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import (
    LiveAssignment,
    LiveCustomerAccess,
    LiveProductQR,
    LiveSession,
    LiveSessionProduct,
)

from .services import (
    convert_live_assignments_to_order,
    release_live_assignment,
    reserve_new_live_assignment,
)


# ============================================================
# FORMULARIO DE ASIGNACIÓN
# ============================================================

class LiveAssignmentAdminForm(forms.ModelForm):

    class Meta:

        model = LiveAssignment

        fields = (
            'live_session',
            'customer',
            'product',
            'quantity',
        )


    def clean(self):

        cleaned_data = super().clean()

        live_session = cleaned_data.get(
            'live_session'
        )

        customer = cleaned_data.get(
            'customer'
        )

        product = cleaned_data.get(
            'product'
        )

        quantity = cleaned_data.get(
            'quantity'
        )


        # ====================================================
        # CLIENTE ACTIVADO
        # ====================================================

        if (
            customer
            and not customer.is_activated
        ):

            raise ValidationError(
                (
                    'El cliente no tiene activado '
                    'Pronty Live.'
                )
            )


        # ====================================================
        # LIVE VÁLIDO
        # ====================================================

        if (
            live_session
            and live_session.status
            == LiveSession.Status.CANCELED
        ):

            raise ValidationError(
                (
                    'No se pueden realizar asignaciones '
                    'en un Live cancelado.'
                )
            )


        # ====================================================
        # PRODUCTO HABILITADO
        # ====================================================

        if (
            live_session
            and product
        ):

            live_product = (
                LiveSessionProduct.objects
                .filter(
                    live_session=live_session,
                    product=product,
                    is_active=True,
                )
                .first()
            )


            if not live_product:

                raise ValidationError(
                    (
                        'Este producto no está habilitado '
                        'para el Live seleccionado.'
                    )
                )


        # ====================================================
        # CANTIDAD
        # ====================================================

        if (
            quantity is not None
            and quantity <= 0
        ):

            raise ValidationError(
                (
                    'La cantidad debe ser '
                    'mayor que cero.'
                )
            )


        # ====================================================
        # STOCK PRELIMINAR
        # ====================================================

        if (
            product
            and quantity
            and quantity > product.stock
        ):

            raise ValidationError(
                (
                    f'No hay existencias suficientes. '
                    f'Disponibles actualmente: '
                    f'{product.stock}.'
                )
            )


        return cleaned_data


# ============================================================
# ACCESO DE CLIENTES A PRONTY LIVE
# ============================================================

@admin.register(LiveCustomerAccess)
class LiveCustomerAccessAdmin(admin.ModelAdmin):

    list_display = (
        'customer_code',
        'user',
        'is_activated',
        'activation_amount',
        'activated_at',
        'created_at',
    )

    list_filter = (
        'is_activated',
        'created_at',
    )

    search_fields = (
        'customer_code',
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
    )

    readonly_fields = (
        'customer_code',
        'created_at',
        'updated_at',
    )

    ordering = (
        'customer_code',
    )


# ============================================================
# SESIONES DE LIVE
# ============================================================

@admin.register(LiveSession)
class LiveSessionAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'platform',
        'status',
        'scheduled_at',
        'started_at',
        'ended_at',
        'created_by',
    )

    list_filter = (
        'platform',
        'status',
        'scheduled_at',
    )

    search_fields = (
        'name',
        'notes',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    ordering = (
        '-scheduled_at',
        '-created_at',
    )


# ============================================================
# QR DE PRODUCTOS
# ============================================================

@admin.register(LiveProductQR)
class LiveProductQRAdmin(admin.ModelAdmin):

    list_display = (
        'product',
        'code',
        'is_active',
        'created_at',
    )

    list_filter = (
        'is_active',
        'created_at',
    )

    search_fields = (
        'product__name',
        'product__sku',
    )

    readonly_fields = (
        'code',
        'created_at',
        'updated_at',
    )

    ordering = (
        'product__name',
    )


# ============================================================
# PRODUCTOS HABILITADOS EN CADA LIVE
# ============================================================

@admin.register(LiveSessionProduct)
class LiveSessionProductAdmin(admin.ModelAdmin):

    list_display = (
        'live_session',
        'product',
        'live_price',
        'is_active',
        'effective_price_display',
    )

    list_filter = (
        'is_active',
        'live_session',
    )

    search_fields = (
        'live_session__name',
        'product__name',
        'product__sku',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    ordering = (
        'live_session',
        'product__name',
    )


    @admin.display(
        description='Precio efectivo'
    )
    def effective_price_display(
        self,
        obj
    ):

        if not obj:
            return '-'

        return obj.effective_price


# ============================================================
# ASIGNACIONES DE LIVE
# ============================================================

@admin.register(LiveAssignment)
class LiveAssignmentAdmin(admin.ModelAdmin):

    form = LiveAssignmentAdminForm


    # ========================================================
    # LISTADO
    # ========================================================

    list_display = (
        'id',
        'live_session',
        'customer',
        'product',
        'quantity',
        'unit_price',
        'subtotal_display',
        'status',
        'order_display',
        'assigned_at',
    )

    list_filter = (
        'status',
        'live_session',
        'assigned_at',
    )

    search_fields = (
        'live_session__name',
        'customer__customer_code',
        'customer__user__username',
        'customer__user__first_name',
        'customer__user__last_name',
        'customer__user__email',
        'product__name',
        'product__sku',
        'order__order_number',
    )

    ordering = (
        '-assigned_at',
        '-id',
    )


    # ========================================================
    # ACCIONES
    # ========================================================

    actions = (
        'convert_selected_assignments_to_order',
        'release_selected_assignments',
    )


    # ========================================================
    # CAMPOS DE SOLO LECTURA
    # ========================================================

    readonly_fields = (
        'live_session',
        'customer',
        'product',
        'quantity',
        'unit_price',
        'unit_cost',
        'status',
        'order',
        'assigned_at',
        'released_at',
        'created_by',
        'updated_at',
        'subtotal_display',
        'total_cost_display',
        'gross_profit_display',
        'gross_margin_percentage_display',
    )


    # ========================================================
    # ORGANIZACIÓN DEL FORMULARIO
    # ========================================================

    fieldsets = (
        (
            'Asignación',
            {
                'fields': (
                    'live_session',
                    'customer',
                    'product',
                    'quantity',
                    'status',
                    'order',
                )
            }
        ),
        (
            'Valores',
            {
                'fields': (
                    'unit_price',
                    'unit_cost',
                    'subtotal_display',
                    'total_cost_display',
                    'gross_profit_display',
                    'gross_margin_percentage_display',
                )
            }
        ),
        (
            'Auditoría',
            {
                'fields': (
                    'created_by',
                    'assigned_at',
                    'released_at',
                    'updated_at',
                )
            }
        ),
    )


    # ========================================================
    # CAMPOS EDITABLES SOLO AL CREAR
    # ========================================================

    def get_readonly_fields(
        self,
        request,
        obj=None
    ):

        if obj is None:

            return (
                'unit_price',
                'unit_cost',
                'status',
                'order',
                'assigned_at',
                'released_at',
                'created_by',
                'updated_at',
                'subtotal_display',
                'total_cost_display',
                'gross_profit_display',
                'gross_margin_percentage_display',
            )


        return self.readonly_fields


    # ========================================================
    # GUARDAR NUEVA ASIGNACIÓN
    # ========================================================

    def save_model(
        self,
        request,
        obj,
        form,
        change
    ):

        if not change:

            reserve_new_live_assignment(
                obj,
                created_by=request.user,
            )

            return


        super().save_model(
            request,
            obj,
            form,
            change
        )


    # ========================================================
    # CONVERTIR SELECCIONADAS EN PEDIDO
    # ========================================================

    @admin.action(
        description=(
            'Convertir asignaciones seleccionadas en pedido'
        )
    )
    def convert_selected_assignments_to_order(
        self,
        request,
        queryset
    ):

        assignment_ids = list(
            queryset.values_list(
                'id',
                flat=True
            )
        )


        if not assignment_ids:

            self.message_user(
                request,
                (
                    'No seleccionaste ninguna '
                    'asignación.'
                ),
                level=messages.WARNING,
            )

            return


        try:

            order = (
                convert_live_assignments_to_order(
                    assignment_ids,
                    created_by=request.user,
                )
            )


        except ValidationError as error:

            if hasattr(
                error,
                'messages'
            ):

                error_message = ' '.join(
                    error.messages
                )

            else:

                error_message = str(
                    error
                )


            self.message_user(
                request,
                error_message,
                level=messages.ERROR,
            )

            return


        except Exception as error:

            self.message_user(
                request,
                (
                    'No fue posible generar el pedido. '
                    f'Detalle: {error}'
                ),
                level=messages.ERROR,
            )

            return


        self.message_user(
            request,
            (
                'Pedido creado correctamente desde '
                f'Pronty Live: {order.order_number}. '
                f'Total: ${order.total:,.2f}.'
            ),
            level=messages.SUCCESS,
        )


    # ========================================================
    # LIBERAR ASIGNACIONES
    # ========================================================

    @admin.action(
        description=(
            'Liberar asignaciones seleccionadas'
        )
    )
    def release_selected_assignments(
        self,
        request,
        queryset
    ):

        released_count = 0

        failed_messages = []


        for assignment in queryset:

            (
                success,
                message
            ) = release_live_assignment(
                assignment,
                released_by=request.user,
            )


            if success:

                released_count += 1

            else:

                failed_messages.append(
                    (
                        f'Asignación '
                        f'#{assignment.pk}: '
                        f'{message}'
                    )
                )


        if released_count:

            self.message_user(
                request,
                (
                    f'Se liberaron correctamente '
                    f'{released_count} asignación(es).'
                ),
                level=messages.SUCCESS,
            )


        for message in failed_messages:

            self.message_user(
                request,
                message,
                level=messages.WARNING,
            )


    # ========================================================
    # PEDIDO ASOCIADO
    # ========================================================

    @admin.display(
        description='Pedido'
    )
    def order_display(
        self,
        obj
    ):

        if not obj:
            return '-'


        try:
            order = obj.order

        except Exception:
            order = None


        if not order:
            return '-'


        return order.order_number


    # ========================================================
    # SUBTOTAL
    # ========================================================

    @admin.display(
        description='Subtotal'
    )
    def subtotal_display(
        self,
        obj
    ):

        if not obj:
            return '-'

        return obj.subtotal


    # ========================================================
    # COSTO TOTAL
    # ========================================================

    @admin.display(
        description='Costo total'
    )
    def total_cost_display(
        self,
        obj
    ):

        if not obj:
            return '-'

        return obj.total_cost


    # ========================================================
    # UTILIDAD BRUTA
    # ========================================================

    @admin.display(
        description='Utilidad bruta'
    )
    def gross_profit_display(
        self,
        obj
    ):

        if not obj:
            return '-'

        return obj.gross_profit


    # ========================================================
    # MARGEN BRUTO
    # ========================================================

    @admin.display(
        description='Margen bruto %'
    )
    def gross_margin_percentage_display(
        self,
        obj
    ):

        if not obj:
            return '-'


        return (
            f'{obj.gross_margin_percentage:.2f}%'
        )