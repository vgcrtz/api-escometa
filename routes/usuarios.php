<?php

require_once '../config/database.php';
require_once '../controllers/UsuarioController.php';

header("Content-Type: application/json");

$db = (new Database())->connect();
$controller = new UsuarioController($db);

$method = $_SERVER['REQUEST_METHOD'];

$id = $_GET['id'] ?? null;

$data = json_decode(file_get_contents("php://input"), true);

switch ($method) {
    case 'GET':
        if ($id) {
            $controller->show($id);
        } else {
            $controller->index();
        }
        break;

    case 'POST':
        $controller->store($data);
        break;

    case 'PUT':
        if (!$id) {
            Response::error("ID requerido", 400);
        }
        $controller->update($id, $data);
        break;

    case 'DELETE':
        if (!$id) {
            Response::error("ID requerido", 400);
        }

        if (isset($_GET['force']) && $_GET['force'] == 'true') {
            $controller->delete($id);
        } else {
            $controller->destroy($id);
        }
        break;

    default:
        Response::error("Método no permitido", 405);
        break;
}