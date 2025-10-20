from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from email.mime.image import MIMEImage


class EmailService:
    @staticmethod
    def get_connection(provider='brevo'):
        config = settings.EMAIL_CONFIGS[provider]
        return get_connection(
            host=config['EMAIL_HOST'],
            port=config['EMAIL_PORT'],
            username=config['EMAIL_HOST_USER'],
            password=config['EMAIL_HOST_PASSWORD'],
            use_tls=config['EMAIL_USE_TLS']
        )

    @staticmethod
    def render_template(template_name, context):
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)  # Para clientes que no soportan HTML
        return html_content, text_content

    @staticmethod
    def attach_cid_images(email, images: dict):
        """
        images = {
            'banner_cid': banner_bytes,
            'qr_cid': qr_bytes,
            'icon_wapp_cid': icon_bytes
        }
        """
        for cid, image_bytes in images.items():
            if image_bytes:
                img = MIMEImage(image_bytes if isinstance(image_bytes, bytes) else image_bytes.getvalue())
                img.add_header('Content-ID', f'<{cid}>')
                img.add_header('Content-Disposition', 'inline')
                email.attach(img)

    @staticmethod
    def enviar_email(provider, header, subject, template_name, context, recipients, images=None):
        connection = EmailService.get_connection(provider)
        html_content, text_content = EmailService.render_template(template_name, context)

        from_email = f'{header} <{settings.EMAIL_CONFIGS[provider]['DEFAULT_FROM_EMAIL']}>'
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipients,
            connection=connection
        )
        email.attach_alternative(html_content, 'text/html')

        if images:
            EmailService.attach_cid_images(email, images)

        try:
            email.send(fail_silently=False)
            return True
        except Exception as e:
            raise e  # Esto será capturado por la APIView