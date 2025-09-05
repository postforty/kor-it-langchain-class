## pgvector

### 1. 설치 버전

> Docker Hub: <https://hub.docker.com/r/pgvector/pgvector>

`pg17-trixie`는 **최신 버전**을, `0.8.0-pg17-trixie`는 **특정 버전**을 제공한다.

---

#### 1) `pg17-trixie`

- **PostgreSQL 버전**: 17
- **운영체제**: 데비안 Trixie
- **pgvector 버전**: **최신** 버전이 포함된다.
- **사용 목적**: 항상 최신 pgvector 기능을 사용하고 싶을 때.

---

#### 2) `0.8.0-pg17-trixie`

- **pgvector 버전**: **0.8.0**으로 **고정**
- **PostgreSQL 버전**: 17
- **운영체제**: 데비안 Trixie
- **사용 목적**: 특정 버전을 고정하여 **안정적인 환경**을 구축하고 싶을 때.

---

> ### 데비안 (Debian)이란?
>
> **개념**: 데비안은 **GNU/리눅스 운영체제**의 한 종류로, 전 세계 자원봉사자들의 협력으로 개발되고 유지되는 **자유 소프트웨어** 프로젝트이다.
>
> **특징**:
>
> - **안정성**: 매우 안정적이고 신뢰성이 높기로 유명하다. 서버 시스템과 같이 장기간 안정적인 운영이 중요한 환경에서 널리 사용된다.
> - **패키지 관리**: **APT(Advanced Package Tool)** 라는 강력한 패키지 관리 시스템을 사용한다. 이를 통해 소프트웨어를 쉽게 설치, 업데이트, 삭제할 수 있다.
> - **폭넓은 지원**: 수많은 하드웨어 아키텍처를 지원하며, 다양한 데스크톱 환경(GNOME, KDE, XFCE 등)을 선택할 수 있다.
>
> **철학**: 자유 소프트웨어 정신을 매우 중요하게 여긴다. 데비안은 "데비안 사회 계약"이라는 철학적 가이드라인에 따라 운영된다.
>
> **영향**: 우분투(Ubuntu), 리눅스 민트(Linux Mint) 등 수많은 인기 있는 리눅스 배포판들이 **데비안을 기반으로 만들어졌다.**

---

### 2. 설치 명령

```bash
docker run --name pgvector-container -e POSTGRES_USER=langchain -e POSTGRES_PASSWORD=langchain -e POSTGRES_DB=langchain -p 5432:5432 -d pgvector/pgvector:pg17-trixie
```

'docker run' 명령어는 **도커 컨테이너를 실행**하는 데 사용되는 명령이다. 이 명령어는 `pgvector/pgvector:pg16` 이미지를 기반으로 PostgreSQL 데이터베이스와 pgvector 확장 기능을 포함하는 컨테이너를 생성하고 실행한다.

| 옵션                             | 설명                                                                                          |
| :------------------------------- | :-------------------------------------------------------------------------------------------- |
| `--name pgvector-container`      | 컨테이너에 **pgvector-container**라는 이름을 부여                                             |
| `-e POSTGRES_USER=langchain`     | (환경 변수를 통해) 컨테이너 내 **PostgreSQL 사용자 이름**을 **langchain**으로 설정            |
| `-e POSTGRES_PASSWORD=langchain` | **langchain 사용자**의 **비밀번호**를 **langchain**으로 설정                                  |
| `-e POSTGRES_DB=langchain`       | **langchain**이라는 이름의 **데이터베이스**를 생성                                            |
| `-p 5432:5432`                   | 로컬 시스템의 **5432 포트**를 컨테이너 내부의 **5432 포트**에 연결하는 **포트 포워딩**을 설정 |
| `-d`                             | 컨테이너를 **백그라운드**(detached mode)에서 실행                                             |
| `pgvector/pgvector:pg17-trixie`  | PostgreSQL 17과 pgvector 확장 기능 포함된 **도커 이미지** 설치                                |

---

#### ✨ 볼륨을 사용하는 경우

```bash
docker run --name pgvector-container -e POSTGRES_USER=langchain -e POSTGRES_PASSWORD=langchain -e POSTGRES_DB=langchain -p 5432:5432 -v C:/docker-postgresql/postgresql_data:/var/lib/postgresql/data -d pgvector/pgvector:pg17-trixie
```

| 옵션                                                               | 설명                                                                                                                           |
| :----------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------- |
| `-v C:/docker-postgresql/postgresql_data:/var/lib/postgresql/data` | C:/docker-postgresql/postgresql_data를 컨테이너 내부의 PostgreSQL 데이터 디렉터리에 연결하여 데이터베이스 파일이 로컬에 저장함 |

```bash
docker inspect pgvector-container # 컨테이너 볼륨 확인(Mounts 섹션 검색)
```

#### ✨ 재시작 정책

`--restart` 옵션은 컨테이너의 종료 코드에 따라 다양한 재시작 정책 제공함.

| 옵션                 | 설명                                                                  | 특징                                                                                                                  |
| -------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `no`                 | 컨테이너가 종료되어도 재시작하지 않음                                 | 기본값이며, 수동으로 재시작해야 함                                                                                    |
| `on-failure`         | 컨테이너가 비정상적으로 종료될 때(종료 코드가 0이 아닐 때)만 재시작함 | 실패 시 자동 복구를 시도하며, 최대 재시작 횟수를 지정할 수 있임                                                       |
| **`unless-stopped`** | 사용자가 직접 `docker stop` 등으로 중지시키기 전까지 항상 재시작함    | Docker 데몬이 재시작되거나 시스템을 재부팅해도 컨테이너가 자동으로 실행됨(개발 및 운영 환경에서 **가장 널리 사용됨**) |
| `always`             | 어떤 이유로든 컨테이너가 종료되면 항상 재시작함                       | 사용자가 수동으로 중지해도 다시 실행되므로, 컨테이너를 영구적으로 제거하려면 `docker rm` 명령어를 사용해야 함         |

---
