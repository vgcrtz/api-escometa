<?php
require_once '../models/Usuario.php';
require_once '../models/Verificacion.php';
require_once '../config/database.php';

$db = (new Database())->connect();

$usuarioModel = new Usuario($db);
$verificacionModel = new Verificacion($db);

$data = json_decode(file_get_contents("php://input"), true);

$user = $usuarioModel->findByCorreo($data['correo']);

if (!$user) {
    echo json_encode(["error" => "Usuario no encontrado"]);
    exit;
}

$registro = $verificacionModel->verificarCodigo(
    $user['id_usuario'],
    $data['codigo']
);

if (!$registro) {
    echo json_encode(["error" => "Código inválido o expirado"]);
    exit;
}

$verificacionModel->marcarUsado($registro['id']);

$usuarioModel->verificarUsuario($user['id_usuario']);

echo json_encode([
    "status" => "success",
    "message" => "Cuenta verificada"
]);
?>