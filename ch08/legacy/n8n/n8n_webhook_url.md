## WEBHOOK_URL의 기본 역할

### 1. 웹훅 URL 생성의 기준점

```bash
# 기본 설정
WEBHOOK_URL=http://localhost:5678

# 실제 생성되는 웹훅 URL
# http://localhost:5678/webhook/[webhook-id]
# http://localhost:5678/webhook-test/[webhook-id]
```

### 2. 내부 vs 외부 접근성 제어

```bash
# 로컬 개발 환경
WEBHOOK_URL=http://localhost:5678

# 외부 접근 가능한 환경
WEBHOOK_URL=http://your-domain.com:5678

# HTTPS 사용
WEBHOOK_URL=https://your-domain.com
```

## 다양한 환경별 설정 예시

### 1. Docker 환경

```yaml
# docker-compose.yml
version: "3.7"
services:
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=0.0.0.0
      - N8N_PORT=5678
      - WEBHOOK_URL=http://localhost:5678 # 외부에서 접근할 URL
    volumes:
      - n8n_data:/home/node/.n8n
```

### 2. 프로덕션 환경 (리버스 프록시 사용)

```bash
# n8n이 내부적으로 3000 포트에서 실행
N8N_PORT=3000
N8N_HOST=127.0.0.1

# 외부에서는 80/443 포트로 접근
WEBHOOK_URL=https://n8n.yourdomain.com
```

### 3. 클라우드 환경 (AWS, GCP 등)

```bash
# 클라우드 인스턴스의 공개 IP
WEBHOOK_URL=http://your-public-ip:5678

# 로드밸런서 사용시
WEBHOOK_URL=https://your-loadbalancer-url
```

## WEBHOOK_URL이 중요한 이유

### 1. 외부 서비스 통합

```javascript
// 외부 서비스가 n8n 웹훅을 호출할 때 사용하는 URL
const webhookUrl = process.env.WEBHOOK_URL + '/webhook/' + webhookId;

// 예: GitHub 웹훅 설정
{
  "url": "https://n8n.yourdomain.com/webhook/github-integration",
  "content_type": "json"
}
```

### 2. 네트워크 라우팅 문제 해결

```bash
# 잘못된 설정 - 외부에서 접근 불가
WEBHOOK_URL=http://127.0.0.1:5678

# 올바른 설정 - 외부에서 접근 가능
WEBHOOK_URL=http://0.0.0.0:5678
# 또는
WEBHOOK_URL=http://your-external-ip:5678
```

### 3. HTTPS/SSL 처리

```bash
# HTTP에서 HTTPS로 업그레이드
WEBHOOK_URL=https://n8n.yourdomain.com

# 이 경우 n8n 앞단에 SSL 터미네이션이 필요
# (Nginx, Apache, Cloudflare 등)
```

## 일반적인 설정 패턴

### 1. 개발 환경

```bash
# .env 파일
N8N_HOST=0.0.0.0
N8N_PORT=5678
WEBHOOK_URL=http://localhost:5678
N8N_EDITOR_BASE_URL=http://localhost:5678
```

### 2. 스테이징 환경

```bash
N8N_HOST=0.0.0.0
N8N_PORT=5678
WEBHOOK_URL=http://staging.yourdomain.com:5678
N8N_EDITOR_BASE_URL=http://staging.yourdomain.com:5678
```

### 3. 프로덕션 환경

```bash
N8N_HOST=127.0.0.1  # 내부에서만 접근
N8N_PORT=3000
WEBHOOK_URL=https://api.yourdomain.com  # 외부 접근 URL
N8N_EDITOR_BASE_URL=https://workflow.yourdomain.com
```

## 트러블슈팅

### 1. 웹훅 URL이 올바르게 생성되지 않는 경우

```bash
# n8n 로그 확인
docker logs n8n-container

# 설정 확인
echo $WEBHOOK_URL
```

### 2. 외부에서 접근되지 않는 경우

```bash
# 포트 확인
netstat -tlnp | grep 5678

# 방화벽 확인
ufw status
iptables -L
```

### 3. CORS 문제 해결

```bash
# CORS 설정 추가
N8N_CORS_ORIGIN=*
# 또는 특정 도메인만
N8N_CORS_ORIGIN=https://yourdomain.com
```

## 실제 사용 예시

### Nginx 리버스 프록시 설정

```nginx
# /etc/nginx/sites-available/n8n
server {
    listen 80;
    server_name n8n.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# n8n 설정
N8N_HOST=127.0.0.1
N8N_PORT=3000
WEBHOOK_URL=http://n8n.yourdomain.com  # Nginx를 통해 접근
```

이렇게 `WEBHOOK_URL`을 올바르게 설정하면 외부 서비스들이 n8n의 웹훅에 정상적으로 접근할 수 있게 된다.
