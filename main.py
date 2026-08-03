from veles.core.brain import ask_veles
from veles.memory.memory import remember
from veles.tts.speak import speak


VOICE_OUTPUT_ENABLED = True


print("====================")
print("     VELES ONLINE")
print("====================")


while True:

    question = input("\nTI: ")

    if question.lower() in ["exit", "quit", "izlaz"]:
        print("Veles offline.")
        break

    result = ask_veles(question)

    print("\nVELES:")
    print(result["answer"])

    if VOICE_OUTPUT_ENABLED:
        try:
            speak(result["answer"])
        except Exception as e:
            print(f"[veles] Glasovni izlaz nije uspeo: {e}")

    suggestion = result.get("suggested_memory")
    if suggestion:
        confirm = input(
            f"\n[Veles predlaže da zapamti: {suggestion['key']} = {suggestion['value']}] "
            f"Da sačuvam? (da/ne): "
        ).strip().lower()
        if confirm == "da":
            remember(suggestion["key"], suggestion["value"])
            print("Sačuvano.")
