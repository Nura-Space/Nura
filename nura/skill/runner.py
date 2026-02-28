import os
from pathlib import Path

from nura.agent.toolcall import ToolCallAgent
from nura.skill.types import Skill


class SkillRunner:
    @staticmethod
    async def run_skill(skill: Skill, user_input: str) -> str:
        """
        Executes a skill using the Manus agent.

        Args:
            skill: The skill to execute.
            user_input: The input from the user.

        Returns:
            The result of the agent execution (only the final step output).
        """
        # Get skill directory from file_path
        skill_dir = str(Path(skill.file_path).parent.resolve())

        # Set SKILL_DIR as environment variable for subagent
        os.environ["SKILL_DIR"] = skill_dir

        # Build skill system prompt with instruction
        system_prompt = (
            f"你是一个技能执行助手。请严格按照以下技能描述按步骤执行任务。\n\n"
            f"{skill.content}"
        )

        # Instantiate Manus agent - override system_prompt with skill content only
        agent = ToolCallAgent(system_prompt=system_prompt)

        # Execute the agent
        result = await agent.run(user_input)

        # Extract the second-to-last step output, since the last step is
        # typically a terminate tool call with no useful summary.
        lines = result.split("\n")
        step_blocks: list[list[str]] = []
        for line in lines:
            if line.startswith("Step "):
                step_blocks.append([line])
            elif step_blocks:
                step_blocks[-1].append(line)

        if len(step_blocks) >= 2:
            return "\n".join(step_blocks[-2][1:]).strip()
        elif step_blocks:
            return "\n".join(step_blocks[-1][1:]).strip()
        return result
