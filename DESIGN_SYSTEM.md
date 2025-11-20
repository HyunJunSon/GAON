# GAON 디자인 시스템

## 🎨 브랜드 정체성
**GAON = "따뜻함, 대화, 가족, 온기, 심리 안정"**

- 따뜻하고 안정적이며 신뢰감 있는 디자인 톤
- 감성적이면서도 전문적인 외관
- 가족/대화/웰니스 분위기

---

## 🎨 컬러 시스템

### Primary Colors (따뜻한 그라데이션)
```css
/* 메인 그라데이션 */
from-orange-500 to-red-500
from-orange-600 to-red-600 (hover)

/* 헤더 배경 */
from-orange-50 via-white to-red-100

/* 아이콘 배경 (투명도 적용) */
from-orange-500/20 to-red-500/20
from-orange-100 to-red-100
```

### Neutral Colors
```css
/* 텍스트 */
text-gray-900  /* 주요 텍스트 */
text-gray-600  /* 본문 텍스트 */
text-gray-500  /* 보조 텍스트 */
text-gray-400  /* 비활성 텍스트 */

/* 배경 */
bg-white       /* 카드 배경 */
bg-gray-50     /* 비활성 배경 */
bg-orange-50   /* 연한 강조 배경 */
```

### Status Colors
```css
/* 성공 */
bg-green-100 text-green-700

/* 경고 */
bg-yellow-100 text-yellow-700

/* 에러 */
bg-red-50 text-red-600 border-red-200

/* 정보 */
bg-blue-50 text-blue-700
```

---

## 📐 타이포그래피

### Font Family
- **Primary**: Pretendard Variable (한글 최적화)
- **Fallback**: -apple-system, BlinkMacSystemFont, system-ui

### Font Scale
```css
/* 헤더 */
text-4xl (36px) - 페이지 메인 타이틀 (md:)
text-3xl (30px) - 섹션 타이틀
text-2xl (24px) - 서브 섹션 타이틀
text-xl (20px)  - 카드 타이틀

/* 본문 */
text-lg (18px)  - 강조 본문
text-base (16px) - 기본 본문
text-sm (14px)  - 보조 텍스트
text-xs (12px)  - 캡션
```

### Font Weight
```css
font-bold (700)    - 메인 타이틀
font-semibold (600) - 섹션 타이틀
font-medium (500)   - 강조 텍스트
font-normal (400)   - 본문
```

### Line Height
```css
leading-relaxed (1.625) - 본문 텍스트
leading-normal (1.5)    - 기본
```

---

## 📦 간격 시스템 (Spacing Scale)

### Vertical Spacing (space-y)
```css
space-y-2  (8px)  - 컴포넌트 내부 작은 간격
space-y-3  (12px) - 리스트 아이템 간격
space-y-4  (16px) - 섹션 내부 간격
space-y-6  (24px) - 폼 필드 간격
space-y-8  (32px) - 섹션 간격
space-y-10 (40px) - 큰 섹션 간격
```

### Horizontal Spacing (gap)
```css
gap-2  (8px)  - 아이콘과 텍스트
gap-3  (12px) - 헤더 아이템
gap-4  (16px) - 카드 내부 요소
gap-6  (24px) - 큰 요소 간격
```

### Padding
```css
p-4  (16px) - 작은 카드
p-6  (24px) - 중간 카드
p-8  (32px) - 큰 카드/섹션
px-4 py-3   - 버튼 (최소 터치 영역 44px)
```

---

## 🔲 Border Radius

```css
rounded-xl   (12px) - 기본 카드, 버튼
rounded-2xl  (16px) - 큰 카드, 섹션
rounded-3xl  (24px) - 헤더 섹션
rounded-full - 원형 요소
```

---

## 🌑 Shadow System

```css
shadow-sm    - 작은 그림자 (카드 호버)
shadow-lg    - 기본 그림자 (카드)
shadow-xl    - 큰 그림자 (호버 상태)
shadow-inner - 내부 그림자 (헤더 배경)
```

---

## 🎯 컴포넌트 톤

### 헤더 (Header)
```tsx
<header className="rounded-3xl border border-orange-200 bg-gradient-to-br from-orange-50 via-white to-red-100 p-8 shadow-inner">
  {/* 아이콘 + 타이틀 + 설명 + 정보 카드 */}
</header>
```

### 카드 (Card)
```tsx
<section className="rounded-2xl border border-orange-100 bg-white p-8 shadow-lg">
  {/* 섹션 헤더 + 컨텐츠 */}
</section>
```

### 버튼 (Button)
```tsx
{/* Primary */}
<button className="rounded-xl bg-gradient-to-r from-orange-500 to-red-500 px-6 py-3 text-white font-semibold shadow-lg transition-all hover:from-orange-600 hover:to-red-600 hover:shadow-xl">

{/* Secondary */}
<button className="rounded-xl border border-gray-200 bg-white px-4 py-2 text-gray-700 hover:bg-gray-50">

{/* Destructive */}
<button className="rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-red-600 hover:bg-red-100">
```

### 입력 필드 (Input)
```tsx
<input className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm focus:border-orange-500 focus:outline-none focus:ring-2 focus:ring-orange-500/20">
```

### 알림 (Alert)
```tsx
<div className="rounded-xl border border-red-200 bg-red-50/80 p-4 text-sm text-red-600">
```

---

## 🎭 애니메이션 & 트랜지션

### 기본 트랜지션
```css
transition-all duration-200  - 기본
transition-colors           - 색상만
transition-transform        - 변형만
```

### 호버 효과
```css
hover:shadow-xl           - 그림자 증가
hover:-translate-y-1      - 살짝 위로
hover:scale-110          - 확대
hover:border-orange-200  - 테두리 색상 변경
```

### 로딩 상태
```css
animate-spin - 회전 애니메이션
```

---

## 📱 반응형 디자인

### Breakpoints
```css
/* 모바일 우선 접근 */
기본: 모바일 스타일
md: (768px+) - 태블릿/데스크탑
```

### 레이아웃 패턴
```tsx
{/* 반응형 그리드 */}
<div className="grid grid-cols-1 gap-4 md:grid-cols-2">

{/* 반응형 플렉스 */}
<div className="flex flex-col gap-6 md:flex-row md:items-center">
```

### 터치 영역
- 최소 터치 영역: **44px × 44px** (모바일 접근성)
- 버튼: `min-h-[44px]` 또는 `py-3` (12px × 2 + 텍스트 높이)

---

## ♿ 접근성 (Accessibility)

### ARIA 속성
```tsx
aria-label="설명 텍스트"
aria-invalid={errors.email ? 'true' : 'false'}
aria-describedby={errors.email ? 'error-id' : undefined}
```

### 키보드 네비게이션
- 모든 인터랙티브 요소는 `focus-visible` 스타일 적용
- 포커스 링: `focus:ring-2 focus:ring-orange-500/20`

### 색상 대비
- 텍스트와 배경: WCAG AA 기준 준수 (4.5:1 이상)
- 주요 액션 버튼: 명확한 색상 대비

---

## 🎨 일관성 체크리스트

- [x] 모든 페이지 헤더 동일한 스타일
- [x] 카드 border-radius 통일 (rounded-2xl)
- [x] 그림자 시스템 일관성
- [x] 간격 시스템 준수 (4-8-12-16-24-32)
- [x] 컬러 그라데이션 통일
- [x] 버튼 스타일 통일
- [x] 입력 필드 스타일 통일
- [x] 반응형 디자인 적용
- [x] 접근성 속성 추가


