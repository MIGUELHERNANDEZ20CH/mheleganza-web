from django.urls import path
from django.http import HttpResponse


inicio = lambda request: HttpResponse("""
<!DOCTYPE html>
<html lang="es">

<head>

    <meta charset="UTF-8">

    <title>Pedidos - MH'Eleganza</title>

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
            max-width: 850px;
            margin: 60px auto;
            padding: 45px;
            background-color: #151a21;
            border: 1px solid #c9a227;
            border-radius: 20px;
        }

        h1 {
            color: #d4af37;
            text-align: center;
            font-size: 40px;
        }

        .pedido {
            margin-top: 30px;
            padding: 25px;
            background-color: #0f1217;
            border-radius: 10px;
        }

        .pedido h3 {
            color: #d4af37;
        }

        .estado {
            color: #d4af37;
        }

        a {
            display: inline-block;
            margin: 8px;
            padding: 12px 22px;
            background-color: #d4af37;
            color: #111111;
            text-decoration: none;
            border-radius: 7px;
            font-weight: bold;
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
        Bienvenido a Pedidos
    </h1>

    <div class="pedido">

        <h3>
            Pedido #001
        </h3>

        <p>
            Cliente: Usuario registrado
        </p>

        <p>
            Producto: Camisa negra
        </p>

        <p>
            Cantidad: 1
        </p>

        <p>
            Total: $80.000
        </p>

        <p class="estado">
            Estado: Pendiente
        </p>

    </div>

    <a href="/pedido/compra/">
        Realizar compra
    </a>

    <a href="/pedido/consultar/">
        Consultar pedidos
    </a>

    <a href="/">
        Inicio
    </a>

</div>

</body>
</html>
""")


compra = lambda request: HttpResponse("""
<!DOCTYPE html>
<html lang="es">

<head>

    <meta charset="UTF-8">

    <title>Realizar Compra</title>

</head>

<body style="
    background-color:#0b0d10;
    color:white;
    text-align:center;
    font-family:Arial;
    padding:80px;
">

<h1 style="color:#d4af37;">
    Realizar Compra
</h1>

<p>
    Confirmación de la compra.
</p>

<p>
    Total: $125.000
</p>

<a href="/pedido/">
    Volver a Pedidos
</a>

</body>

</html>
""")


consultar = lambda request: HttpResponse("""
<!DOCTYPE html>
<html lang="es">

<head>

    <meta charset="UTF-8">

    <title>Consultar Pedidos</title>

</head>

<body style="
    background-color:#0b0d10;
    color:white;
    text-align:center;
    font-family:Arial;
    padding:80px;
">

<h1 style="color:#d4af37;">
    Consultar Pedidos
</h1>

<p>
    Pedido #001 - Pendiente
</p>

<a href="/pedido/">
    Volver a Pedidos
</a>

</body>

</html>
""")


urlpatterns = [

    path("", inicio),

    path("compra/", compra),

    path("consultar/", consultar),

]