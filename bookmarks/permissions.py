# bookmarks/permissions.py (새 파일 생성)

from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    자기 것만 수정/삭제 가능
    """

    def has_object_permission(self, request, view, obj):
        # obj = 수정/삭제하려는 북마크
        # request.user = 현재 로그인한 사용자
        if request.method in permissions.SAFE_METHODS:
            return True
        # 북마크 주인과 현재 사용자가 같으면 True
        return obj.owner == request.user