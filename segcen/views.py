from rest_framework.authtoken.models import Token

# Create your views here.
def get_initial_data_user(self, request, token_request=False):
    if token_request:
        token_key = request.data['token']
        token = Token.objects.get(key=token_key)
        user = token.user
    else:
        serializer = self.serializer_class(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
    return user, token
