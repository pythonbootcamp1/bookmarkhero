# bookmarks/views.py (Step 6 - ViewSet 사용!)
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Bookmark
from .serializers import BookmarkSerializer, UserSerializer, RegisterSerializer

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
    permission_classes = [IsAuthenticated]

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
        북마크 생성 시 owner 자동 설정
        """
        serializer.save()

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
from rest_framework_simplejwt.tokens import RefreshToken
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