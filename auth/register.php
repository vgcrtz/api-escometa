<?php
require_once '../config/database.php';
require_once '../models/Usuario.php';
require_once '../utils/email.php';
require_once '../models/Verificacion.php';

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

if (
    !isset($data['correo']) ||
    !isset($data['contraseña']) ||
    !isset($data['tipo_usuario'])
) {
    http_response_code(400);
    echo json_encode(["status" => "error", "message" => "Datos incompletos"]);
    exit;
}

$correo = $data['correo'];
$password = $data['contraseña'];
$tipo = $data['tipo_usuario'];

if ($tipo === 'ADMIN') {
    echo json_encode([
        "status" => "error",
        "message" => "No puedes registrarte como administrador"
    ]);
    exit;
}

try {
    $db = new Database();
    $conn = $db->connect();

    $usuarioModel = new Usuario($conn);

    $dominiosPermitidos = ['ipn.mx', 'alumno.ipn.mx', 'egresado.ipn.mx'];

    $dominio = substr(strrchr($correo, "@"), 1);

    if (!in_array($dominio, $dominiosPermitidos)) {
        http_response_code(400);
        echo json_encode([
            "status" => "error",
            "message" => "Dominio de correo no permitido"
        ]);
        exit;
    }

    if ($usuarioModel->findByCorreo($correo)) {
        http_response_code(409);
        echo json_encode(["status" => "error", "message" => "El correo ya está registrado"]);
        exit;
    }

    $passwordHash = password_hash($password, PASSWORD_DEFAULT);

    $conn->beginTransaction();

    $id_usuario = $usuarioModel->create($correo, $passwordHash, $tipo);

    if (!$id_usuario) {
        throw new Exception("Error al crear usuario");
    }

    switch ($tipo) {
        case "ALUMNO":
            $usuarioModel->createAlumno(
                $id_usuario,
                $data['boleta'] ?? null,
                $data['carrera'] ?? null,
                $data['semestre'] ?? null
            );
            break;

        case "DOCENTE":
            $usuarioModel->createDocente(
                $id_usuario,
                $data['grado_academico'] ?? null,
                $data['departamento'] ?? null
            );
            break;

        case "ADMINISTRATIVO":
            $usuarioModel->createAdministrativo(
                $id_usuario,
                $data['area'] ?? null,
                $data['puesto'] ?? null
            );
            break;

        default:
            throw new Exception("Tipo de usuario inválido");
    }

    $conn->commit();

    $session_data = [
        "id_usuario" => $id_usuario,
        "correo" => $correo,
        "tipo_usuario" => $tipo
    ];

    setcookie(
        "session",
        json_encode($session_data),
        [
            'expires' => time() + 86400,
            'path' => '/',
            'httponly' => true,
            'secure' => false,
            'samesite' => 'Lax'
        ]
    );

    echo json_encode([
        "status" => "success",
        "message" => "Usuario registrado correctamente",
        "data" => $session_data
    ]);

} catch (Exception $e) {
    if ($conn->inTransaction()) {
        $conn->rollBack();
    }

    http_response_code(500);
    echo json_encode([
        "status" => "error",
        "message" => "Error al registrar",
        "debug" => $e->getMessage()
    ]);
//
//    $codigo = rand(100000, 999999);
//
//    $verificacion = new Verificacion($db);
//    $verificacion->crearCodigo($id_usuario, $codigo);
//
//    enviarCodigo($data['correo'], $codigo);
//
//    echo json_encode([
//        "status" => "success",
//        "message" => "Usuario creado, verifica tu correo"]);
}