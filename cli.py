"""CLI entry point for github-auto."""

from __future__ import annotations

import time
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
    driver: str = typer.Option("camoufox", "--driver", help="Browser driver (camoufox/patchright)"),
    headless: bool = typer.Option(False, "--headless", help="Run browser headless"),
    password: Optional[str] = typer.Option(None, "--password", help="Password for all accounts"),
    email_provider: Optional[str] = typer.Option(None, "--email-provider", help="Email provider (lewattok/supabase)"),
    delay: Optional[float] = typer.Option(None, "--delay", help="Delay between accounts (seconds)"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug screenshots"),
    resume: bool = typer.Option(False, "--resume", help="Resume from checkpoint"),
):
    """Create GitHub accounts."""
    from config.settings import config
    from src.core.pipeline import Pipeline
    from src.core.store import AccountStore
    from src.email.manager import EmailManager
    from src.proxy.manager import ProxyManager
    from providers.github import GithubProvider
    from src.utils.ui import make_progress, print_summary

    # Override config from CLI
    if proxy:
        config.proxy.__init__ = lambda: None  # bypass frozen
    if delay:
        pass  # handled by pipeline

    store = AccountStore(config.storage.accounts_file)
    email_mgr = EmailManager(email_provider)
    proxy_mgr = ProxyManager(
        proxy_file=proxy_file,
        static_proxy=proxy,
    )

    provider = GithubProvider(
        email_manager=email_mgr,
        proxy_manager=proxy_mgr,
        driver=driver,
        headless=headless,
        debug_screenshots=debug,
    )

    pipeline = Pipeline(
        store=store,
        worker=provider.create_account,
        delay_base=delay or config.pipeline.delay_base,
        delay_jitter=config.pipeline.delay_jitter,
        checkpoint_file=config.pipeline.checkpoint_file,
    )

    console.print(f"[bold blue]Creating {count} GitHub accounts...[/bold blue]")
    if proxy:
        console.print(f"  Proxy: {proxy[:30]}...")
    console.print(f"  Driver: {driver}")
    console.print(f"  Headless: {headless}")
    console.print()

    start = time.time()
    progress = make_progress()
    task = progress.add_task("Registering...", total=count)

    def on_progress(current: int, total: int) -> None:
        progress.update(task, completed=current)

    result = pipeline.run(
        count=count,
        resume=resume,
        on_progress=on_progress,
    )

    progress.stop()
    print_summary(count, result.success, result.failed, time.time() - start)


@app.command()
def status():
    """Show account inventory status."""
    from config.settings import config
    from src.core.store import AccountStore
    from src.core.account import AccountStatus
    from src.utils.ui import print_account_table

    store = AccountStore(config.storage.accounts_file)

    total = store.count()
    created = store.count(AccountStatus.CREATED)
    verified = store.count(AccountStatus.VERIFIED)
    failed = store.count(AccountStatus.FAILED)

    console.print("[bold]Account Inventory[/bold]")
    console.print(f"  Total:    {total}")
    console.print(f"  Created:  [green]{created}[/green]")
    console.print(f"  Verified: [blue]{verified}[/blue]")
    console.print(f"  Failed:   [red]{failed}[/red]")
    console.print()

    accounts = store.list_all()
    if accounts:
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
        from pathlib import Path
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text("\n".join(lines), encoding="utf-8")
        console.print(f"[green]Exported {len(accounts)} accounts to {output}[/green]")
    else:
        console.print(f"[red]Unknown format: {format}[/red]")


@app.command()
def config_check():
    """Show current configuration."""
    from config.settings import config

    console.print("[bold]Current Configuration[/bold]")
    console.print(f"  Email provider: {config.email.provider}")
    console.print(f"  LewatTok API:   {'***' if config.email.lewattok_api_key else 'NOT SET'}")
    console.print(f"  Supabase URL:   {config.email.supabase_url or 'NOT SET'}")
    console.print(f"  Browser driver: {config.browser.driver}")
    console.print(f"  Browser headless: {config.browser.headless}")
    console.print(f"  Groq API:       {'***' if config.captcha.groq_api_key else 'NOT SET'}")
    console.print(f"  Proxy file:     {config.proxy.file}")
    console.print(f"  Accounts file:  {config.storage.accounts_file}")
    console.print(f"  Delay base:     {config.pipeline.delay_base}s")
    console.print(f"  Delay jitter:   {config.pipeline.delay_jitter}s")


if __name__ == "__main__":
    app()
