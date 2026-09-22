from django.urls import path
from django.http import HttpResponse


inicio = lambda request: HttpResponse("""
<!DOCTYPE html>
<html lang="es">

<head>

    <meta charset="UTF-8">

    <title>Productos - MH'Eleganza</title>

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
            max-width: 1000px;
            margin: 50px auto;
            padding: 45px;
            text-align: center;
        }

        h1 {
            color: #d4af37;
            font-size: 40px;
        }

        p {
            color: #bbbbbb;
        }

        .productos {
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
            margin-top: 35px;
        }

        .producto {
            width: 190px;
            padding: 25px;
            background-color: #151a21;
            border: 1px solid #333333;
            border-radius: 15px;
        }

        .producto h3 {
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
        Bienvenido a Productos
    </h1>

    <p>
        Catálogo de productos de MH'Eleganza.
    </p>

    <div class="productos">

        <div class="producto">
            <h3>Camisas</h3>
            <p>Prendas elegantes.</p>
        </div>

        <div class="producto">
            <h3>Pantalones</h3>
            <p>Estilo y comodidad.</p>
        </div>

        <div class="producto">
            <h3>Gorras</h3>
            <p>Accesorios modernos.</p>
        </div>

        <div class="producto">
            <h3>Accesorios</h3>
            <p>Complementa tu estilo.</p>
        </div>

    </div>

    <br>

    <a href="/productos/catalogo/">
        Catálogo
    </a>

    <a href="/productos/filtros/">
        Filtrar productos
    </a>

    <a href="/productos/detalle/">
        Detalles
    </a>

    <a href="/">
        Inicio
    </a>

</div>

</body>
</html>
""")


catalogo = lambda request: HttpResponse("""
<h1>Catálogo de Productos</h1>

<p>Aquí aparecerán los productos disponibles.</p>

<a href="/productos/">
    Volver a Productos
</a>
""")


filtros = lambda request: HttpResponse("""
<h1>Filtrar Productos</h1>

<p>
Filtros por categoría, talla, color y precio.
</p>

<a href="/productos/">
    Volver a Productos
</a>
""")


detalle = lambda request: HttpResponse("""
<h1>Detalle del Producto</h1>

<p>
Aquí aparecerá la información detallada del producto.
</p>

<a href="/productos/">
    Volver a Productos
</a>
""")


urlpatterns = [

    path("", inicio),

    path("catalogo/", catalogo),

    path("filtros/", filtros),

    path("detalle/", detalle),

]