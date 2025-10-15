"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,      # 로그인 (토큰 발급)
    TokenRefreshView,         # 토큰 갱신
    TokenVerifyView,          # 토큰 검증
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # ===== 북마크 API =====
    path('api/', include('bookmarks.urls')),
    # ===== JWT 인증 API =====
    # 로그인: username/password → Access + Refresh Token
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    # 토큰 갱신: Refresh Token → 새 Access Token
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 토큰 검증: 토큰이 유효한지 확인 (선택사항)
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]

# 1:40까지
# view 내용 입력 -> 어떤 흐름이 구성되어 있는지 확인
# url 작성
# 서버 실행
# postman 테스트 - GET:조회, POST:생성
