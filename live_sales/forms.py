from django import forms

from .models import LiveSession


# ============================================================
# FORMULARIO DE LIVE
# ============================================================

class LiveSessionForm(forms.ModelForm):

    class Meta:

        model = LiveSession

        fields = (
            'name',
            'platform',
            'scheduled_at',
            'notes',
        )

        widgets = {

            'name': forms.TextInput(
                attrs={
                    'class': 'live-admin-form__input',
                    'placeholder': (
                        'Ej. Live Moda SHEIN viernes'
                    ),
                    'autocomplete': 'off',
                }
            ),

            'platform': forms.Select(
                attrs={
                    'class': 'live-admin-form__input',
                }
            ),

            'scheduled_at': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={
                    'class': 'live-admin-form__input',
                    'type': 'datetime-local',
                }
            ),

            'notes': forms.Textarea(
                attrs={
                    'class': 'live-admin-form__input',
                    'rows': 5,
                    'placeholder': (
                        'Observaciones internas del Live'
                    ),
                }
            ),
        }


    def __init__(
        self,
        *args,
        **kwargs
    ):

        super().__init__(
            *args,
            **kwargs
        )


        scheduled_at_field = (
            self.fields.get(
                'scheduled_at'
            )
        )


        if isinstance(
            scheduled_at_field,
            forms.DateTimeField
        ):

            scheduled_at_field.input_formats = [
                '%Y-%m-%dT%H:%M',
            ]