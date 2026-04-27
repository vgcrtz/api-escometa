<?php
class Grupo {
    private $conn;
    private $table = "GrupoAcademico";

    public function __construct($db) {
        $this->conn = $db;
    }

    public function getAll() {
        $stmt = $this->conn->query("SELECT * FROM $this->table");
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }

    public function create($data) {
        $stmt = $this->conn->prepare(
            "INSERT INTO $this->table (nombre) VALUES (?)"
        );
        return $stmt->execute([$data->nombre]);
    }

    public function addUsuario($grupo_id, $usuario_id) {
        $stmt = $this->conn->prepare(
            "INSERT INTO Usuario_Grupo (grupo_id, usuario_id)
             VALUES (?, ?)"
        );
        return $stmt->execute([$grupo_id, $usuario_id]);
    }

    public function getUsuarios($grupo_id) {
        $stmt = $this->conn->prepare(
            "SELECT u.* FROM Usuario u
             JOIN Usuario_Grupo gu ON u.id = gu.usuario_id
             WHERE gu.grupo_id=?"
        );
        $stmt->execute([$grupo_id]);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }
}