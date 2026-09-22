from django.urls import path
from django.http import HttpResponse


inicio = lambda request: HttpResponse("""
<!DOCTYPE html>
<html lang="es">

<head>

    <meta charset="UTF-8">

    <title>Inventario - MH'Eleganza</title>

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
            width: 85%;
            max-width: 950px;
            margin: 60px auto;
            padding: 45px;
            background-color: #151a21;
            border: 1px solid #c9a227;
            border-radius: 20px;
            text-align: center;
        }

        h1 {
            color: #d4af37;
            font-size: 40px;
        }

        p {
            color: #bbbbbb;
        }

        table {
            width: 100%;
            margin-top: 30px;
            border-collapse: collapse;
        }

        th {
            color: #d4af37;
        }

        th,
        td {
            padding: 15px;
            border-bottom: 1px solid #333333;
        }

        td {
            color: #cccccc;
        }

        a {
            display: inline-block;
            margin-top: 25px;
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
        Bienvenido al Inventario
    </h1>

    <p>
        Control de existencias de MH'Eleganza.
    </p>

    <table>

        <tr>
            <th>Producto</th>
            <th>Stock</th>
            <th>Estado</th>
        </tr>

        <tr>
            <td>Camisa negra</td>
            <td>10</td>
            <td>Disponible</td>
        </tr>

        <tr>
            <td>Gorra azul</td>
            <td>8</td>
            <td>Disponible</td>
        </tr>

        <tr>
            <td>Pantalón negro</td>
            <td>3</td>
            <td>Bajo stock</td>
        </tr>

    </table>

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