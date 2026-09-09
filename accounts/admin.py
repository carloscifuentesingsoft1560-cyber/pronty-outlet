from django.contrib import admin

from .models import CustomerProfile


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):

    list_display = (
        'customer_name',
        'customer_email',
        'commercial_status',
        'has_wholesale_prices_display',
        'wholesale_activated_at',
        'maintenance_deadline',
        'grace_deadline',
    )

    list_filter = (
        'commercial_status',
        'wholesale_activated_at',
        'maintenance_deadline',
        'grace_deadline',
    )

    search_fields = (
        'user__first_name',
        'user__last_name',
        'user__email',
        'user__username',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    fieldsets = (
        (
            'Cliente',
            {
                'fields': (
                    'user',
                    'commercial_status',
                )
            }
        ),
        (
            'Mayorista',
            {
                'fields': (
                    'wholesale_activated_at',
                    'maintenance_deadline',
                    'last_wholesale_purchase_at',
                    'last_wholesale_purchase_total',
                )
            }
        ),
        (
            'Período de gracia',
            {
                'fields': (
                    'grace_started_at',
                    'grace_deadline',
                )
            }
        ),
        (
            'Auditoría',
            {
                'fields': (
                    'created_at',
                    'updated_at',
                )
            }
        ),
    )

    ordering = (
        'user__first_name',
        'user__last_name',
    )

    @admin.display(
        description='Cliente'
    )
    def customer_name(self, obj):

        full_name = obj.user.get_full_name().strip()

        return (
            full_name
            or obj.user.username
        )

    @admin.display(
        description='Correo'
    )
    def customer_email(self, obj):

        return obj.user.email

    @admin.display(
        boolean=True,
        description='Precio mayorista'
    )
    def has_wholesale_prices_display(self, obj):

        return obj.has_wholesale_prices