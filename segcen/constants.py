SEND_EMAIL_NOTIFICATION_NEW_USER = '''
Hola {user_fullname}, ha sido registrado como usuario {user_rol} en Hazlo Simple.
A continuación adjuntamos el link del sistema y sus credenciales.

Link: {link_app_hs}
Usuario: {username}
Contraseña: {password}

¡Gracias por usar Iglesia Bautista Misionera de Santa Eulalia!
Saludos
'''

SEND_EMAIL_NOTIFICATION_RESET_PASSWORD_USER = '''
Hola {user_fullname}, ha sido generado una nueva contraseña para Hazlo Simple.
A continuación adjuntamos el link del sistema y sus nuevas credenciales.

Link: {link_app_hs}
Usuario: {username}
Contraseña: {password}

¡Gracias por usar Iglesia Bautista Misionera de Santa Eulalia!
Saludos
'''