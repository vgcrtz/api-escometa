<?php
header("Content-Type: application/json");
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Credentials: true");

$request = $_SERVER['REQUEST_URI'];
$method = $_SERVER['REQUEST_METHOD'];

if (strpos($request, '/usuarios') !== false) {
    require_once './controllers/usuario.php';
} elseif (strpos($request, '/grupos') !== false) {
    require_once './controllers/grupo.php';
} elseif (strpos($request, '/mensajes') !== false) {
    require_once './controllers/mensaje.php';
} elseif (strpos($request, '/auth') !== false) {
    require_once './controllers/auth.php';
} else {
    echo json_encode(["error" => "Ruta no encontrada"]);
}

?>