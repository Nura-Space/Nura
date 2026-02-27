"""
Skills Tool - 使用 SkillQueue 异步执行 Skill

替代 OpenManus 的同步执行方式:
- 将任务放入 SkillQueue (非阻塞)
- 后台 SkillExecutor 异步执行
- LLM 总结结果后注入/队列
"""

from typing import Any

from pydantic import ConfigDict

from nura.tool.base import BaseTool
from nura.core.skill_queue import SkillTask, SkillStatus, get_skill_queue


class Skills(BaseTool):
    """
    Tool for executing skills asynchronously with progressive disclosure.

    Flow:
    1. Puts task to SkillQueue (non-blocking)
    2. Returns "Skill 已加入队列" immediately
    3. Background SkillExecutor runs the skill
    4. LLM summarizes the result
    5. SkillAnnounceHandler injects/queues the result
    """

    model_config = ConfigDict(extra="allow")

    name: str = "skills"
    description: str = (
        "Execute a skill to perform specific tasks. Use this tool when you need to use a skill."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "skill_name": {
                "type": "string",
                "description": "The name of the skill to execute.",
            },
            "user_input": {
                "type": "string",
                "description": "The input for the skill execution.",
            },
        },
        "required": ["skill_name", "user_input"],
    }

    def __init__(self, **data):
        super().__init__(**data)
        self._skill_queue = get_skill_queue()

    async def execute(
        self, skill_name: str, user_input: str, blocking: bool = None
    ) -> Any:
        """Execute skill - either blocking or non-blocking based on skill configuration.

        Args:
            skill_name: The name of the skill to execute.
            user_input: The input for the skill execution.
            blocking: Override the blocking behavior. If None, uses skill's configuration.
        """
        from nura.skill import get_skill_manager

        # Validate skill exists
        skill_manager = get_skill_manager()
        skill = skill_manager.get_skill(skill_name)

        if not skill:
            available = ", ".join([s.name for s in skill_manager.list_skills()])
            return self.fail_response(
                f"Skill '{skill_name}' not found. Available skills: {available}"
            )

        if not skill.available:
            missing = (
                skill_manager._get_missing_requirements(skill.requires)
                if skill.requires
                else "unknown"
            )
            return self.fail_response(
                f"Skill '{skill_name}' is not available. Missing requirements: {missing}"
            )

        # Determine blocking mode: use parameter if provided, otherwise use skill's config
        is_blocking = blocking if blocking is not None else skill.blocking

        if is_blocking:
            return await self._run_blocking(skill, user_input)
        else:
            return await self._run_async(skill, user_input)

    async def _run_blocking(self, skill, user_input: str) -> Any:
        """Execute skill synchronously and wait for result."""
        from nura.skill.runner import SkillRunner

        try:
            result = await SkillRunner.run_skill(skill, user_input)
            return self.success_response(result)
        except Exception as e:
            return self.fail_response(f"Skill execution failed: {str(e)}")

    async def _run_async(self, skill, user_input: str) -> Any:
        """Execute skill asynchronously by putting it into the queue."""
        from nura.services.base import ClientFactory

        # Get current session/chat ID from the current platform client
        client = ClientFactory.get_current_client()
        session_id = client.chat_id if client and client.chat_id else "default"

        # Create task and put to queue (non-blocking)
        task = SkillTask(
            skill_name=skill.name,
            user_input=user_input,
            session_id=session_id,
            status=SkillStatus.PENDING,
        )

        # Put to queue - this is non-blocking
        success = await self._skill_queue.put(task)

        if success:
            return self.success_response(
                f"✅ 技能「{skill.name}」已启动，正在异步执行中。\n"
                f"请继续聊天，稍后即可收到结果。"
            )
        else:
            return self.fail_response("Skill queue is busy, please try again later.")
