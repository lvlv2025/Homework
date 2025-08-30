from openai import OpenAI

def get_chat_data(messages_list:list):

    client = OpenAI(api_key="", base_url="https://api.deepseek.com")
    response = client.chat.completions.create(model="deepseek-chat", messages=messages_list, stream=False)
    #print(response.choices[0].message.content)
    return response.choices[0].message.content
