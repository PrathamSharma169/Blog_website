from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Tweet(models.Model):
    user= models.ForeignKey(User,on_delete=models.CASCADE)
    title=models.TextField(max_length=240,default='my first blog')
    text=models.TextField(max_length=240)
    photo=models.ImageField(upload_to='photos/',blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField( auto_now=True)
    likes = models.ManyToManyField(User, related_name='liked_tweets', blank=True)

    def like_count(self):
        return self.likes.count()

    def __str__(self):
        return f'{self.user.username}- {self.text[:10]}'
    
class Comment(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    sentiment = models.CharField(max_length=20, default='neutral')  # 'positive', 'negative', 'neutral'

    def __str__(self):
        return f"{self.user.username}: {self.text[:30]}"