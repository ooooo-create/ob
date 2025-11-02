"""Commands for managing GitHub workflows."""

import os
from typing import Any

from github import Auth, Github


def trigger_workflow_dispatch(
    repo_name: str,
    workflow_id: str,
    ref: str = "main",
    inputs: dict[str, Any] | None = None,
    token: str | None = None,
) -> bool:
    """
    触发 GitHub workflow_dispatch 事件的通用方法。

    Args:
        repo_name: 仓库名称，格式为 "owner/repo"
        workflow_id: workflow 文件名（如 "autotable-update.yml"）或 workflow ID
        ref: 要运行 workflow 的分支、标签或 commit SHA，默认为 "main"
        inputs: workflow 的输入参数字典
        token: GitHub Personal Access Token，如果不提供则从环境变量 GITHUB_TOKEN 或 PAT 读取

    Returns:
        bool: 成功返回 True，失败返回 False

    Raises:
        ValueError: 如果找不到有效的 GitHub token
        Exception: 如果触发 workflow 失败

    Example:
        >>> trigger_workflow_dispatch(
        ...     repo_name="owner/repo",
        ...     workflow_id="deploy.yml",
        ...     ref="main",
        ...     inputs={"environment": "production", "version": "1.0.0"}
        ... )
        True
    """
    # 获取 GitHub token
    if token is None:
        token = os.getenv("GITHUB_TOKEN") or os.getenv("PAT")
        if not token:
            raise ValueError(
                "GitHub token not found. Please provide token parameter or set GITHUB_TOKEN/PAT environment variable."
            )

    # 创建 GitHub 实例
    auth = Auth.Token(token)
    g = Github(auth=auth)

    try:
        # 获取仓库
        repo = g.get_repo(repo_name)

        # 获取 workflow
        workflow = repo.get_workflow(workflow_id)

        # 触发 workflow_dispatch
        success = workflow.create_dispatch(ref=ref, inputs=inputs or {})

        if success:
            print(f"✓ Successfully triggered workflow '{workflow_id}' on {repo_name}@{ref}")
            if inputs:
                print(f"  Inputs: {inputs}")
            return True
        else:
            print(f"✗ Failed to trigger workflow '{workflow_id}' on {repo_name}@{ref}")
            return False

    except Exception as e:
        print(f"✗ Error triggering workflow: {e}")
        raise
    finally:
        g.close()
