<?php
use PHPMailer\PHPMailer\PHPMailer;

require '../vendor/autoload.php';

function enviarCodigo($correo, $codigo) {
    $mail = new PHPMailer(true);

    $mail->isSMTP();
    $mail->Host = 'smtp.gmail.com';
    $mail->SMTPAuth = true;
    $mail->Username = '*';
    $mail->Password = '*';
    $mail->SMTPSecure = 'tls';
    $mail->Port = 587;

    $mail->setFrom('*', 'Sistema');
    $mail->addAddress($correo);

    $mail->Subject = 'Verificación de cuenta';
    $mail->Body = "Tu código es: $codigo";

    try {
        $mail->send();
        echo "Correo enviado correctamente";
    } catch (Exception $e) {
        echo "Error al enviar correo: " . $mail->ErrorInfo;
    }
}