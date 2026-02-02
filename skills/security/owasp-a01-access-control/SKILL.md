# Access Control Review Skill

## 목적
권한 부여 및 접근 제어 관련 취약점을 탐지합니다.

## OWASP A01:2025 - Broken Access Control

접근 제어는 사용자가 허용된 범위를 벗어나 행동하지 못하도록 하는 정책입니다.
실패 시 무단 정보 공개, 수정, 삭제 또는 권한 상승이 발생합니다.

## 체크리스트

| 체크 | 항목 | 심각도 |
|------|------|--------|
| [ ] | 모든 엔드포인트에 권한 검사 존재 | Critical |
| [ ] | IDOR 취약점 없음 (직접 객체 참조) | Critical |
| [ ] | 수직 권한 상승 불가 (일반 사용자 → 관리자) | High |
| [ ] | 수평 권한 상승 불가 (사용자 A → 사용자 B 데이터) | High |
| [ ] | CORS 설정 적절 | Medium |
| [ ] | JWT/세션 검증 적절 | High |
| [ ] | 기본 거부 정책 적용 | Medium |

## Red Flags (경고 신호)

- 권한 검사 없는 관리자 엔드포인트
- 사용자 ID를 URL 파라미터로 직접 사용
- 클라이언트 측 권한 검사만 존재
- 하드코딩된 역할 목록
- 권한 검사 로직 중복

## 언어별 검토 패턴

### Python/FastAPI
```python
# 검색 키워드
@router, Depends, current_user, @requires, get_current_user

# 위험 패턴
request.query_params.get("user_id")  # IDOR 가능
# 권한 데코레이터 없는 @router.post  # 미검증 접근

# 안전 패턴
async def get_item(item_id: int, user: User = Depends(get_current_user)):
    item = await get_item_by_id(item_id)
    if item.owner_id != user.id:
        raise HTTPException(403)
```

### Node.js/Express
```javascript
// 검색 키워드
req.user, isAuthenticated, authorize, middleware

// 위험 패턴
req.params.userId  // 직접 사용 시 IDOR 가능
// 미들웨어 없는 라우트  // 미검증 접근

// 안전 패턴
router.get('/items/:id', authenticate, async (req, res) => {
    const item = await Item.findById(req.params.id);
    if (item.userId !== req.user.id) {
        return res.status(403).json({ error: 'Forbidden' });
    }
});
```

## 검토 질문

1. 이 리소스에 접근하려면 어떤 권한이 필요한가?
2. 권한 검사가 서버 측에서 수행되는가?
3. 다른 사용자의 데이터에 접근할 수 있는 경로가 있는가?
4. 관리자 기능이 일반 사용자에게 노출되어 있는가?

## 발견 시 보고 형식

```markdown
**[Critical]** src/api/users.py:45

IDOR 취약점: 사용자 ID 파라미터가 현재 사용자와 일치하는지 검증하지 않음.
공격자가 다른 사용자의 데이터에 접근할 수 있습니다.

**수정 제안**:
```python
if user_id != current_user.id and not current_user.is_admin:
    raise HTTPException(status_code=403, detail="Forbidden")
```
```
