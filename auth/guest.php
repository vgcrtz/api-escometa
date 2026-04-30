<?php
header("Content-Type: application/json");

header("Access-Control-Allow-Origin: http://localhost:4200");
header("Access-Control-Allow-Credentials: true");
header("Access-Control-Allow-Headers: Content-Type");
header("Access-Control-Allow-Methods: POST");

$guest_id = "guest_" . bin2hex(random_bytes(8));

$session_data = [
    "id_usuario" => null,
    "guest_id" => $guest_id,
    "tipo_usuario" => "INVITADO"
];

setcookie(
    "session",
    json_encode($session_data),
    [
        'expires' => time() + 3600,
        'path' => '/',
        'httponly' => true,
        'secure' => false,
        'samesite' => 'Lax'
    ]
);

echo json_encode([
    "status" => "success",
    "message" => "Sesión como invitado creada",
    "data" => $session_data
]);