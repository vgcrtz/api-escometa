<?php
require_once '../middleware/authMiddleware.php';

header("Content-Type: application/json");

header("Access-Control-Allow-Origin: http://localhost:4200");
header("Access-Control-Allow-Credentials: true");
header("Access-Control-Allow-Methods: POST");

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode([
        "status" => "error",
        "message" => "Método no permitido"
    ]);
    exit;
}

$session = AuthMiddleware::optionalAuth();

setcookie(
    "session",
    "",
    [
        'expires' => time() - 3600,
        'path' => '/',
        'httponly' => true,
        'secure' => false, // true en producción
        'samesite' => 'Lax'
    ]
);

unset($_COOKIE['session']);

echo json_encode([
    "status" => "success",
    "message" => "Sesión cerrada correctamente"
]);