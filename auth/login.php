<?php
require_once '../config/database.php';
require_once '../models/Usuario.php';

header("Content-Type: application/json");

header("Access-Control-Allow-Origin: http://localhost:4200");
header("Access-Control-Allow-Credentials: true");
header("Access-Control-Allow-Headers: Content-Type");
header("Access-Control-Allow-Methods: POST");

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(["status" => "error", "message" => "Método no permitido"]);
    exit;
}

$data = json_decode(file_get_contents("php://input"), true);

if (!isset($data['correo']) || !isset($data['contraseña'])) {
    http_response_code(400);
    echo json_encode(["status" => "error", "message" => "Datos incompletos"]);
    exit;
}

$correo = $data['correo'];
$password = $data['contraseña'];

try {
    $db = new Database();
    $conn = $db->connect();

    $usuarioModel = new Usuario($conn);

    $usuario = $usuarioModel->findByCorreo($correo);

    if (!$usuario) {
        http_response_code(401);
        echo json_encode([
            "status" => "error",
            "message" => "Usuario no encontrado"
        ]);
        exit;
    }

    if (!$usuario['activo']) {
        http_response_code(403);
        echo json_encode([
            "status" => "error",
            "message" => "Usuario desactivado"
        ]);
        exit;
    }

    if (!$usuarioModel->verifyPassword($password, $usuario['contraseña'])) {
        http_response_code(401);
        echo json_encode(["status" => "error", "message" => "Credenciales inválidas"]);
        exit;
    }

    $session_data = [
        "id_usuario" => $usuario['id_usuario'],
        "correo" => $usuario['correo'],
        "tipo_usuario" => $usuario['tipo_usuario']
    ];

    setcookie(
        "session",
        json_encode($session_data),
        [
            'expires' => time() + 86400,
            'path' => '/',
            'httponly' => true,
            'secure' => false, // true en producción
            'samesite' => 'Lax'
        ]
    );

    echo json_encode([
        "status" => "success",
        "message" => "Login exitoso",
        "data" => $session_data
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        "status" => "error",
        "message" => "Error del servidor",
        "debug" => $e->getMessage()
    ]);
}

?>