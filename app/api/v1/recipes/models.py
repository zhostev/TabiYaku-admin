# api/v1/recipes/models.py
from tortoise import fields
from tortoise.models import Model

class RecipeRecognition(Model):
    id = fields.IntField(pk=True)
    image_url = fields.CharField(max_length=255)
    base64_image = fields.TextField()
    recognized_text = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "recipe_recognitions"