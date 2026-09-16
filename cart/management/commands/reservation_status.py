from django.core.management.base import BaseCommand
from django.utils import timezone

from cart.models import Order


class Command(BaseCommand):

    help = (
        'Muestra un resumen del estado actual '
        'de las reservas de inventario.'
    )

    def handle(
        self,
        *args,
        **options
    ):

        now = timezone.now()

        active = (
            Order.objects
            .filter(
                inventory_reservation_status=(
                    Order.ReservationStatus.ACTIVE
                )
            )
            .count()
        )

        expired_active = (
            Order.objects
            .filter(
                inventory_reservation_status=(
                    Order.ReservationStatus.ACTIVE
                ),
                reservation_expires_at__isnull=False,
                reservation_expires_at__lte=now,
            )
            .count()
        )

        finalized = (
            Order.objects
            .filter(
                inventory_reservation_status=(
                    Order.ReservationStatus.FINALIZED
                )
            )
            .count()
        )

        released = (
            Order.objects
            .filter(
                inventory_reservation_status=(
                    Order.ReservationStatus.RELEASED
                )
            )
            .count()
        )

        not_applicable = (
            Order.objects
            .filter(
                inventory_reservation_status=(
                    Order.ReservationStatus.NOT_APPLICABLE
                )
            )
            .count()
        )

        self.stdout.write(
            ''
        )

        self.stdout.write(
            self.style.SUCCESS(
                'ESTADO DE RESERVAS PRONTY'
            )
        )

        self.stdout.write(
            '---------------------------'
        )

        self.stdout.write(
            f'Reservas activas: {active}'
        )

        self.stdout.write(
            f'Activas pero vencidas: {expired_active}'
        )

        self.stdout.write(
            f'Convertidas en venta: {finalized}'
        )

        self.stdout.write(
            f'Liberadas: {released}'
        )

        self.stdout.write(
            f'Pedidos antiguos / no aplica: {not_applicable}'
        )

        self.stdout.write(
            ''
        )
        