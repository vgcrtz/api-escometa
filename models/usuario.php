<?php
class Usuario {
    private $conn;
    private $table = "Usuario";

    public function __construct($db) {
        $this->conn = $db;
    }

    public function getAll() {
        $stmt = $this->conn->prepare("SELECT * FROM $this->table");
        $stmt->execute();
        return $stmt;
    }

    public function getById($id) {
        $stmt = $this->conn->prepare("SELECT * FROM $this->table WHERE id=?");
        $stmt->execute([$id]);
        return $stmt->fetch(PDO::FETCH_ASSOC);
    }

    public function create($data) {
        $stmt = $this->conn->prepare(
            "INSERT INTO $this->table (nombre, correo, password)
             VALUES (?, ?, ?)"
        );

        return $stmt->execute([
            $data->nombre,
            $data->correo,
            password_hash($data->password, PASSWORD_BCRYPT)
        ]);
    }

    public function update($id, $data) {
        $stmt = $this->conn->prepare(
            "UPDATE $this->table SET nombre=?, correo=? WHERE id=?"
        );

        return $stmt->execute([
            $data->nombre,
            $data->correo,
            $id
        ]);
    }

    public function delete($id) {
        $stmt = $this->conn->prepare(
            "DELETE FROM $this->table WHERE id=?"
        );
        return $stmt->execute([$id]);
    }

    public function findByCorreo($correo) {
        $stmt = $this->conn->prepare(
            "SELECT * FROM $this->table WHERE correo=?"
        );
        $stmt->execute([$correo]);
        return $stmt->fetch(PDO::FETCH_ASSOC);
    }
}