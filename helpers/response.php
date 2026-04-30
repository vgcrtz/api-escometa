<?php

class Response {
    public static function success($data = null) {
        echo json_encode([
            "status" => "success",
            "data" => $data
        ]);
        exit;
    }

    public static function error($message, $code = 400) {
        http_response_code($code);
        echo json_encode([
            "status" => "error",
            "message" => $message
        ]);
        exit;
    }
}

?>