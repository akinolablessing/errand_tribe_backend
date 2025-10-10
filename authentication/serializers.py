from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from .models import IdentityVerification, WithdrawalMethod

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number", "role"]

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(User.objects.make_random_password())
        user.save()
        return user

class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return data


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data["email"], password=data["password"])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        # data["user"] = user
        if not user.is_active:
            raise serializers.ValidationError("This account is inactive")
        data["is_active"] = user
        return data


class EmailOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(required=False, max_length=6)



class IdentityVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityVerification
        fields = ['country', 'document_type', 'document_file','verified','submitted_at']
        read_only_fields = ['verified','submitted_at']

class UploadPictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["profile_picture"]

class LocationPermissionSerializer(serializers.ModelSerializer):
    location_permission = serializers.ChoiceField(choices=User.LOCATION_CHOICES)

    class Meta:
        model = User
        fields = ["location_permission"]

    def validate_location_permission(self, value):
        if value not in dict(User.LOCATION_CHOICES):
            raise serializers.ValidationError("Invalid location permission choice.")
        return value

class WithdrawalMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalMethod
        fields = ["id", "method_type", "bank_name", "account_number", "account_name", "created_at"]
        read_only_fields =["id","created_at"]