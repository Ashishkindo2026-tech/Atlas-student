from goals.goal_manager import GoalManager
from brain.planner import Planner


class ReasoningEngine:

    def think(
        self,
        user_input,
        memory,
        llm,
        recent_history,
        personality
    ):

        goal_manager = GoalManager()

        text = user_input.lower()

        # NAME MEMORY

        if text.startswith("my name is"):

            name = user_input[11:].strip()

            memory.remember("name", name)

            return f"Nice to meet you, {name}."

        elif "what is my name" in text:

            name = memory.recall("name")

            if name:
                return f"Your name is {name}."

            return "I do not know your name yet."

        # FAVORITE COLOR

        elif text.startswith("my favorite color is"):

            color = user_input[20:].strip()

            memory.remember("favorite_color", color)

            return f"I will remember that your favorite color is {color}."

        elif (
            "what is my favorite color" in text
            or
            "what is my favorite colour" in text
        ):

            color = memory.recall("favorite_color")

            if color:
                return f"Your favorite color is {color}."

            return "I do not know your favorite color."

        # FAVORITE SUBJECT

        elif text.startswith("my favorite subject is"):

            subject = user_input[22:].strip()

            memory.remember("favorite_subject", subject)

            return f"I will remember that your favorite subject is {subject}."

        elif "what is my favorite subject" in text:

            subject = memory.recall("favorite_subject")

            if subject:
                return f"Your favorite subject is {subject}."

            return "I do not know your favorite subject."

        # GOALS

        elif text.startswith("my goal is"):

            goal = user_input[10:].strip()

            goal_manager.add_goal(goal)

            planner = Planner()

            plan = planner.create_plan(goal)

            result = f"Goal saved: {goal}\n\n"

            result += "Suggested Plan:\n\n"

            for i, step in enumerate(plan, 1):

                result += f"{i}. {step}\n"

            return result

        elif "what are my goals" in text:

            goals = goal_manager.get_goals()

            if not goals:

                return "You currently have no saved goals."

            result = "Your active goals:\n\n"

            for i, goal in enumerate(goals, 1):

                result += f"{i}. {goal}\n"

            return result

        # IMPORTANT MEMORIES

        elif (
            "important memories" in text
            or
            "show important memories" in text
            or
            "what do you remember" in text
            or
            "show memories" in text
        ):

            memories = memory.get_important_memories()

            if not memories:

                return "I do not have any important memories yet."

            result = "\n=== IMPORTANT MEMORIES ===\n\n"

            for i, item in enumerate(memories, 1):

                result += f"{i}. {item}\n"

            result += f"\nTotal Memories: {len(memories)}"

            return result

        # PROFILE

        elif "show profile" in text:

            name = memory.recall("name") or "Unknown"
            color = memory.recall("favorite_color") or "Unknown"
            subject = memory.recall("favorite_subject") or "Unknown"

            return f"""
=== USER PROFILE ===

Name: {name}
Favorite Color: {color}
Favorite Subject: {subject}
"""

        # DEFAULT LLM RESPONSE

        name = memory.recall("name") or "Unknown"
        color = memory.recall("favorite_color") or "Unknown"
        subject = memory.recall("favorite_subject") or "Unknown"

        prompt = f"""
You are Atlas.

PERSONALITY

Name: {personality.get('name', 'Atlas')}
Creator: {personality.get('creator', 'Ashish')}
Tone: {personality.get('tone', 'friendly')}
Curiosity: {personality.get('curiosity', 8)}
Humor: {personality.get('humor', 6)}
Helpfulness: {personality.get('helpfulness', 10)}
Calmness: {personality.get('calmness', 10)}
Kindness: {personality.get('kindness', 9)}
Confidence: {personality.get('confidence', 8)}
Creativity: {personality.get('creativity', 8)}
Intelligence: {personality.get('intelligence', 9)}
Loyalty: {personality.get('loyalty', 10)}
Patience: {personality.get('patience', 10)}
Empathy: {personality.get('empathy', 8)}
Casualness: {personality.get('casualness', 8)}

USER PROFILE

Name: {name}
Favorite Color: {color}
Favorite Subject: {subject}

RECENT CONVERSATION

{recent_history}

CURRENT MESSAGE

{user_input}

Respond naturally as Atlas.
"""

        return llm.generate(prompt)