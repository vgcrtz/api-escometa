<?php
require_once '../config/database.php';
require_once '../models/Usuario.php';

header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Credentials: true");
header("Access-Control-Allow-Headers: Content-Type");
header("Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS");

$db = (new Database())->connect();
$usuario = new Usuario($db);

$data = json_decode(file_get_contents("php://input"));

switch($_SERVER['REQUEST_METHOD']) {

    case 'GET':
        if(isset($_GET['id'])) {
            echo json_encode($usuario->getById($_GET['id']));
        } else {
            echo json_encode($usuario->getAll()->fetchAll(PDO::FETCH_ASSOC));
        }
        break;

    case 'POST':
        $usuario->create($data);
        echo json_encode(["mensaje" => "Usuario creado"]);
        break;

    case 'PUT':
        parse_str($_SERVER['QUERY_STRING'], $params);
        $usuario->update($params['id'], $data);
        echo json_encode(["mensaje" => "Usuario actualizado"]);
        break;

    case 'DELETE':
        parse_str($_SERVER['QUERY_STRING'], $params);
        $usuario->delete($params['id']);
        echo json_encode(["mensaje" => "Usuario eliminado"]);
        break;
}