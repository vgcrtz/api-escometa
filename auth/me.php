<?php
require_once '../middleware/authMiddleware.php';

header("Content-Type: application/json");
header("Access-Control-Allow-Origin: http://localhost:4200");
header("Access-Control-Allow-Credentials: true");

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    http_response_code(405);
    echo json_encode([
        "status" => "error",
        "message" => "Método no permitido"
    ]);
    exit;
}

$session = AuthMiddleware::optionalAuth();

if (!$session) {
    echo json_encode([
        "status" => "success",
        "authenticated" => false,
        "data" => null
    ]);
    exit;
}

if ($session['tipo_usuario'] === 'INVITADO') {
    echo json_encode([
        "status" => "success",
        "authenticated" => true,
        "isGuest" => true,
        "data" => [
            "guest_id" => $session['guest_id'],
            "tipo_usuario" => "INVITADO"
        ]
    ]);
    exit;
}

echo json_encode([
    "status" => "success",
    "authenticated" => true,
    "isGuest" => false,
    "data" => [
        "id_usuario" => $session['id_usuario'],
        "correo" => $session['correo'],
        "tipo_usuario" => $session['tipo_usuario']
    ]
]);