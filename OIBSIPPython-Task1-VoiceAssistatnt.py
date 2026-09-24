from datetime import datetime
from threading import Lock
from urllib.parse import quote_plus
import webbrowser

import win32com.client
import speech_recognition as sr


speech_lock = Lock()


def speak(text):
    """Speak one complete message through the Windows SAPI directly

    A brand-new engine is created on every call because pyttsx3's SAPI5
    driver on Windows reliably speaks only once per engine instance --
    reusing one engine across multiple speak() calls causes later calls
    to silently produce no audio.
    """
    with speech_lock:
            engine = win32com.client.Dispatch("SAPI.SpVoice")
            engine.Volume = 100
            engine.Rate = 0
            engine.Speak(str(text))


def listen():
    """Capture one spoken command and convert it to text."""
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 0.8
    try:
        with sr.Microphone(sample_rate=44100) as source:
            print("Adjusting for ambient noise, please wait...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening... say something")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        speak(f"You said: {text}")
        return text
    except sr.WaitTimeoutError:
        speak("I did not hear anything. Please try again.")
    except sr.UnknownValueError:
        speak("Sorry, I could not understand what you said. Please repeat.")
    except sr.RequestError:
        speak("I cannot process your request right now. Please try again later.")
    except AttributeError:
        speak("Microphone support is not installed. Please install PyAudio.")
    except OSError:
        speak("I cannot access the microphone. Please check your microphone settings.")
    return None


def tell_time():
    current_time = datetime.now().strftime("%I:%M %p")
    speak(f"The current time is {current_time}.")


def tell_date():
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    speak(f"Today's date is {current_date}.")


def search_web(topic):
    """Open a Google search for the requested topic."""
    if not topic:
        speak("What would you like me to search for?")
        return
    speak(f"Searching the web for {topic}.")
    search_url = "https://www.google.com/search?q=" + quote_plus(topic)
    webbrowser.open(search_url)


def process_command(command):
    """Handle one command and return False only when the assistant should exit."""
    if not command:
        speak("I did not receive a command. Please try again.")
        return True

    command = command.lower().strip()
    exit_phrases = ("goodbye", "good bye", "exit", "quit", "stop", "bye", "end program")

    if command in exit_phrases or any(phrase in command for phrase in exit_phrases):
        speak("Goodbye! See you next time.")
        return False
    if command in ("hello", "hi", "hii") or "hello" in command:
        speak("Hello! Nice to meet you. How can I assist you today?")
        return True
    if "time" in command:
        tell_time()
        return True
    if "date" in command or "today" in command:
        tell_date()
        return True
    if command.startswith("search"):
        topic = command[len("search"):].strip()
        search_web(topic)
        return True

    speak("I do not know how to do that yet. Please try another command.")
    return True


def main():
    speak("Hello! I am your voice assistant. How can I help you today?")
    speak("You can ask for the time or date, say search followed by a topic, or say goodbye.")
    while True:
        try:
            if not process_command(listen()):
                break
        except (RuntimeError, OSError) as error:
            print(f"Loop error: {error}")
            speak("Something went wrong. I am ready to listen again.")


if __name__ == "__main__":
    main()