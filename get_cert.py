from django.http import HttpResponse

def get_qz_certificate(request):
    with open('/certs/certificate.pem', 'r') as file:
        return HttpResponse(file.read(), content_type='text/plain')
