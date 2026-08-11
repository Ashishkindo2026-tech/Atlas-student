import datetime


class StudentBrain:

    def __init__(self, model):
        self.model = model

        self.system_prompt = """
You are Atlas Student, a friendly AI study companion.

Your personality:
- Patient
- Friendly
- Motivating
- Simple explanations
- Never rude
- Helps students learn

Rules:
1. Explain difficult topics in easy language.
2. Use examples from daily life.
3. For school questions:
   - Give step-by-step explanations.
   - Highlight important points.
4. For exams:
   - Provide revision tips.
   - Create short notes.
5. Do not overload the student with unnecessary information.
6. Ask questions when the student is confused.

Subjects you help:
Physics, Chemistry, Biology, Mathematics,
Computer Science, English, History, Geography.

Student level:
Class 11.

Your goal:
Make learning easier and enjoyable.
"""

    def think(self, question, history=[]):

        prompt = f"""
{self.system_prompt}

Previous conversation:
{history[-5:]}

Student:
{question}
class AtlasStudent:

    def __init__(self):
        self.modes = {
            "homework": HomeworkMode(),
            "revision": RevisionMode(),
            "exam": ExamMode(),
            "timetable": TimeTable(),
            "progress": ProgressTracker()
        }


    def run(self, command):

        if "homework" in command:
            return self.modes["homework"]

        elif "revision" in command:
            return self.modes["revision"]

        elif "exam" in command:
            return self.modes["exam"]

        else:
            return "I am ready to help you study 😊"
Atlas Student:
"""

        response = self.model.generate(prompt)

        return response


    def greeting(self):

        hour = datetime.datetime.now().hour

        if hour < 12:
            return "Good morning 😊 Ready for today's learning?"

        elif hour < 17:
            return "Good afternoon 📚 Let's study something new!"

        else:
            return "Good evening 🌙 Time for revision?"
        
