from .models import Note, Category, Tag
from rest_framework import serializers

class CategorySerializer(serializers.ModelSerializer):
    """Category to front end"""
    class Meta:
        model = Category
        fields = ['id', 'name', 'user', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'user']
        read_only_fields = ['id', 'user']

class NotesSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category.name',
        read_only=True,
        default=""
    )
    tags_names = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name',
        source='tags'
    )

    user_name = serializers.CharField(
        source='user.username',
        read_only=True,
    )

    class Meta:
        model = Note
        fields = "__all__"
        read_only_fields = ['id', 'created_at', 'user', 'user_name']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class ImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "image"]
        read_only_fields = ["id"]

