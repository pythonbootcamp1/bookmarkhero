from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookmarkViewSet, AuthViewSet

router = DefaultRouter()
router.register('bookmarks', BookmarkViewSet)

# 인증 API
router.register('auth', AuthViewSet, basename='auth')

urlpatterns = [
    path('', include(router.urls)),
]


# viewset 변경코드(노션)
# -> serializer 변경코드(노션) -user정보를 결합하는 임시코드(중요X) -> 나중에 JWT인증 방식이 중요합니다.
# urls 자동완성코드(노션)
# api 테스트 화면 확인하고 테스트 해보기(postman을 쓰지 않고도 테스트가 가능)
# 11:30 까지 완료하겠습니다.


# 3:40까지 
# 회원 가입 적용해 보겠습니다!!
# 1. serializer 코드 적용
# 2. viewset 코드 적용
# 3. urls 코드 적용
# 4. postman을 통해 api 테스트 화면 확인하고 테스트 해보기