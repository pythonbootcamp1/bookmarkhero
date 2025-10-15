# bookmarks/serializers.py (Step 5)
from rest_framework import serializers
from .models import Bookmark
from django.contrib.auth import get_user_model

User = get_user_model()
    
class BookmarkSerializer(serializers.ModelSerializer):
    """
    ModelSerializer 버전
    총 48줄 (40% 감소!)
    """
    owner = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()
    )
    # ===== Meta 클래스로 필드 자동 생성 =====
    # 기존 7줄 → 4줄로 감소!
    class Meta:
        model = Bookmark  # 이 모델을 기반으로 Serializer 생성
        fields = '__all__'  # 모든 필드를 자동으로 포함
        read_only_fields = ['id', 'created_at', 'owner']

        # 이 4줄이 다음 7줄을 대체함:
        # id = serializers.IntegerField(read_only=True)
        # title = serializers.CharField(max_length=200)
        # url = serializers.URLField()
        # description = serializers.CharField(...)
        # is_public = serializers.BooleanField(default=True)
        # owner = serializers.CharField(...)
        # created_at = serializers.DateTimeField(read_only=True)

    # ===== 검증 메서드는 그대로 유지 (65줄) =====
    # 비즈니스 로직이므로 자동화 불가능
    def validate_url(self, value):
        from urllib.parse import urlparse

        queryset = Bookmark.objects.filter(url=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                "이 URL은 이미 저장되어 있습니다."
            )

        parsed = urlparse(value)
        domain = parsed.netloc
        blocked_domains = ['spam.com', 'malicious.com']
        if domain in blocked_domains:
            raise serializers.ValidationError(
                f"이 도메인({domain})은 차단되었습니다."
            )

        return value

    def validate_title(self, value):
        import re
        clean_title = re.sub(r'<[^>]+>', '', value)

        if len(clean_title.strip()) < 3:
            raise serializers.ValidationError(
                "제목은 HTML 태그를 제외하고 3자 이상이어야 합니다."
            )

        return clean_title

    def validate(self, attrs):
        is_public = attrs.get('is_public')
        description = attrs.get('description')

        if is_public and not description:
            raise serializers.ValidationError(
                "공개 북마크는 설명이 필수입니다."
            )

        return attrs

    # ===== create/update 메서드 삭제! =====
    # 기존 8줄 → 0줄!
    # ModelSerializer가 자동으로 처리
    #
    # 아래 코드들이 모두 사라짐:
    # def create(self, validated_data):
    #     return Bookmark.objects.create(**validated_data)
    #
    # def update(self, instance, validated_data):
    #     instance.title = validated_data.get('title', instance.title)
    #     ...
    #     instance.save()
    #     return instance


# model serializer 를 적용해 보겠습니다
# 이전의 코드와의 차이점을 확인
# 잘 동작하는지 postman 으로 확인
# 9시 50분까지 완료하겠습니다.

class UserSerializer(serializers.ModelSerializer):
    """
    사용자 조회용 Serializer
    비밀번호는 제외
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    """
    회원가입용 Serializer

    비즈니스 요구사항:
    - username: 3자 이상 (중복 체크는 ModelSerializer가 자동 처리)
    - email: 필수 (중복 체크)
    - password: 8자 이상, 영문+숫자 조합
    - password_confirm: password와 일치해야 함
    """

    # password 필드를 ModelSerializer가 자동 생성하지만
    # write_only=True를 명시적으로 설정
    password = serializers.CharField(
        write_only=True,     # 응답에 포함 안 됨
        min_length=8,        # 최소 8자
        style={'input_type': 'password'}  # Browsable API에서 password 입력란으로 표시
    )

    # 비밀번호 확인 필드 (모델에는 없는 필드)
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
        extra_kwargs = {
            'email': {'required': True},  # email을 필수로
        }

    def validate_username(self, value):
        """
        username 필드 검증

        실행 시점: is_valid() 호출 시
        ModelSerializer가 이미 unique 체크를 하지만
        추가 비즈니스 로직이 필요하면 여기에 작성
        """
        # 최소 길이 체크
        if len(value) < 3:
            raise serializers.ValidationError(
                "사용자명은 3자 이상이어야 합니다."
            )

        # 특수문자 체크 (선택사항)
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                "사용자명은 영문, 숫자, 언더스코어만 가능합니다."
            )

        return value

    def validate_email(self, value):
        """
        email 중복 체크
        """
        # ModelSerializer가 자동으로 unique 체크를 하지만
        # 더 친절한 에러 메시지를 위해 명시적으로 작성
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "이미 사용 중인 이메일입니다."
            )

        return value

    def validate_password(self, value):
        """
        password 복잡도 검증
        """
        import re

        # 영문 포함 확인
        if not re.search(r'[a-zA-Z]', value):
            raise serializers.ValidationError(
                "비밀번호는 영문을 포함해야 합니다."
            )

        # 숫자 포함 확인
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError(
                "비밀번호는 숫자를 포함해야 합니다."
            )

        # Django의 기본 비밀번호 검증도 사용 (선택사항)
        from django.contrib.auth.password_validation import validate_password as django_validate
        try:
            django_validate(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))

        return value

    def validate(self, attrs):
        """
        객체 레벨 검증
        password와 password_confirm 일치 확인
        """
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm')  # pop으로 제거 (모델에 없는 필드)

        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': '비밀번호가 일치하지 않습니다.'
            })

        return attrs

    def create(self, validated_data):
        """
        사용자 생성

        중요: 비밀번호는 해시화하여 저장!
        User.objects.create() 대신 create_user() 사용
        """
        # create_user()는 자동으로 비밀번호를 해시화
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],  # 자동 해시화됨
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )

        return user