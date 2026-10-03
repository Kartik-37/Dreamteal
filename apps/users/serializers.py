"""
Serializers for User Authentication and User Profile in DreamTeal.
Strictly adheres to the Zero-Star Rating Policy.
"""

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from apps.users.models import UserProfile

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'display_name', 'bio', 'avatar_url', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserMeSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source='profile.display_name', read_only=True)
    bio = serializers.CharField(source='profile.bio', read_only=True)
    avatar_url = serializers.CharField(source='profile.avatar_url', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'display_name', 'bio', 'avatar_url', 'is_staff']
        read_only_fields = ['id', 'username', 'email', 'display_name', 'bio', 'avatar_url', 'is_staff']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError('Invalid username or password.')
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled.')
        attrs['user'] = user
        return attrs
