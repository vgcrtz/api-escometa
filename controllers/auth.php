<?php
require_once '../config/db.php';
require_once '../models/Usuario.php';

$db = (new Database())->connect();
$usuario = new Usuario($db);

$data = json_decode(file_get_contents("php://input"));

switch($_SERVER['REQUEST_METHOD']) {

    case 'POST':
        $user = $usuario->findByCorreo($data->correo);

        if($user && password_verify($data->password, $user['password'])) {

            setcookie("user_id", $user['id'], [
                'expires' => time() + 3600,
                'path' => '/',
                'secure' => false,
                'httponly' => true,
                'samesite' => 'Lax'
            ]);

            echo json_encode(["mensaje" => "Login exitoso"]);
        } else {
            echo json_encode(["error" => "Credenciales incorrectas"]);
        }
        break;

    case 'GET':
        if(isset($_COOKIE['user_id'])) {
            echo json_encode([
                "autenticado" => true,
                "user_id" => $_COOKIE['user_id']
            ]);
        } else {
            echo json_encode(["autenticado" => false]);
        }
        break;

    case 'DELETE':
        setcookie("user_id", "", time() - 3600, "/");
        echo json_encode(["mensaje" => "Logout exitoso"]);
        break;
}