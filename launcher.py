"""
JARVIS 설정 마법사 / 런처
최초 실행 시 환경을 검증하고 사용자 설정을 안내한다.

실행: python launcher.py
"""
import sys
import os
import shutil

# 프로젝트 루트를 PYTHONPATH에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table

console = Console()


def check_python_version() -> bool:
    v = sys.version_info
    ok = v.major >= 3 and v.minor >= 10
    status = "[green]OK[/green]" if ok else "[red]FAIL[/red]"
    console.print(f"  Python 버전: {v.major}.{v.minor}.{v.micro} {status}")
    if not ok:
        console.print("  [red]Python 3.10 이상이 필요합니다.[/red]")
    return ok


def check_portaudio() -> bool:
    try:
        import sounddevice as sd
        sd.query_devices()
        console.print("  PortAudio: [green]OK[/green]")
        return True
    except OSError:
        console.print("  PortAudio: [red]FAIL[/red]")
        console.print("  [yellow]설치 방법:[/yellow]")
        console.print("    macOS: brew install portaudio")
        console.print("    Linux: sudo apt-get install portaudio19-dev")
        return False


def check_microphone() -> bool:
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [
            d for d in devices if d.get("max_input_channels", 0) > 0
        ]
        if input_devices:
            default = sd.query_devices(kind="input")
            console.print(f"  마이크: [green]{default['name']}[/green]")
            return True
        else:
            console.print("  마이크: [red]입력 장치를 찾을 수 없습니다[/red]")
            return False
    except Exception as e:
        console.print(f"  마이크: [red]{e}[/red]")
        return False


def check_speaker() -> bool:
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        output_devices = [
            d for d in devices if d.get("max_output_channels", 0) > 0
        ]
        if output_devices:
            default = sd.query_devices(kind="output")
            console.print(f"  스피커: [green]{default['name']}[/green]")
            return True
        else:
            console.print("  스피커: [red]출력 장치를 찾을 수 없습니다[/red]")
            return False
    except Exception as e:
        console.print(f"  스피커: [red]{e}[/red]")
        return False


def check_dependencies() -> bool:
    required = [
        ("anthropic", "Anthropic SDK"),
        ("faster_whisper", "Faster Whisper"),
        ("edge_tts", "Edge TTS"),
        ("rich", "Rich"),
        ("numpy", "NumPy"),
        ("scipy", "SciPy"),
    ]
    all_ok = True
    for module, name in required:
        try:
            __import__(module)
            console.print(f"  {name}: [green]OK[/green]")
        except ImportError:
            console.print(f"  {name}: [red]미설치[/red]")
            all_ok = False
    return all_ok


def check_env_file() -> bool:
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    example_path = os.path.join(os.path.dirname(__file__), ".env.example")

    if os.path.exists(env_path):
        console.print("  .env 파일: [green]존재[/green]")
        return True
    else:
        console.print("  .env 파일: [yellow]없음[/yellow]")
        if os.path.exists(example_path):
            if Confirm.ask("  .env.example을 복사하여 .env를 생성할까요?"):
                shutil.copy(example_path, env_path)
                console.print("  [green].env 파일을 생성했습니다.[/green]")
                return True
        return False


def check_api_key() -> bool:
    from dotenv import load_dotenv
    load_dotenv()
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if key and not key.startswith("sk-ant-여기"):
        console.print("  Anthropic API Key: [green]설정됨[/green]")
        return True
    else:
        console.print("  Anthropic API Key: [red]미설정[/red]")
        console.print("  [yellow].env 파일에 ANTHROPIC_API_KEY를 입력하세요.[/yellow]")
        return False


def test_tts() -> bool:
    console.print("\n  TTS 테스트 중...")
    try:
        from core.tts import TTS
        tts = TTS()
        tts.speak("자비스 음성 테스트 완료.")
        console.print("  TTS: [green]OK[/green]")
        return True
    except Exception as e:
        console.print(f"  TTS: [red]{e}[/red]")
        return False


def setup_autostart():
    from services.startup_service import StartupService
    service = StartupService()

    if service.is_autostart_enabled():
        console.print("  자동 시작: [green]이미 등록됨[/green]")
    else:
        if Confirm.ask("  OS 시작 시 자비스를 자동으로 실행할까요?"):
            result = service.enable_autostart()
            console.print(f"  [green]{result}[/green]")


def list_audio_devices():
    import sounddevice as sd
    devices = sd.query_devices()
    table = Table(title="오디오 장치 목록")
    table.add_column("번호", style="cyan")
    table.add_column("이름")
    table.add_column("입력", style="green")
    table.add_column("출력", style="blue")

    for i, d in enumerate(devices):
        inp = str(d["max_input_channels"]) if d["max_input_channels"] > 0 else "-"
        out = str(d["max_output_channels"]) if d["max_output_channels"] > 0 else "-"
        table.add_row(str(i), d["name"], inp, out)

    console.print(table)


def run_wizard():
    console.print(Panel.fit(
        "[bold cyan]JARVIS 설정 마법사[/bold cyan]\n"
        "[dim]시스템 환경을 검증하고 초기 설정을 진행합니다.[/dim]",
        border_style="cyan",
    ))

    # 1. 환경 검증
    console.print("\n[bold]1단계: 환경 검증[/bold]")
    results = {}
    results["python"] = check_python_version()
    results["deps"] = check_dependencies()
    results["portaudio"] = check_portaudio()
    results["mic"] = check_microphone()
    results["speaker"] = check_speaker()
    results["env"] = check_env_file()
    results["api_key"] = check_api_key()

    # 결과 요약
    critical_fail = not results["python"] or not results["deps"] or not results["portaudio"]
    if critical_fail:
        console.print("\n[bold red]필수 요구사항이 충족되지 않았습니다.[/bold red]")
        console.print("위 오류를 해결한 후 다시 실행해주세요.")
        return False

    if not results["api_key"]:
        console.print("\n[yellow]API 키가 설정되지 않았습니다.[/yellow]")
        console.print(".env 파일에 키를 입력한 후 main.py를 실행하세요.")

    # 2. 오디오 장치
    console.print("\n[bold]2단계: 오디오 장치[/bold]")
    if Confirm.ask("  오디오 장치 목록을 확인하시겠습니까?", default=False):
        list_audio_devices()

    # 3. TTS 테스트
    console.print("\n[bold]3단계: 음성 출력 테스트[/bold]")
    if results["speaker"]:
        if Confirm.ask("  음성 출력을 테스트하시겠습니까?", default=True):
            test_tts()

    # 4. 자동 시작
    console.print("\n[bold]4단계: 자동 시작 설정[/bold]")
    setup_autostart()

    # 5. 효과음 생성
    console.print("\n[bold]5단계: 효과음 생성[/bold]")
    try:
        from ui.sounds import ensure_sounds_exist
        ensure_sounds_exist()
        console.print("  효과음: [green]준비 완료[/green]")
    except Exception as e:
        console.print(f"  효과음: [yellow]{e}[/yellow]")

    # 완료
    console.print(Panel.fit(
        "[bold green]설정 완료![/bold green]\n\n"
        "자비스를 시작하려면:\n"
        "  [cyan]python main.py[/cyan]\n\n"
        "사용법:\n"
        '  [yellow]"자비스"[/yellow] 라고 말하거나 [yellow]박수 한 번[/yellow]으로 활성화\n'
        '  [yellow]박수 두 번[/yellow]으로 대화 종료\n'
        '  [yellow]박수 세 번[/yellow]으로 긴급 정지',
        border_style="green",
    ))

    return True


if __name__ == "__main__":
    run_wizard()
