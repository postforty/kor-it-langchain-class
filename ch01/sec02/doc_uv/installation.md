# uv 설치하기

> 원문: <https://docs.astral.sh/uv/getting-started/installation/>

## 설치 방법

uv는 독립형 설치 프로그램 또는 원하는 패키지 관리자를 통해 설치할 수 있습니다.

### 독립형 설치 프로그램

uv는 uv를 다운로드하고 설치하기 위한 독립형 설치 프로그램을 제공합니다:

irm을 사용하여 스크립트를 다운로드하고 iex로 실행하십시오:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

실행 정책을 변경하면 인터넷에서 스크립트를 실행할 수 있습니다.

URL에 특정 버전을 포함하여 특정 버전을 요청할 수 있습니다:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.8.3/install.ps1 | iex"
```

> **팁**
> 설치 스크립트는 사용 전에 검사할 수 있습니다:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | more"
```

또는 설치 프로그램이나 바이너리는 [GitHub](https://github.com/astral-sh/uv/releases)에서 직접 다운로드할 수 있습니다.

uv 설치 사용자 지정에 대한 자세한 내용은 [설치 프로그램 참조 문서](../../reference/installer/)를 참조하십시오.

### PyPI

편의를 위해 uv는 [PyPI](https://pypi.org/project/uv/)에 게시됩니다.

PyPI에서 설치하는 경우, uv를 격리된 환경(예: `pipx`)에 설치하는 것을 권장합니다:

```bash
pipx install uv
```

하지만, `pip`도 사용할 수 있습니다:

```bash
pip install uv
```

> **참고**
> uv는 많은 플랫폼용으로 사전 구축된 배포판(휠)과 함께 제공됩니다. 특정 플랫폼에 휠이 없는 경우, uv는 Rust 툴체인을 필요로 하는 소스에서 빌드됩니다. 소스에서 uv를 빌드하는 방법에 대한 자세한 내용은 [기여 설정 가이드](https://github.com/astral-sh/uv/blob/main/CONTRIBUTING.md#setup)를 참조하십시오.

### Homebrew

uv는 Homebrew 핵심 패키지에서 사용할 수 있습니다.

```bash
brew install uv
```

### WinGet

uv는 [WinGet](https://winstall.app/apps/astral-sh.uv)을 통해 사용할 수 있습니다.

```bash
winget install --id=astral-sh.uv  -e
```

### Scoop

uv는 [Scoop](https://scoop.sh/#/apps?q=uv)을 통해 사용할 수 있습니다.

```bash
scoop install main/uv
```

### Docker

uv는 [ghcr.io/astral-sh/uv](https://github.com/astral-sh/uv/pkgs/container/uv)에서 Docker 이미지를 제공합니다.

자세한 내용은 [Docker에서 uv 사용 가이드](../../guides/integration/docker/)를 참조하십시오.

### GitHub 릴리스

uv 릴리스 아티팩트는 [GitHub 릴리스](https://github.com/astral-sh/uv/releases)에서 직접 다운로드할 수 있습니다.

각 릴리스 페이지에는 지원되는 모든 플랫폼용 바이너리와 astral.sh 대신 github.com을 통해 독립형 설치 프로그램을 사용하는 방법에 대한 지침이 포함되어 있습니다.

### Cargo

uv는 Cargo를 통해 사용할 수 있지만, 게시되지 않은 크레이트에 대한 종속성으로 인해 [crates.io](https://crates.io) 대신 Git에서 빌드되어야 합니다.

```bash
cargo install --git https://github.com/astral-sh/uv uv
```

> **참고**
> 이 방법은 호환되는 Rust 툴체인을 필요로 하는 소스에서 uv를 빌드합니다.

## uv 업그레이드하기

uv가 독립형 설치 프로그램을 통해 설치된 경우, 필요에 따라 자체적으로 업데이트할 수 있습니다:

```bash
uv self update
```

> **팁**
> uv를 업데이트하면 설치 프로그램이 다시 실행되고 셸 프로필을 수정할 수 있습니다. 이 동작을 비활성화하려면 `INSTALLER_NO_MODIFY_PATH=1`로 설정하십시오.

다른 설치 방법이 사용될 경우, 자체 업데이트는 비활성화됩니다. 대신 패키지 관리자의 업그레이드 방법을 사용하십시오. 예를 들어, `pip`의 경우:

```bash
pip install --upgrade uv
```

## 셸 자동 완성

> **팁**
> 셸을 확인하는 데 도움이 되도록 `echo $SHELL`을 실행할 수 있습니다.

uv 명령어에 대한 셸 자동 완성을 활성화하려면 다음 중 하나를 실행하십시오:

```powershell
if (!($PROFILE | Test-Path)) {
  New-Item -ItemType File -Path $PROFILE -Force
}
Add-Content -Path $PROFILE -Value "(& uv generate-shell-completion powershell) | Out-String | Invoke-Expression"
```

uvx에 대한 셸 자동 완성을 활성화하려면 다음 중 하나를 실행하십시오:

```powershell
if (!($PROFILE | Test-Path)) {
  New-Item -ItemType File -Path $PROFILE -Force
}
Add-Content -Path $PROFILE -Value "(& uvx --generate-shell-completion powershell) | Out-String | Invoke-Expression"
```

그런 다음 셸을 다시 시작하거나 셸 구성 파일을 소싱하십시오.

## 제거

시스템에서 uv를 제거해야 하는 경우, 다음 단계를 따르십시오:

1.  저장된 데이터 정리(선택 사항):

    ```bash
    uv cache clean
    rm -r "$(uv python dir)"
    rm -r "$(uv tool dir)"
    ```

    > **팁**
    > 바이너리를 제거하기 전에, uv가 저장한 데이터를 제거하는 것을 권장합니다.

2.  uv 및 uvx 바이너리 제거:

    ```powershell
    rm $HOME\.local\bin\uv.exe
    rm $HOME\.local\bin\uvx.exe
    ```

    > **참고**
    > 0.5.0 이전에는 uv가 `~/.cargo/bin`에 설치되었습니다. 해당 위치에서 바이너리를 제거하여 제거할 수 있습니다. 이전 버전에서 업그레이드해도 `~/.cargo/bin`의 바이너리가 자동으로 제거되지는 않습니다.

## 다음 단계

uv 사용을 시작하려면 [첫 단계](../first-steps/)를 참조하거나 바로 [가이드](../../guides/)로 이동하십시오.
