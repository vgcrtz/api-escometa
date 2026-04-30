<?php
class Usuario {
    private $conn;
    private $table = "Usuario";

    public function __construct($db) {
        $this->conn = $db;
    }

    public function findByCorreo($correo) {
        $query = "SELECT * FROM " . $this->table . " WHERE correo = :correo LIMIT 1";
        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(":correo", $correo);
        $stmt->execute();

        return $stmt->fetch(PDO::FETCH_ASSOC);
    }

    public function create($correo, $passwordHash, $tipo_usuario) {
        $query = "INSERT INTO " . $this->table . " (correo, contraseña, tipo_usuario)
                  VALUES (:correo, :password, :tipo_usuario)";

        if ($tipo_usuario === 'ADMIN') {
            return false;
        }

        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(":correo", $correo);
        $stmt->bindParam(":password", $passwordHash);
        $stmt->bindParam(":tipo_usuario", $tipo_usuario);

        if ($stmt->execute()) {
            return $this->conn->lastInsertId();
        }

        return false;
    }

    public function createAlumno($id_usuario, $boleta, $carrera, $semestre) {
        $query = "INSERT INTO Alumno (id_usuario, boleta, carrera, semestre)
                  VALUES (:id, :boleta, :carrera, :semestre)";

        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(":id", $id_usuario);
        $stmt->bindParam(":boleta", $boleta);
        $stmt->bindParam(":carrera", $carrera);
        $stmt->bindParam(":semestre", $semestre);

        return $stmt->execute();
    }
    public function createDocente($id_usuario, $grado, $departamento) {
        $query = "INSERT INTO Docente (id_usuario, grado_academico, departamento)
                  VALUES (:id, :grado, :depto)";

        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(":id", $id_usuario);
        $stmt->bindParam(":grado", $grado);
        $stmt->bindParam(":depto", $departamento);

        return $stmt->execute();
    }

    public function createAdministrativo($id_usuario, $area, $puesto) {
        $query = "INSERT INTO Administrativo (id_usuario, area, puesto)
                  VALUES (:id, :area, :puesto)";

        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(":id", $id_usuario);
        $stmt->bindParam(":area", $area);
        $stmt->bindParam(":puesto", $puesto);

        return $stmt->execute();
    }

    public function createWithRole($data) {
        try {
            $this->conn->beginTransaction();

            $id = $this->create(
                $data['correo'],
                $data['password'],
                $data['tipo_usuario']
            );

            if (!$id) throw new Exception("Error creando usuario");

            switch ($data['tipo_usuario']) {
                case 'ALUMNO':
                    $this->createAlumno($id, $data['boleta'], $data['carrera'], $data['semestre']);
                    break;

                case 'DOCENTE':
                    $this->createDocente($id, $data['grado'], $data['departamento']);
                    break;

                case 'ADMINISTRATIVO':
                    $this->createAdministrativo($id, $data['area'], $data['puesto']);
                    break;
            }

            $this->conn->commit();
            return $id;

        } catch (Exception $e) {
            $this->conn->rollBack();
            return false;
        }
    }

    public function verifyPassword($inputPassword, $hashedPassword) {
        return password_verify($inputPassword, $hashedPassword);
    }

    public function getAll() {
        $stmt = $this->conn->prepare("SELECT id_usuario, correo, tipo_usuario FROM Usuario WHERE activo = TRUE");
        $stmt->execute();
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }

    public function getById($id) {
        $stmt = $this->conn->prepare("SELECT * FROM Usuario WHERE id_usuario = :id");
        $stmt->bindParam(":id", $id);
        $stmt->execute();
        return $stmt->fetch(PDO::FETCH_ASSOC);
    }

    public function delete($id) {
        $stmt = $this->conn->prepare("DELETE FROM Usuario WHERE id_usuario = :id");
        $stmt->bindParam(":id", $id);
        return $stmt->execute();
    }

    public function activate($id) {
        $query = "UPDATE Usuario 
              SET activo = TRUE
              WHERE id_usuario = :id";

        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(":id", $id);

        return $stmt->execute();
    }

    public function deactivate($id) {
        $query = "UPDATE Usuario 
              SET activo = FALSE
              WHERE id_usuario = :id";

        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(":id", $id);

        return $stmt->execute();
    }

    public function verificarUsuario($id) {
        $query = "UPDATE Usuario SET verificado = TRUE WHERE id_usuario = :id";
        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(":id", $id);
        return $stmt->execute();
    }

    public function update($id, $data) {
        $query = "UPDATE Usuario SET correo = :correo WHERE id_usuario = :id";
        $stmt = $this->conn->prepare($query);

        $stmt->bindParam(":correo", $data['correo']);
        $stmt->bindParam(":id", $id);

        return $stmt->execute();
    }

}

?>