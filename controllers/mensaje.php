<?php
require_once '../config/database.php';
require_once '../models/Mensaje.php';
require_once '../middleware/auth.php';

$db = (new Database())->connect();
$mensaje = new Mensaje($db);

$data = json_decode(file_get_contents("php://input"));

switch($_SERVER['REQUEST_METHOD']) {

    case 'GET':
        if(isset($_GET['id_conversacion'])) {
            echo json_encode(
                $mensaje->getByConversacion($_GET['id_conversacion'])
            );
        }
        break;

    case 'POST':
        $mensaje->create($data);
        echo json_encode(["mensaje" => "Mensaje enviado"]);
        break;

}