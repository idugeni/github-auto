"""CLI entry point for github-auto."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="github-auto",
    help="Automated GitHub account creation with anti-detection",
    no_args_is_help=True,
)
console = Console()


@app.command()
def register(
    count: int = typer.Option(1, "-n", "--count", help="Number of accounts to create"),
    proxy: Optional[str] = typer.Option(None, "--proxy", help="Single proxy URL"),
    proxy_file: Optional[str] = typer.Option(None, "--proxy-file", help="Proxy list file"),
    email_provider: Optional[str] = typer.Option(None, "--email-provider", help="Email provider (lewattok/supabase)"),
    delay: Optional[float] = typer.Option(None, "--delay", help="Delay between accounts (seconds)"),
    resume: bool = typer.Option(False, "--resume", help="Resume from checkpoint"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Create GitHub accounts."""
    from config.settings import config
    from src.core.pipeline import Pipeline
    from src.core.store import AccountStore
    from src.email.manager import EmailManager
    from src.proxy.manager import ProxyManager
    from providers.github import GithubProvider

    store = AccountStore(config.storage.accounts_file)
    email_mgr = EmailManager(email_provider)
    proxy_mgr = ProxyManager(proxy_file=proxy_file, static_proxy=proxy)

    provider = GithubProvider(email_manager=email_mgr, proxy_manager=proxy_mgr)

    pipeline = Pipeline(
        store=store,
        worker=provider.create_account,
        delay_base=delay or config.pipeline.delay_base,
        delay_jitter=config.pipeline.delay_jitter,
        checkpoint_file=config.pipeline.checkpoint_file,
    )

    start = time.time()

    if json_output:
        result = pipeline.run(count=count, resume=resume)
        elapsed = time.time() - start
        print(json.dumps({
            "success": result.success,
            "failed": result.failed,
            "total": result.total,
            "elapsed": round(elapsed, 1),
        }))
    else:
        console.print(f"[bold blue]Creating {count} GitHub accounts...[/bold blue]")
        if proxy:
            console.print(f"  Proxy: {proxy[:30]}...")
        console.print()

        from src.utils.ui import make_progress, print_summary

        progress = make_progress()
        task = progress.add_task("Registering...", total=count)

        def on_progress(current: int, total: int) -> None:
            progress.update(task, completed=current)

        result = pipeline.run(count=count, resume=resume, on_progress=on_progress)
        progress.stop()
        elapsed = time.time() - start
        print_summary(count, result.success, result.failed, elapsed)


@app.command()
def status(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show account inventory status."""
    from config.settings import config
    from src.core.store import AccountStore
    from src.core.account import AccountStatus

    store = AccountStore(config.storage.accounts_file)

    total = store.count()
    created = store.count(AccountStatus.CREATED)
    verified = store.count(AccountStatus.VERIFIED)
    failed = store.count(AccountStatus.FAILED)

    if json_output:
        accounts = store.list_all()
        print(json.dumps({
            "total": total,
            "created": created,
            "verified": verified,
            "failed": failed,
            "accounts": [a.model_dump() for a in accounts],
        }))
    else:
        console.print("[bold]Account Inventory[/bold]")
        console.print(f"  Total:    {total}")
        console.print(f"  Created:  [green]{created}[/green]")
        console.print(f"  Verified: [blue]{verified}[/blue]")
        console.print(f"  Failed:   [red]{failed}[/red]")
        console.print()

        accounts = store.list_all()
        if accounts:
            from src.utils.ui import print_account_table
            print_account_table(
                [a.model_dump() for a in accounts[:20]],
                title=f"Accounts (showing {min(20, len(accounts))}/{len(accounts)})",
            )


@app.command()
def export(
    output: str = typer.Option("data/results/creds.txt", "-o", "--output", help="Output file"),
    format: str = typer.Option("creds", "-f", "--format", help="Format: creds/csv"),
):
    """Export accounts to file."""
    from config.settings import config
    from src.core.store import AccountStore
    from src.core.account import AccountStatus

    store = AccountStore(config.storage.accounts_file)

    if format == "creds":
        count = store.export_creds(output, AccountStatus.CREATED)
        console.print(f"[green]Exported {count} accounts to {output}[/green]")
    elif format == "csv":
        accounts = store.list_all(AccountStatus.CREATED)
        lines = ["email,password,username"]
        for a in accounts:
            lines.append(f"{a.email},{a.password},{a.username}")
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text("\n".join(lines), encoding="utf-8")
        console.print(f"[green]Exported {len(accounts)} accounts to {output}[/green]")
    else:
        console.print(f"[red]Unknown format: {format}[/red]")


@app.command("config")
def config_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show current configuration."""
    from config.settings import config

    if json_output:
        print(json.dumps({
            "email_provider": config.email.provider,
            "browser_headless": True,
            "proxy_url": config.proxy.url or "",
            "delay_base": config.pipeline.delay_base,
            "delay_jitter": config.pipeline.delay_jitter,
            "password": config.registration.password or "AutoGen2026!",
        }))
    else:
        console.print("[bold]Current Configuration[/bold]")
        console.print(f"  Email provider: {config.email.provider}")
        console.print(f"  LewatTok API:   {'***' if config.email.lewattok_api_key else 'NOT SET'}")
        console.print(f"  Supabase URL:   {config.email.supabase_url or 'NOT SET'}")
        console.print(f"  Browser:        camoufox (headless)")
        console.print(f"  Groq API:       {'***' if config.captcha.groq_api_key else 'NOT SET'}")
        console.print(f"  Proxy file:     {config.proxy.file}")
        console.print(f"  Accounts file:  {config.storage.accounts_file}")
        console.print(f"  Delay base:     {config.pipeline.delay_base}s")
        console.print(f"  Delay jitter:   {config.pipeline.delay_jitter}s")

        from src.proxy.manager import ProxyManager
        proxy_mgr = ProxyManager()
        stats = proxy_mgr.stats()
        console.print(f"  Proxies:        {stats['total']} total, {stats['healthy']} healthy")


@app.command("config-set")
def config_set(
    key: str = typer.Argument(..., help="Config key (e.g. email_provider, proxy_url)"),
    value: str = typer.Argument(..., help="Config value"),
):
    """Set a configuration value."""
    env_file = Path(".env")
    lines = env_file.read_text(encoding="utf-8").splitlines() if env_file.exists() else []

    # Map CLI keys to env var names
    key_map = {
        "email_provider": "EMAIL_PROVIDER",
        "proxy_url": "PROXY_URL",
        "proxy_file": "PROXY_FILE",
        "delay_base": "BATCH_DELAY_BASE",
        "delay_jitter": "BATCH_DELAY_JITTER",
        "password": "REGISTRATION_PASSWORD",
        "username_prefix": "USERNAME_PREFIX",
        "username_length": "USERNAME_LENGTH",
        "otp_timeout": "OTP_TIMEOUT",
        "max_retries": "MAX_RETRIES",
        "log_level": "LOG_LEVEL",
    }

    env_key = key_map.get(key, key.upper())
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{env_key}="):
            lines[i] = f"{env_key}={value}"
            found = True
            break

    if not found:
        lines.append(f"{env_key}={value}")

    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    console.print(f"[green]Set {env_key}={value}[/green]")


@app.command("proxy")
def proxy_cmd(
    action: str = typer.Argument(..., help="Action: list, add, remove, test"),
    url: Optional[str] = typer.Option(None, help="Proxy URL"),
    proxy_file: Optional[str] = typer.Option(None, "--proxy-file", help="Proxy file path"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Manage proxies."""
    from src.proxy.manager import ProxyManager
    from src.proxy.detect import detect_proxy_country

    if action == "list":
        mgr = ProxyManager(proxy_file=proxy_file)
        entries = mgr._entries
        if json_output:
            data = []
            for e in entries:
                data.append({
                    "url": e.url,
                    "country_code": e.country_code,
                    "country_name": e.country_name,
                    "healthy": e.is_healthy,
                })
            print(json.dumps(data))
        else:
            console.print(f"[bold]Proxies ({len(entries)} total)[/bold]")
            for e in entries[:20]:
                status = "[green]OK[/green]" if e.is_healthy else "[red]FAIL[/red]"
                console.print(f"  {status} {e.url[:50]}")

    elif action == "add" and url:
        proxy_file_path = Path("config/proxies.txt")
        proxy_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(proxy_file_path, "a", encoding="utf-8") as f:
            f.write(f"\n{url}")
        console.print(f"[green]Added proxy: {url[:50]}[/green]")

    elif action == "remove" and url:
        proxy_file_path = Path("config/proxies.txt")
        if proxy_file_path.exists():
            lines = proxy_file_path.read_text(encoding="utf-8").splitlines()
            lines = [l for l in lines if url not in l]
            proxy_file_path.write_text("\n".join(lines), encoding="utf-8")
            console.print(f"[green]Removed proxy: {url[:50]}[/green]")

    elif action == "test" and url:
        info = detect_proxy_country(url)
        console.print(f"Country: {info.country_name} ({info.country_code})")
        console.print(f"Latency: {info.latency_ms:.0f}ms")
        console.print(f"IP: {info.ip}")

    else:
        console.print("[red]Usage: proxy <list|add|remove|test> [--url URL][/red]")


@app.command("logs")
def logs_cmd(
    lines: int = typer.Option(100, "-n", "--lines", help="Number of log lines"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show recent log entries."""
    from config.settings import config

    log_file = Path(config.log.log_dir) / "github-auto.log"
    if not log_file.exists():
        if json_output:
            print("[]")
        else:
            console.print("[yellow]No log file found[/yellow]")
        return

    try:
        all_lines = log_file.read_text(encoding="utf-8").splitlines()
        recent = all_lines[-lines:]

        if json_output:
            entries = []
            for line in recent:
                parts = line.split(" | ", 3) if " | " in line else ["", "INFO", "", line]
                entries.append({
                    "timestamp": parts[0] if len(parts) > 0 else "",
                    "level": parts[1] if len(parts) > 1 else "INFO",
                    "module": parts[2] if len(parts) > 2 else "",
                    "message": parts[3] if len(parts) > 3 else line,
                })
            print(json.dumps(entries))
        else:
            console.print(f"[bold]Recent Logs ({len(recent)} lines)[/bold]")
            for line in recent[-20:]:
                console.print(f"  {line}")
    except Exception as exc:
        console.print(f"[red]Error reading logs: {exc}[/red]")


if __name__ == "__main__":
    app()
