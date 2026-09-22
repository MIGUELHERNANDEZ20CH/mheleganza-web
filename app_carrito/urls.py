from django.urls import path
from django.http import HttpResponse


inicio = lambda request: HttpResponse("""
<!DOCTYPE html>
<html lang="es">

<head>

    <meta charset="UTF-8">

    <title>Carrito - MH'Eleganza</title>

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
        }

        .producto {
            padding: 20px;
            margin: 15px 0;
            background-color: #0f1217;
            border-radius: 10px;
        }

        .producto h3 {
            color: #d4af37;
        }

        .total {
            text-align: right;
            color: #d4af37;
            font-size: 24px;
            margin-top: 30px;
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
        Bienvenido al Carrito
    </h1>

    <div class="producto">

        <h3>
            Camisa negra
        </h3>

        <p>
            Cantidad: 1
        </p>

        <p>
            Precio: $80.000
        </p>

    </div>

    <div class="producto">

        <h3>
            Gorra azul
        </h3>

        <p>
            Cantidad: 1
        </p>

        <p>
            Precio: $45.000
        </p>

    </div>

    <div class="total">
        Total: $125.000
    </div>

    <a href="/pedido/">
        Continuar compra
    </a>

    <a href="/">
        Inicio
    </a>

</div>

</body>
</html>
""")


urlpatterns = [

    path("", inicio),

]