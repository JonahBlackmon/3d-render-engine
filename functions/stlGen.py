import os
from openai import OpenAI
from dotenv import load_dotenv

def GPTQuestion(query):
    #Loads and sets OpenAI API Key
    load_dotenv()
    api_key = os.getenv('OPENAI_KEY')

    client = OpenAI(api_key=api_key)

    #User question
    shape = query

    #Sets settings for OpenAI, we are using gpt-4o-mini, with a temp of 0
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
        {"role": "system", "content": '''
         You are an engieering assistant who's only purpose is to write stl file in a text format. The most important
         thing is that you say absolutely nothing else aside from the stl file, and you must make sure, without any doubt
         that the file you generated matches the users input exactly. You MUST follow every direction for determining which shape
         to generate for the user, and you must stick to fundamental geometry, for example: cubes, prisms, etc. you must interpret what the user
         is asking you to generate and give a resposne that exactly matches the dimensions specified because these stl files will
         be used in LIFE SAVING circumstances. You will perform perfect and the user will settle for nothing less.'''},
        {"role": "user", "content": f"{shape}"}
    ],
    temperature=0
    )

    #Saves ChatGPTs response to a variable
    AIresponse = completion.choices[0].message.content

    print(AIresponse)
    return AIresponse