from django.urls import path, include
from django.http import HttpResponse


inicio = lambda request: HttpResponse("""
<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>MH'Eleganza</title>

    <style>

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background-color: #0b0d10;
            color: white;
        }

        header {
            background-color: #11151a;
            padding: 25px;
            text-align: center;
            border-bottom: 2px solid #c9a227;
        }

        .logo {
            color: #d4af37;
            font-size: 32px;
            font-weight: bold;
            letter-spacing: 3px;
        }

        nav {
            margin-top: 20px;
        }

        nav a {
            color: white;
            text-decoration: none;
            margin: 5px;
            padding: 10px 15px;
            border-radius: 6px;
        }

        nav a:hover {
            background-color: #d4af37;
            color: #111111;
        }

        .principal {
            width: 85%;
            max-width: 1000px;
            margin: 70px auto;
            padding: 60px 30px;
            text-align: center;
            background-color: #151a21;
            border: 1px solid #c9a227;
            border-radius: 20px;
        }

        h1 {
            color: #d4af37;
            font-size: 45px;
        }

        h2 {
            color: #cccccc;
            font-weight: normal;
        }

        p {
            color: #bbbbbb;
            font-size: 18px;
            line-height: 1.6;
        }

        .boton {
            display: inline-block;
            margin: 10px;
            padding: 14px 25px;
            background-color: #d4af37;
            color: #111111;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
        }

        .boton:hover {
            background-color: #f0cf55;
        }

        footer {
            text-align: center;
            padding: 25px;
            color: #777777;
        }

    </style>
</head>

<body>

<header>

    <div class="logo">
        MH'ELEGANZA
    </div>

    <nav>

        <a href="/usuarios/">
            Usuarios
        </a>

        <a href="/productos/">
            Productos
        </a>

        <a href="/inventario/">
            Inventario
        </a>

        <a href="/carrito/">
            Carrito
        </a>

        <a href="/pedido/">
            Pedidos
        </a>

    </nav>

</header>

<div class="principal">

    <h1>
        Bienvenido a MH'Eleganza
    </h1>

    <h2>
        Moda, elegancia y estilo
    </h2>

    <p>
        Sistema web para la gestión de usuarios,
        productos, inventario, carrito de compras
        y pedidos.
    </p>

    <a class="boton" href="/productos/">
        Ver productos
    </a>

    <a class="boton" href="/usuarios/">
        Usuarios
    </a>

</div>

<footer>
    MH'Eleganza © 2026
</footer>

</body>
</html>
""")


urlpatterns = [

    path("", inicio),

    path(
        "usuarios/",
        include("app_usuarios.urls")
    ),

    path(
        "productos/",
        include("app_productos.urls")
    ),

    path(
        "inventario/",
        include("app_inventario.urls")
    ),

    path(
        "carrito/",
        include("app_carrito.urls")
    ),

    path(
        "pedido/",
        include("app_pedido.urls")
    ),

]