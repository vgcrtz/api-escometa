<?php
require_once '../config/database.php';
require_once '../models/Grupo.php';
require_once '../middleware/auth.php';

$db = (new Database())->connect();
$grupo = new Grupo($db);

$data = json_decode(file_get_contents("php://input"));

switch($_SERVER['REQUEST_METHOD']) {

    case 'GET':
        if(isset($_GET['id'])) {
            echo json_encode($grupo->getUsuarios($_GET['id']));
        } else {
            echo json_encode($grupo->getAll());
        }
        break;

    case 'POST':
        if(isset($_GET['action']) && $_GET['action'] === 'addUser') {
            $grupo->addUsuario($data->grupo_id, $data->usuario_id);
            echo json_encode(["mensaje" => "Usuario agregado al grupo"]);
        } else {
            $grupo->create($data);
            echo json_encode(["mensaje" => "Grupo creado"]);
        }
        break;

    case 'PUT':
        parse_str($_SERVER['QUERY_STRING'], $params);
        $grupo->update($params['id'], $data);
        echo json_encode(["mensaje" => "Grupo actualizado"]);
        break;

    case 'DELETE':
        parse_str($_SERVER['QUERY_STRING'], $params);
        $grupo->delete($params['id']);
        echo json_encode(["mensaje" => "Grupo eliminado"]);
        break;
}