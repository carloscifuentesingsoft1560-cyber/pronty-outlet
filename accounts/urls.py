from django.contrib.auth import views as auth_views
from django.urls import path

from accounts import views


app_name = 'accounts'


urlpatterns = [
    path(
        '',
        views.account_dashboard,
        name='dashboard'
    ),

    path(
        'pedido/<str:order_number>/',
        views.order_detail,
        name='order_detail'
    ),

    path(
        'ingresar/',
        views.account_login,
        name='login'
    ),

    path(
        'registro/',
        views.account_register,
        name='register'
    ),

    path(
        'salir/',
        views.account_logout,
        name='logout'
    ),

    # ========================================================
    # RECUPERACIÓN DE CONTRASEÑA
    # ========================================================

    path(
        'recuperar-contrasena/',
        auth_views.PasswordResetView.as_view(
            template_name=(
                'accounts/password_reset_form.html'
            ),
            email_template_name=(
                'accounts/password_reset_email.html'
            ),
            subject_template_name=(
                'accounts/password_reset_subject.txt'
            ),
            success_url=(
                '/cuenta/recuperar-contrasena/enviado/'
            ),
        ),
        name='password_reset'
    ),

    path(
        'recuperar-contrasena/enviado/',
        auth_views.PasswordResetDoneView.as_view(
            template_name=(
                'accounts/password_reset_done.html'
            )
        ),
        name='password_reset_done'
    ),

    path(
        'restablecer/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name=(
                'accounts/password_reset_confirm.html'
            ),
            success_url=(
                '/cuenta/restablecer/completado/'
            ),
        ),
        name='password_reset_confirm'
    ),

    path(
        'restablecer/completado/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name=(
                'accounts/password_reset_complete.html'
            )
        ),
        name='password_reset_complete'
    ),
]