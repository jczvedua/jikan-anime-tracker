from django.db import models
from django.core.validators import MinValueValidator

class AnimeList(models.Model):
    STATUS_CHOICES = [
        ('watching', 'Watching'),
        ('planning', 'Plan to Watch'),
        ('completed', 'Completed'),
        ('paused', 'On Hold'),
        ('dropped', 'Dropped')
    ]

    anilist_id = models.IntegerField(null=False, blank=False, unique=True)
    # title = models.CharField(max_length=255)
    # image_url = models.URLField(max_length=500, blank=True)
    progress = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    total_episodes = models.PositiveIntegerField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default="planning",
        )
    is_active = models.BooleanField(default=True)
    
    def __str__ (self):
        return str(self.anilist_id)

