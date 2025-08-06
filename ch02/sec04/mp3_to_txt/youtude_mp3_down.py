# uv add yt_dlp
import yt_dlp
import os


def download_youtube_video(url):
    """
    주어진 유튜브 링크의 영상을 MP3 파일로 다운로드합니다.

    Args:
        url (str): 다운로드할 유튜브 영상의 URL.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': './downloads/%(title)s.%(ext)s',
    }
    try:
        # downloads 폴더가 없으면 생성
        if not os.path.exists('./downloads'):
            os.makedirs('./downloads')

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"음성 파일 다운로드가 완료되었습니다: {url}")
    except yt_dlp.utils.DownloadError as e:
        print(f"다운로드 오류: {e}")
    except yt_dlp.utils.ExtractorError as e:
        print(f"추출 오류: {e}")
    except Exception as e:
        print(f"영상 다운로드 중 오류가 발생했습니다: {e}")
        print("유효한 유튜브 링크인지 확인하거나, yt-dlp를 최신 버전으로 업데이트해 보십시오.")


if __name__ == "__main__":
    video_url = input("MP3 파일로 다운로드할 유튜브 영상 링크를 입력하십시오: ")
    if video_url:
        download_youtube_video(video_url)
    else:
        print("유튜브 링크가 입력되지 않았습니다.")

# video_url 예시
# - Steve Jobs' 2005 Stanford Commencement Address: https://youtu.be/UF8uR6Z6KLc?feature=shared

# 오류 발생 시
# ERROR: Postprocessing: ffprobe and ffmpeg not found. Please install or provide the path using --ffmpeg-location 
# FFmpeg 공식 웹사이트: https://ffmpeg.org/download.html 에서 윈도우 버전을 다운로드합니다.
# 다운로드 후 환경 변수에 추가합니다.
# 환경 변수 추가 방법:
# 1. 제어판 > 시스템 및 보안 > 시스템 > 고급 시스템 설정 > 환경 변수 > 시스템 변수 > 새로 만들기
# 2. 추가 내용: C:\ffmpeg-2025-08-04-git-9a32b86307-full_build\bin
# 3. 확인 버튼을 클릭하여 저장합니다.
# 4. 환경 변수 추가 후 터미널을 다시 시작합니다.
# 5. 터미널에서 다시 실행합니다.
# 6. 터미널에서 테스트: ffmpeg -version
# 참고: https://kminito.tistory.com/108