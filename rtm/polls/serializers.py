from rest_framework import serializers


class PollResultSerializer(serializers.Serializer):
    contact = serializers.CharField(max_length=36)
    category = serializers.CharField(max_length=255)
    text = serializers.CharField()
