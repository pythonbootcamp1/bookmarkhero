# bookmarks/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Bookmark(models.Model):
    """
    북마크 모델
    
    실무 팁:
    - created_at, updated_at은 거의 모든 모델에 포함
    - owner는 ForeignKey로 사용자와 연결
    - __str__ 메서드는 Admin에서 보기 편하게
    """
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    title = models.CharField(max_length=200)
    url = models.URLField(unique=True)  # URL 중복 방지
    description = models.TextField(blank=True)
    # 새로 추가하는 필드
    is_public = models.BooleanField('공개 여부', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']  # 최신순 정렬
        
    def __str__(self):
        return self.title