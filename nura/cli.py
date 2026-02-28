#!/usr/bin/env python3
"""Nura CLI - Command-line interface for Nura platform."""

import click
import json
import asyncio


@click.group()
def main():
    """Nura - Universal Event-Driven AI Agent Platform"""
    pass


@main.command()
@click.option("--config", required=True, help="Path to config.json")
@click.option("--platform", default="feishu", help="Platform: feishu, wechat, slack")
def run(config, platform):
    """Run Nura agent with specified platform"""
    with open(config) as f:
        cfg = json.load(f)

    if platform == "feishu":
        from nura.integrations.feishu.bot import run_feishu_bot

        asyncio.run(run_feishu_bot(cfg))
    else:
        click.echo(f"Platform {platform} not supported yet")


if __name__ == "__main__":
    main()
