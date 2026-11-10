from django.urls import path
from django.urls import reverse_lazy
from . import views
from . import views_auth
from django.contrib.auth import views as auth_views

password_reset_view = auth_views.PasswordResetView.as_view(
    template_name='app_usuarios/password_reset_form.html',
    email_template_name='app_usuarios/password_reset_email.txt',
    html_email_template_name='app_usuarios/password_reset_email.html',
    subject_template_name='app_usuarios/password_reset_subject.txt',
    success_url=reverse_lazy('password_reset_done'),
)

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('recuperar/telefono/', views_auth.request_phone_reset, name='request_phone_reset'),
    path('recuperar/telefono/verificar/', views_auth.verify_phone_code, name='verify_phone_code'),
    path('recuperar/telefono/nueva-contrasena/', views_auth.set_new_password, name='set_new_password'),
    path('password-reset/', password_reset_view, name='password_reset'),
    path('recuperar/', password_reset_view, name='recuperar_contrasena'),
    path(
        'password-reset/enviado/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='app_usuarios/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'password-reset/confirmar/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='app_usuarios/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'password-reset/completado/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='app_usuarios/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
    path('perfil/', views.perfil_datos_view, name='perfil_datos'),
    path('perfil/actualizar/', views.actualizar_perfil_view, name='actualizar_perfil'),
    path('perfil/direccion/', views.actualizar_direccion_view, name='actualizar_direccion'),
    path('perfil/contrasena/', views.actualizar_contrasena_view, name='actualizar_contrasena'),
    path('logout/', views.cerrar_sesion_view, name='cerrar_sesion'), # Función extra de cierre de sesión
]