import typer
from .commands import trigger_workflow_dispatch
from pathlib import Path
import configparser
from rich.console import Console
from rich.table import Table

HOME_DIR = Path.home()
OB_CONFIG_PATH = HOME_DIR / ".ob_config"

# --- Helper Functions ---

def get_config():
    """读取并返回配置解析器对象。"""
    if not OB_CONFIG_PATH.exists():
        typer.secho(f"配置文件不存在，请先运行 'ob init'", fg=typer.colors.YELLOW)
        raise typer.Exit(1)
    conf = configparser.ConfigParser()
    conf.read(OB_CONFIG_PATH, encoding="utf-8")
    return conf

def write_config(conf: configparser.ConfigParser):
    """将配置写回文件。"""
    with open(OB_CONFIG_PATH, "w", encoding="utf-8") as f:
        conf.write(f)

# --- Typer App Setup ---

app = typer.Typer(name="ob", no_args_is_help=True, rich_markup_mode="markdown")

@app.command()
def init():
    """
    初始化配置文件。
    """
    OB_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    OB_CONFIG_PATH.touch(exist_ok=True)
    typer.secho(f"✓ 配置文件已创建: {OB_CONFIG_PATH}", fg=typer.colors.GREEN)

table_app = typer.Typer(help="管理使用 autoTable 的 Issue。")
app.add_typer(table_app, name="table")

# --- Table Commands ---

@table_app.command("update", help="更新 autoTable 管理的 issue。")
def table_update(
    owner_repo: str | None = typer.Argument(None, help="仓库地址 (格式: owner/repo)。"),
    issue_number: int | None = typer.Argument(None, help="Issue 编号。"),
    alias: str | None = typer.Option(None, "--alias", "-a", help="使用别名代替直接参数。"),
    target_repo: str = typer.Option("ooooo-create/ob", help="运行 workflow 的目标仓库。"),
    token: str | None = typer.Option(None, help="GitHub Personal Access Token。"),
):
    """
    更新 autoTable 管理的 issue。
    
    可以通过别名或直接提供仓库和 issue 编号来使用。
    """
    # 优先使用别名
    if alias:
        conf = get_config()
        if not conf.has_section(alias):
            typer.secho(f"✗ 错误: 别名 '{alias}' 不存在。", fg=typer.colors.RED)
            raise typer.Exit(1)
        
        owner_repo = conf.get(alias, "repo")
        issue_number = int(conf.get(alias, "issue_number"))
    
    # 使用直接提供的参数
    elif owner_repo and issue_number:
        pass  # 直接使用提供的参数
    
    # 参数不足
    else:
        typer.secho("✗ 错误: 请提供仓库地址和 issue 编号，或使用 --alias。", fg=typer.colors.RED)
        typer.echo("\n使用示例:")
        typer.echo("  ob table update PaddlePaddle/Paddle 63683")
        typer.echo("  ob table update --alias 'typos 升级到 1.38.1'")
        raise typer.Exit(1)

    typer.echo(f"🚀 正在触发 {owner_repo}#{issue_number} 的更新...")
    success = trigger_workflow_dispatch(
        repo_name=target_repo,
        workflow_id="autotable-update.yml",
        ref="main",
        inputs={
            "owner_repo": owner_repo,
            "issue_number": str(issue_number),
        },
        token=token,
    )
    if success:
        typer.secho("✓ 更新任务已成功触发！", fg=typer.colors.GREEN)

@table_app.command("show", help="展示所有被 autoTable 管理的 issue。")
def table_show():
    """以表格形式显示所有配置的 issue。"""
    conf = get_config()
    if not conf.sections():
        typer.secho("🤔 配置文件中没有找到任何 issue 配置。", fg=typer.colors.YELLOW)
        return

    table = Table("别名 (Alias)", "仓库 (Repo)", "Issue 编号")
    for section in conf.sections():
        repo = conf.get(section, "repo", fallback="N/A")
        issue_number = conf.get(section, "issue_number", fallback="N/A")
        table.add_row(section, repo, issue_number)

    console = Console()
    console.print(table)

@table_app.command("add", help="添加一个新的 issue 配置。")
def table_add(
    alias: str = typer.Argument(..., help="配置的唯一别名。"),
    repo: str = typer.Argument(..., help="仓库地址 (格式: owner/repo)。"),
    issue_number: int = typer.Argument(..., help="Issue 编号。"),
):
    """添加一个新的 issue 配置到 .ob_config 文件。"""
    conf = get_config()
    if conf.has_section(alias):
        typer.secho(f"✗ 错误: 别名 '{alias}' 已存在。", fg=typer.colors.RED)
        raise typer.Exit(1)

    conf.add_section(alias)
    conf.set(alias, "repo", repo)
    conf.set(alias, "issue_number", str(issue_number))
    write_config(conf)
    typer.secho(f"✓ 成功添加配置 '{alias}'。", fg=typer.colors.GREEN)

@table_app.command("remove", help="根据别名删除一个 issue 配置。")
def table_remove(alias: str = typer.Argument(..., help="要删除的配置别名。")):
    """从 .ob_config 文件中删除一个 issue 配置。"""
    conf = get_config()
    if not conf.has_section(alias):
        typer.secho(f"✗ 错误: 别名 '{alias}' 不存在。", fg=typer.colors.RED)
        raise typer.Exit(1)

    conf.remove_section(alias)
    write_config(conf)
    typer.secho(f"✓ 成功删除配置 '{alias}'。", fg=typer.colors.GREEN)

if __name__ == "__main__":
    app()
