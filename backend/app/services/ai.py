import json
from openai import OpenAI
from app.config import settings

class AIService:
    def __init__(self):
        self.api_key = settings.openai_api_key
        # Initialise client if key is provided, otherwise let it fail on trigger
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def transcribe_audio(self, file_path: str) -> str:
        """
        Transcribes audio file to text using OpenAI Whisper API
        """
        if not self.client:
            raise ValueError("OPENAI_API_KEY is not configured in settings.")
            
        with open(file_path, "rb") as audio_file:
            # response_format="text" directly returns a string
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="text"
            )
        return transcript

    def summarize_notes(self, transcript: str) -> dict:
        """
        Generates structured SOAP Notes from transcript
        """
        if not self.client:
            raise ValueError("OPENAI_API_KEY is not configured in settings.")

        prompt = f"""
        You are a medical scribe. Convert the following clinician-patient interaction transcript into a structured SOAP Note document response IN JSON FORMAT.
        
        Transcript: 
        {transcript}
        
        The JSON response MUST strictly follow this structure:
        {{
            "overview": "A detailed paragraph describing meeting overview and symptoms",
            "medications": [ "string listing medication and dosage" ],
            "diagnoses": [ "string listing condition" ],
            "action_items": [ "string listing next steps for patient or doctor" ],
            "urgency_tag": "normal" | "follow-up" | "referral" | "prescription" | "urgent"
        }}
        """

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        
        result = response.choices[0].message.content
        if not result:
            raise ValueError("Received empty response from OpenAI Completion.")
            
        return json.loads(result)
