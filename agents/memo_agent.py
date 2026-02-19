import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def get_investment_advice(user_question):
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""
                당신은 투자 초보자를 돕는 친절한 투자 보조 AI입니다.
                전문 용어는 쉽게 설명하고, 명확하고 간결하게 답변해주세요.
                
                질문: {user_question}
                """
            }
        ]
    )
    return message.content[0].text