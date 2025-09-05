## 유용한 도커 명령어

### 이미지 확인

```bash
docker image ls
```

### 이미지 삭제

```bash
docker image rm <IMAGE ID>
docker image rm -f <IMAGE ID> # 강제 삭제
```

### 이미지 삭제

```bash
docker image rm <IMAGE ID> # 해당 ID 이미지 삭제(컨테이너 중지 후)
docker image rm -f <IMAGE ID> # 강제 삭제
docker image prune -a # 사용하지 않는 모든 이미지 일괄 삭제
docker image prune -a -f # 사용하지 않는 모든 이미지 일괄 강제 삭제
```

### 컨테이너 관리

```bash
docker ps # 실행 중인 컨테이너 목록 확인
docker ps -a # 모든 컨테이너 목록 확인
docker stop <IMAGE ID> # 컨테이너 중지
docker kill <IMAGE ID> # 컨테이너 강제 중지
docker start <IMAGE ID> # 중지된 컨테이너 실행
docker rm <IMAGE ID> # 컨테이너 삭제
```
