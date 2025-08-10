import assemblyai as aai
import json
from typing import Dict, Any
import os
import re

# Set your AssemblyAI API key
aai.settings.api_key = "37e88f4158d04c60bc975dad64be9b67"

class TranscriptionService:
    """Service for handling audio transcription using AssemblyAI"""
    
    def __init__(self):
        # Simplified config for better reliability
        self.config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.best,
            punctuate=True,
            format_text=True,
            # Remove summary features that might not work for short clips
        )
    
    def transcribe_audio(self, file_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file and return transcript with summary
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary containing transcript, summary, and other data
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file not found: {file_path}")
            
            # Start transcription
            transcriber = aai.Transcriber(config=self.config)
            transcript = transcriber.transcribe(file_path)
            
            if transcript.status == "error":
                raise RuntimeError(f"Transcription failed: {transcript.error}")
            
            # Create our own summary if AssemblyAI doesn't provide one
            transcript_text = transcript.text or "No transcript available"
            ai_summary = getattr(transcript, 'summary', None)
            
            # If no AI summary, create a simple one
            if not ai_summary:
                ai_summary = self.create_simple_summary(transcript_text)
            
            # Extract key information
            result = {
                "transcript": transcript_text,
                "summary": ai_summary,
                "chapters": [],
                "confidence": getattr(transcript, 'confidence', 0.0),
                "audio_duration": getattr(transcript, 'audio_duration', 0)
            }
            
            # Add chapters if available
            if hasattr(transcript, 'chapters') and transcript.chapters:
                result["chapters"] = [
                    {
                        "headline": chapter.headline,
                        "summary": chapter.summary,
                        "start": chapter.start,
                        "end": chapter.end
                    }
                    for chapter in transcript.chapters
                ]
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Transcription service error: {str(e)}")
    
    def create_simple_summary(self, transcript_text: str) -> str:
        """
        Create a simple summary from transcript text
        """
        if not transcript_text or len(transcript_text.strip()) < 10:
            return "Short audio clip with minimal content."
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', transcript_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 2:
            return f"Brief audio containing: {transcript_text[:100]}..."
        
        # Take first and last sentences for simple summary
        first_part = sentences[0]
        last_part = sentences[-1] if len(sentences) > 1 else ""
        
        summary = f"The audio discusses {first_part.lower()}"
        if last_part:
            summary += f" and concludes with {last_part.lower()}"
        
        return summary + "."
    
    def extract_action_items(self, transcript_text: str) -> list:
        """
        Extract action items from transcript (improved keyword-based approach)
        """
        if not transcript_text:
            return []
            
        action_keywords = [
            "need to", "should", "must", "have to", "will",
            "action", "todo", "to do", "follow up", "next step",
            "assign", "responsible", "deadline", "schedule",
            "contact", "email", "call", "meeting", "send",
            "remember", "don't forget", "make sure"
        ]
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', transcript_text)
        action_items = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 5:  # Skip very short sentences
                continue
                
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in action_keywords):
                # Clean up the sentence
                clean_sentence = sentence.capitalize()
                if not clean_sentence.endswith('.'):
                    clean_sentence += '.'
                action_items.append(clean_sentence)
        
        # If no action items found, create some based on content
        if not action_items and transcript_text:
            if "meeting" in transcript_text.lower():
                action_items.append("Follow up on meeting discussion.")
            elif "call" in transcript_text.lower():
                action_items.append("Review call notes and next steps.")
            else:
                action_items.append("Review recording content for further action.")
        
        return action_items[:5]  # Return max 5 action items
    
    def extract_key_points(self, summary: str, transcript: str = "") -> list:
        """
        Extract key points from summary and transcript
        """
        points = []
        
        # Extract from summary
        if summary:
            # Split by common delimiters
            summary_points = re.split(r'[.!?;]+', summary)
            for point in summary_points:
                point = point.strip()
                if len(point) > 15:  # Filter out very short points
                    clean_point = point.capitalize()
                    if not clean_point.endswith('.'):
                        clean_point += '.'
                    points.append(clean_point)
        
        # If we don't have enough points, extract from transcript
        if len(points) < 3 and transcript:
            transcript_sentences = re.split(r'[.!?]+', transcript)
            for sentence in transcript_sentences[:3]:  # Take first 3 sentences
                sentence = sentence.strip()
                if len(sentence) > 20:
                    clean_sentence = sentence.capitalize()
                    if not clean_sentence.endswith('.'):
                        clean_sentence += '.'
                    points.append(clean_sentence)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_points = []
        for point in points:
            if point.lower() not in seen:
                seen.add(point.lower())
                unique_points.append(point)
        
        return unique_points[:5]  # Return max 5 key points
