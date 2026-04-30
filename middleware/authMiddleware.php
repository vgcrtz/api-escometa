<?php

class AuthMiddleware {
    public static function getSession() {
        if (!isset($_COOKIE['session'])) {
            return null;
        }

        $session = json_decode($_COOKIE['session'], true);

        if (!$session) {
            return null;
        }

        return $session;
    }

    public static function requireAuth() {
        $session = self::getSession();

        if (!$session) {
            http_response_code(401);
            echo json_encode([
                "status" => "error",
                "message" => "No autenticado"
            ]);
            exit;
        }

        return $session;
    }

    public static function requireUser() {
        $session = self::requireAuth();

        if ($session['tipo_usuario'] === 'INVITADO') {
            http_response_code(403);
            echo json_encode([
                "status" => "error",
                "message" => "Acceso solo para usuarios registrados"
            ]);
            exit;
        }

        return $session;
    }

    public static function requireGuest() {
        $session = self::requireAuth();

        if ($session['tipo_usuario'] !== 'INVITADO') {
            http_response_code(403);
            echo json_encode([
                "status" => "error",
                "message" => "Acceso solo para invitados"
            ]);
            exit;
        }

        return $session;
    }

    public static function requireRole($roles = []) {
        $session = self::requireUser();

        if (!in_array($session['tipo_usuario'], $roles)) {
            http_response_code(403);
            echo json_encode([
                "status" => "error",
                "message" => "No tienes permisos para esta acción"
            ]);
            exit;
        }

        return $session;
    }

    public static function requireAdmin() {
        $session = self::requireUser();

        if ($session['tipo_usuario'] !== 'ADMIN') {
            http_response_code(403);
            echo json_encode([
                "status" => "error",
                "message" => "Acceso solo para administradores"
            ]);
            exit;
        }

        return $session;
    }

    public static function optionalAuth() {
        return self::getSession(); // puede ser null
    }

    public static function getUserId() {
        $session = self::requireUser();
        return $session['id_usuario'];
    }

    public static function getGuestId() {
        $session = self::requireGuest();
        return $session['guest_id'];
    }

    public static function requireOwnership($resourceUserId) {
        $session = self::requireUser();

        if ($session['id_usuario'] != $resourceUserId) {
            http_response_code(403);
            echo json_encode([
                "status" => "error",
                "message" => "No tienes acceso a este recurso"
            ]);
            exit;
        }

        return $session;
    }
}