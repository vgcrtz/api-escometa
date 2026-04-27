<?php
if(!isset($_COOKIE['user_id'])) {
    http_response_code(401);
    echo json_encode(["error" => "No autorizado"]);
    exit();
}
?>