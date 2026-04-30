<?php
require_once '../config/database.php';
require_once '../models/Usuario.php';
require_once '../models/Verificacion.php';
require_once '../helpers/response.php';
require_once '../utils/email.php';

header("Content-Type: application/json");

$db = (new Database())->connect();

$usuarioModel = new Usuario($db);
$verificacionModel = new Verificacion($db);

$data = json_decode(file_get_contents("php://input"), true);

if (!isset($data['correo'])) {
    Response::error("Correo requerido");
}

$user = $usuarioModel->findByCorreo($data['correo']);

if (!$user) {
    Response::error("Usuario no encontrado");
}

if ($user['verificado']) {
    Response::error("El usuario ya está verificado");
}

$query = "UPDATE VerificacionCorreo 
          SET usado = TRUE 
          WHERE id_usuario = :id";

$stmt = $db->prepare($query);
$stmt->bindParam(":id", $user['id_usuario']);
$stmt->execute();

$codigo = rand(100000, 999999);

$verificacionModel->crearCodigo($user['id_usuario'], $codigo);

enviarCodigo($user['correo'], $codigo);

Response::success("Código reenviado");