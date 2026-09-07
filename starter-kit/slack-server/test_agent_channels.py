import unittest

from agent_channels import resolve_agent
from personas import PERSONAS


class AgentChannelTests(unittest.TestCase):
    def test_all_eight_staff_keys_resolve(self):
        for number in range(1, 9):
            with self.subTest(number=number):
                self.assertEqual(resolve_agent(f"staff{number}"), f"staff{number}")
                self.assertEqual(resolve_agent(f"직원{number}"), f"staff{number}")

    def test_persona_display_names_resolve(self):
        for agent, persona in PERSONAS.items():
            with self.subTest(agent=agent):
                self.assertEqual(resolve_agent(persona["display_name"]), agent)

    def test_unknown_channel_uses_default(self):
        self.assertEqual(resolve_agent("등록되지-않은-채널"), "staff1")


if __name__ == "__main__":
    unittest.main()
