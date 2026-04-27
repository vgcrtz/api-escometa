<?php
class Database {
    private $host = "localhost";
    private $db_name = "escometa";
    private $username = "root";
    private $password = "n0m3l0";

    public function connect() {
        $conn = null;

        try {
            $conn = new PDO(
                "mysql:host=$this->host;dbname=$this->db_name",
                $this->username,
                $this->password
            );
            $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        } catch(PDOException $e) {
            echo json_encode(["error" => $e->getMessage()]);
        }

        return $conn;
    }
}