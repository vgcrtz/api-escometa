<?php
class Mensaje {
    private $conn;
    private $table = "Mensaje";

    public function __construct($db) {
        $this->conn = $db;
    }

    public function getByConversacion($id) {
        $stmt = $this->conn->prepare(
            "SELECT * FROM $this->table WHERE conversacion_id=?"
        );
        $stmt->execute([$id]);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }

    public function create($data) {
        $stmt = $this->conn->prepare(
            "INSERT INTO $this->table (contenido, usuario_id, conversacion_id)
             VALUES (?, ?, ?)"
        );

        return $stmt->execute([
            $data->contenido,
            $data->usuario_id,
            $data->conversacion_id
        ]);
    }
}