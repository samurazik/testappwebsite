from langchain.agents import AgentType, initialize_agent, load_tools
from langchain.callbacks import StreamlitCallbackHandler
from langchain.callbacks.base import BaseCallbackHandler
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains.llm import LLMChain
from langchain.schema import ChatMessage
from langchain.llms import OpenAI
from datetime import timedelta
from datetime import datetime
import streamlit as st
from PIL import Image
import datetime as dt
import requests
import asyncio
import base64
import time
import json
import urllib.request

st.set_page_config(page_title="Dater", page_icon="🌌️", layout="wide", initial_sidebar_state="expanded")
container = st.container()
img = Image.open("./Backgrounds/LOGO.jpg")
img = img.resize((300, 75))
container.image(img)

openai_api_key = "sk-RnGKIPPPQ_LyjszViG72N-H9oj4sUjVSwtHdGMU7kZT3BlbkFJIKauUeLelBXvf0C_NFagaKl6UO61Jg9GkSOPbFfKEA"

class Background:
    def __init__(self, img):
        self.img = img

    def set_back_side(self):
        side_bg_ext = 'png'
        side_bg = self.img

        st.markdown(
            f"""
            <style>
                [data-testid="stSidebar"] > div:first-child {{
                    background: url(data:image/{side_bg_ext};base64,{base64.b64encode(open(side_bg, "rb").read()).decode()});
                }}
            </style>
            """,
            unsafe_allow_html=True,
        )

class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)

class Fundamental:
    def __init__(self):
        self.query = ("Please, give me an exhaustive fundamental analysis about the companies that you find in the documented knowledge. "
                      "I want to know the pros and cons of a long-term investment. Please, base your answer on what you know about the company, "
                      "but also on what you find useful about the documented knowledge. I want you to also give me your opinion on whether it is "
                      "worth investing in that company given the fundamental analysis you make. If you conclude that it is actually wise to invest "
                      "in a given company, or in multiple companies (focus only on the ones in the documented knowledge), then come up with some "
                      "strategies that I could follow to make the best out of my investments.")
        self.llm = OpenAI(model_name="gpt-4o", temperature=0, streaming=True, api_key=openai_api_key)
        self.tools = load_tools(["ddg-search"])
        self.agent = initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=False,
            handle_parsing_errors=True  # Added handle_parsing_errors parameter here
        )
        self.prompt_template = " stock symbol(s). Return only the symbols separated by spaces. Don't add any type of punctuation. If you already know the answer, there is no need to search for it on DuckDuckGo"
        self.DEFAULT_TEMPLATE = """The following is a friendly conversation between a human and an AI. The
        AI is an AI-powered fundamental analyst. It uses Documented Information to give fundamental insights on an asset determined by the user. It is specific and gives full relevant
        perspective to let the user know if it is worth making an investment in a certain asset and can also build intelligent strategies with the given information, as well as from intel that it
        already knows, or will generate. Take into account that the documented knowledge comes in the next structure. **Title:** (Message of the Title), **Description:** (Message of the
        Description)\n\n, and so on. All articles from the documented knowledge have a title and a description (both of which are separated by commas), and all articles are separated with the \n\n
        command between one another.

        Documented Information:
        {docu_knowledge},

        (You do not need to use these pieces of information if not relevant)

        Current conversation:
        Human: {input}
        AI-bot:"""

    async def get_stock_symbol(self, company_name):
        st_callback = StreamlitCallbackHandler(st.container())
        search_results = self.agent.run(company_name + self.prompt_template, callbacks=[st_callback])
        symbols = search_results.split(" ")
        return symbols

    def get_gnews_api(self):
        url = "https://gnews.io/api/v4/top-headlines?lang=en&token=<API_KEY>"
        response = requests.get(url)
        news = response.json()
        return news

    def get_gnews_api_spec(self, search_term):
        url = f"https://gnews.io/api/v4/search?q={search_term}&token=<API_KEY>"
        response = requests.get(url)
        news = response.json()
        return news

    def get_response(self, user_message, docu_knowledge, temperature=0):
        PROMPT = PromptTemplate(input_variables=['input', 'docu_knowledge'], template=self.DEFAULT_TEMPLATE)
        stream_handler = StreamHandler(st.empty())
        chat_gpt = ChatOpenAI(streaming=True, callbacks=[stream_handler], temperature=temperature, model_name="gpt-4o")
        conversation_with_summary = LLMChain(llm=chat_gpt, prompt=PROMPT, verbose=True)
        output = conversation_with_summary.predict(input=user_message, docu_knowledge=docu_knowledge)
        return output

    async def run(self):
        date_now = datetime.now()
        date_year = date_now.year
        date_month = date_now.month
        date_day = date_now.day
        date_day_ = date_now.strftime("%A")

        date_d = "{}-{}-{}".format(date_year, date_month, date_day)

        st.title(":orange[Welcome!]")
        st.subheader(f" _{date_d}_")
        st.subheader(f" :orange[_{date_day_}_]", divider='rainbow')

        if "messages" not in st.session_state:
            st.session_state["messages"] = [ChatMessage(role="assistant", content="")]

        with st.form(key='company_search_form'):
            company_name = st.text_input("Enter a company name:")
            submit_button = st.form_submit_button("Search", type="primary")

        if submit_button and company_name:
            articles_string = ""
            symbols = await self.get_stock_symbol(company_name)
            cont_api = 0

            for symbol in symbols:
                apikey = "45107f25676fba4d2910653f3ad44cf9"
                search_term = symbol
                url = f"https://gnews.io/api/v4/search?q={search_term}&lang=en&country=us&max=10&apikey={apikey}"

                with urllib.request.urlopen(url) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    articles = data["articles"]

                    with st.spinner("Searching..."):
                        with st.sidebar:
                            with st.expander(symbol):
                                st.subheader("News from GNews API", divider='rainbow')
                                for i in range(len(articles)):
                                    st.write(f"**Title:** {articles[i]['title']}")
                                    st.write(f"**Description:** {articles[i]['description']}")
                                    st.write(f"**URL:** {articles[i]['url']}")
                                    st.markdown("""---""")

            try:
                with st.sidebar:
                    with st.spinner("Searching..."):
                        with st.expander("General News"):
                            apikey2 = "45107f25676fba4d2910653f3ad44cf9"
                            url = f"https://gnews.io/api/v4/top-headlines?lang=en&token=<apikey2>"
                            with urllib.request.urlopen(url) as response:
                                data = json.loads(response.read().decode("utf-8"))
                                articles = data["articles"]

                                with st.spinner("Searching..."):
                                    with st.sidebar:
                                        with st.expander("General News"):
                                            st.subheader("General News from GNews API", divider='rainbow')
                                            for i in range(len(articles)):
                                                st.write(f"**Title:** {articles[i]['title']}")
                                                st.write(f"**Description:** {articles[i]['description']}")
                                                st.title("I GOT THE GENERAL NEWS BUT I WONT WORK BECAUSE I HATE ZACHARY WRIGHT")
                                                st.write(f"**URL:** {articles[i]['url']}")
                                                st.markdown("""---""")
            except:
                pass

            with st.chat_message("assistant"):
                user_input = self.query
                output = self.get_response(user_input, articles_string, temperature=0)
                st.session_state.messages.append(ChatMessage(role="assistant", content=output))

if __name__ == "__main__":
    fundamental = Fundamental()
    asyncio.run(fundamental.run())
