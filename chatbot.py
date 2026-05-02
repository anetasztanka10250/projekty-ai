from openai import OpenAI

client = OpenAI(
    api_key=input("Wpisz swój klucz API: "),
    base_url="https://api.groq.com/openai/v1"
)

print("Chatbot AI gotowy! Wpisz 'koniec' żeby zakończyć.")

while True:
    pytanie = input("Ty: ")
    if pytanie == "koniec":
        break
    
    odpowiedz = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": pytanie}]
    )
    
    print("AI:", odpowiedz.choices[0].message.content)