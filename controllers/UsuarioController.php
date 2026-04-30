<?php
require_once '../models/Usuario.php';
require_once '../helpers/response.php';
require_once '../middleware/authMiddleware.php';

class UsuarioController {

    private $usuario;

    public function __construct($db) {
        $this->usuario = new Usuario($db);
    }

    public function index() {
        AuthMiddleware::requireAdmin();

        $usuarios = $this->usuario->getAll();
        Response::success($usuarios);
    }

    public function show($id) {
        AuthMiddleware::requireAuth();

        $usuario = $this->usuario->getById($id);

        if (!$usuario) {
            Response::error("Usuario no encontrado", 404);
        }

        Response::success($usuario);
    }

    public function store($data) {
        AuthMiddleware::requireAdmin();

        if (!isset($data['correo'], $data['contraseña'], $data['tipo_usuario'])) {
            Response::error("Datos incompletos");
        }

        $passwordHash = password_hash($data['contraseña'], PASSWORD_DEFAULT);

        $id = $this->usuario->createWithRole([
            "correo" => $data['correo'],
            "password" => $passwordHash,
            "tipo_usuario" => $data['tipo_usuario'],
            "extra" => $data
        ]);

        if (!$id) {
            Response::error("Error al crear usuario");
        }

        Response::success([
            "id_usuario" => $id
        ]);
    }

    public function update($id, $data) {
        AuthMiddleware::requireAdmin();

        $updated = $this->usuario->update($id, $data);

        if (!$updated) {
            Response::error("Error al actualizar");
        }

        Response::success("Usuario actualizado");
    }

    public function destroy($id) {
        AuthMiddleware::requireAdmin();

        $deleted = $this->usuario->deactivate($id);

        if (!$deleted) {
            Response::error("Error al eliminar");
        }

        Response::success("Usuario desactivado");
    }

    public function delete($id) {

        $deleted = $this->usuario->delete($id);

        if (!$deleted) {
            Response::error("Error al eliminar");
        }

        Response::success("Usuario eliminado");
    }
}