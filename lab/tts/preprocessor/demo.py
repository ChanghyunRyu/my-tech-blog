import normalizer


text = "이 기능은 real-time rendering을 사용합니다. 이번 프로젝트는 server-side rendering 구조입니다. 모델 학습은 Python script로 실행합니다. 권한 관리에는 OAuth 2.0을 사용합니다. 배포는 CI/CD pipeline으로 자동화되었습니다."
print(normalizer.normalize_text(text))
