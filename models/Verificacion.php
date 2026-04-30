<?php
class Verificacion {
    private $conn;

    public function __construct($db) {
        $this->conn = $db;
    }

    public function crearCodigo($id_usuario, $codigo) {
        $query = "INSERT INTO VerificacionCorreo 
                  (id_usuario, codigo, expiracion) 
                  VALUES (:id, :codigo, DATE_ADD(NOW(), INTERVAL 10 MINUTE))";

        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(":id", $id_usuario);
        $stmt->bindParam(":codigo", $codigo);

        return $stmt->execute();
    }

    public function verificarCodigo($id_usuario, $codigo) {
        $query = "SELECT * FROM VerificacionCorreo 
                  WHERE id_usuario = :id 
                  AND codigo = :codigo 
                  AND usado = FALSE 
                  AND expiracion > NOW()
                  LIMIT 1";

        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(":id", $id_usuario);
        $stmt->bindParam(":codigo", $codigo);
        $stmt->execute();

        return $stmt->fetch(PDO::FETCH_ASSOC);
    }

    public function marcarUsado($id) {
        $query = "UPDATE VerificacionCorreo SET usado = TRUE WHERE id = :id";
        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(":id", $id);
        return $stmt->execute();
    }
}