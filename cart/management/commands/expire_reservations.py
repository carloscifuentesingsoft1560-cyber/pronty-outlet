from django.core.management.base import BaseCommand

from cart.reservation_services import (
    expire_due_reservations,
)


class Command(BaseCommand):

    help = (
        'Libera las reservas de inventario '
        'que ya superaron su fecha límite.'
    )

    def handle(
        self,
        *args,
        **options
    ):

        self.stdout.write(
            'Buscando reservas vencidas...'
        )

        expired_count = (
            expire_due_reservations()
        )

        if expired_count == 0:

            self.stdout.write(
                self.style.WARNING(
                    'No se encontraron reservas '
                    'vencidas para liberar.'
                )
            )

            return

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f'Se liberaron correctamente '
                    f'{expired_count} reserva(s) vencida(s).'
                )
            )
        )