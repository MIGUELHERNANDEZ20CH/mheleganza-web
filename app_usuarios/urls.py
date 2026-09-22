from django.urls import path
from django.http import HttpResponse


inicio = lambda request: HttpResponse("""
<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>Usuarios - MH'Eleganza</title>

    <style>

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background-color: #0b0d10;
            color: white;
        }

        header {
            padding: 25px;
            text-align: center;
            background-color: #11151a;
            border-bottom: 2px solid #c9a227;
        }

        .logo {
            color: #d4af37;
            font-size: 30px;
            font-weight: bold;
            letter-spacing: 3px;
        }

        .panel {
            width: 80%;
            max-width: 900px;
            margin: 60px auto;
            padding: 50px;
            text-align: center;
            background-color: #151a21;
            border: 1px solid #c9a227;
            border-radius: 20px;
        }

        h1 {
            color: #d4af37;
            font-size: 40px;
        }

        p {
            color: #bbbbbb;
            font-size: 18px;
        }

        a {
            display: inline-block;
            margin: 8px;
            padding: 13px 22px;
            background-color: #d4af37;
            color: #111111;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
        }

        a:hover {
            background-color: #f0cf55;
        }

    </style>
</head>

<body>

<header>

    <div class="logo">
        MH'ELEGANZA
    </div>

</header>

<div class="panel">

    <h1>
        Bienvenido a Usuarios
    </h1>

    <p>
        Gestión de clientes y administradores.
    </p>

    <a href="/usuarios/registro/">
        Registrar usuario
    </a>

    <a href="/usuarios/login/">
        Iniciar sesión
    </a>

    <a href="/usuarios/recuperar/">
        Recuperar contraseña
    </a>

    <a href="/usuarios/perfil/">
        Datos personales
    </a>

    <br>

    <a href="/">
        Inicio
    </a>

</div>

</body>
</html>
""")


registro = lambda request: HttpResponse("""
<h1>Registrar Usuario</h1>

<p>Formulario para registrar un nuevo usuario.</p>

<a href="/usuarios/">
    Volver a Usuarios
</a>
""")


login = lambda request: HttpResponse("""
<h1>Iniciar Sesión</h1>

<p>Acceso para clientes y administradores.</p>

<a href="/usuarios/">
    Volver a Usuarios
</a>
""")


recuperar = lambda request: HttpResponse("""
<h1>Recuperar Contraseña</h1>

<p>Proceso para recuperar la contraseña.</p>

<a href="/usuarios/">
    Volver a Usuarios
</a>
""")


perfil = lambda request: HttpResponse("""
<h1>Datos Personales</h1>

<p>Consulta y actualización de los datos personales.</p>

<a href="/usuarios/">
    Volver a Usuarios
</a>
""")


urlpatterns = [

    path("", inicio),

    path("registro/", registro),

    path("login/", login),

    path("recuperar/", recuperar),

    path("perfil/", perfil),

]