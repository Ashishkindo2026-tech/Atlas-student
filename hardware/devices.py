"""Device stubs used to test Atlas hardware integration without real devices."""

class SimulatedSpeaker:
    name = "simulated_speaker"
    capability = "audio_output"

    def execute(self, action: str, **kwargs):
        if action != "speak":
            raise ValueError(f"Unsupported speaker action: {action}")
        return {"spoken": str(kwargs.get("text", ""))}


class SimulatedMicrophone:
    name = "simulated_microphone"
    capability = "audio_input"

    def execute(self, action: str, **kwargs):
        if action != "listen":
            raise ValueError(f"Unsupported microphone action: {action}")
        return {"text": str(kwargs.get("text", ""))}
