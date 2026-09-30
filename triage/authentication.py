from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

         # use role from django group
        role = user.groups.first().name if user.groups.exists() else "User"

        # add custom info to jwt
        token["role"] = role
        token["full_name"] = user.get_full_name()

        return token