# bookmarks/views.py (Step 6 - ViewSet 사용!)
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,IsAuthenticatedOrReadOnly
from .models import Bookmark
from .serializers import BookmarkSerializer, UserSerializer, RegisterSerializer
from .permissions import IsOwnerOrReadOnly

class BookmarkViewSet(viewsets.ModelViewSet):
    """
    북마크 ViewSet

    기능:
    - list: 북마크 목록
    - create: 북마크 생성
    - retrieve: 북마크 상세
    - update: 북마크 수정
    - partial_update: 북마크 부분 수정
    - destroy: 북마크 삭제

    커스텀 액션:
    - recent: 최근 북마크
    - my_bookmarks: 내 북마크
    - public_bookmarks: 공개 북마크
    - toggle_public: 공개/비공개 토글
    """
    queryset = Bookmark.objects.select_related('owner').all()
    serializer_class = BookmarkSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        """
        사용자별로 다른 queryset 반환
        - 일반 사용자: 자신의 북마크 + 공개 북마크
        - 관리자: 모든 북마크
        """
        return Bookmark.objects.all()
        # user = self.request.user

        # if user.is_staff:
        #     # 관리자: 모든 북마크
        #     return Bookmark.objects.select_related('owner').all()
        # else:
        #     # 일반 사용자: 자신의 북마크 + 공개 북마크
        #     from django.db.models import Q
        #     return Bookmark.objects.select_related('owner').filter(
        #         Q(owner=user) | Q(is_public=True)
        #     )

    def perform_create(self, serializer):
        """
        북마크 생성 시 owner를 현재 로그인한 사용자로 자동 설정
        """
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        최근 북마크 10개
        URL: GET /bookmarks/recent/
        """
        bookmarks = self.get_queryset().order_by('-created_at')[:10]
        serializer = self.get_serializer(bookmarks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_bookmarks(self, request):
        """
        내 북마크만 조회
        URL: GET /bookmarks/my_bookmarks/
        """
        bookmarks = Bookmark.objects.filter(owner=request.user)
        serializer = self.get_serializer(bookmarks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def public_bookmarks(self, request):
        """
        공개 북마크만 조회
        URL: GET /bookmarks/public_bookmarks/
        """
        bookmarks = Bookmark.objects.filter(is_public=True)
        serializer = self.get_serializer(bookmarks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_public(self, request, pk=None):
        """
        공개/비공개 토글
        URL: POST /bookmarks/{id}/toggle_public/
        """
        bookmark = self.get_object()

        # 자신의 북마크만 수정 가능
        if bookmark.owner != request.user:
            return Response(
                {'error': '자신의 북마크만 수정할 수 있습니다.'},
                status=status.HTTP_403_FORBIDDEN
            )

        bookmark.is_public = not bookmark.is_public
        bookmark.save()

        serializer = self.get_serializer(bookmark)
        return Response(serializer.data)

from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from django.contrib.auth import get_user_model
User = get_user_model()

class AuthViewSet(viewsets.GenericViewSet):
    """
    인증 관련 ViewSet

    GenericViewSet: 기본 CRUD 없이 커스텀 액션만 사용
    """

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        회원가입

        URL: POST /api/auth/register/

        요청:
        {
            "username": "john",
            "email": "john@example.com",
            "password": "secret123",
            "password_confirm": "secret123",
            "first_name": "John",
            "last_name": "Doe"
        }

        응답:
        {
            "user": {
                "id": 1,
                "username": "john",
                "email": "john@example.com"
            },
            "tokens": {
                "access": "eyJhbGciOi...",
                "refresh": "eyJzdWIiOi..."
            }
        }
        """
        # 1. 요청 데이터 검증
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. 사용자 생성
        user = serializer.save()

        # 3. JWT 토큰 생성
        # 회원가입 후 자동 로그인 처리
        refresh = RefreshToken.for_user(user)

        # 4. 응답 반환
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        현재 로그인한 사용자 정보 조회

        URL: GET /api/auth/me/
        Headers: Authorization: Bearer <access_token>

        응답:
        {
            "id": 1,
            "username": "john",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "date_joined": "2025-10-12T10:30:00Z"
        }
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        로그아웃

        URL: POST /api/auth/logout/
        Headers: Authorization: Bearer <access_token>

        요청:
        {
            "refresh": "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6I..."
        }

        응답:
        {
            "detail": "로그아웃되었습니다."
        }
        """
        try:
            # 1. Refresh Token 가져오기
            refresh_token = request.data.get('refresh')

            if not refresh_token:
                return Response(
                    {'detail': 'Refresh token이 필요합니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2. Refresh Token 블랙리스트에 추가
            token = RefreshToken(refresh_token)
            token.blacklist()
            # 내부적으로 token_blacklist_blacklistedtoken 테이블에 추가됨

            return Response(
                {'detail': '로그아웃되었습니다.'},
                status=status.HTTP_200_OK
            )

        except TokenError:
            return Response(
                {'detail': '유효하지 않은 토큰입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )


# 로그아웃 기능을 구현
# access token / refresh token 을 입력해서 테스트
# 10:50까지 진행해 보겠습니다!


# PUT, PATCH, DELETE 실습 (정상상황) -> REST API 사용법 익히기
# 1. 토큰 발급
# 2. 인증 설정(Authoriztion: Bearer <access_token>)
# 3. PUT, PATCH, DELETE 요청 보내기 -> localhost:8000/api/bookmarks/<대상bookmark id>/ -> PUT, PATCH, DELETE 요청 보내기
# 4. PUT, PATCH 차이점 확인 -> 전체 수정(전체 내용을 넣어줘야 합니다) vs 부분 수정(수정할 내용만 넣어주면 됩니다)
# 11:40까지 진행해 보겠습니다.


# 권한 부여 실습
# IsOwnerOrReadOnly or IsOwner 클래스 작성 하고 적용 -> 어떻게 동작하는지 확인
# 1:50까지 진행해 보겠습니다.