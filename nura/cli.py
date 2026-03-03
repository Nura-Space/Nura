#!/usr/bin/env python3
"""Nura CLI - Command-line interface for Nura platform."""

import click
import asyncio


@click.group()
def main():
    """Nura - Universal Event-Driven AI Agent Platform"""
    pass


@main.command()
@click.option("--platform", default="feishu", help="Platform: feishu, wechat, slack")
@click.option("--config", default=None, help="Path to custom configuration file (JSON/TOML)")
def run(platform, config):
    """Run Nura agent with specified platform.

    Configuration is loaded from:
    - config/default.toml (global settings)
    - config/platforms/<platform>.toml (platform-specific settings)
    - Environment variables (FEISHU_*, VOLCENGINE_*, NURA_*)
    - .env file (if present)
    - Custom config file (if specified with --config)

    Examples:
        nura run --platform feishu
        nura run --config /path/to/config.json --platform feishu
    """
    if config:
        click.echo(f"Custom config not supported yet: {config}")
    if platform == "feishu":
        from nura.integrations.feishu.bot import run_feishu_bot, load_platform_config

        try:
            cfg = load_platform_config()
            click.echo("Using configuration from TOML + env vars")
            asyncio.run(run_feishu_bot(cfg))
        except Exception as e:
            click.echo(f"Failed to load configuration: {e}", err=True)
            click.echo("\nPlease ensure:")
            click.echo("  1. config/default.toml exists (copy from default.example.toml)")
            click.echo("  2. config/platforms/feishu.toml exists (copy from feishu.example.toml)")
            click.echo("  3. Or set environment variables (FEISHU_APP_ID, FEISHU_APP_SECRET)")
            raise click.Abort()
    else:
        click.echo(f"Platform {platform} not supported yet")


if __name__ == "__main__":
    main()
