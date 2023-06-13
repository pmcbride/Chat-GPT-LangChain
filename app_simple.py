from dotenv import load_dotenv

load_dotenv()

import io
import os
import ssl
from contextlib import closing
from typing import Any, Dict, List, Optional, Callable, Tuple, Union
import datetime

import boto3
import gradio as gr
import requests

#  UNCOMMENT TO USE WHISPER
import warnings
import whisper

from langchain import ConversationChain, LLMChain

from langchain.agents import load_tools, initialize_agent, AgentType, AgentExecutor, Agent
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.memory.chat_memory import BaseChatMemory, BaseMemory
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.base_language import BaseLanguageModel
from langchain.chains.combine_documents.base import BaseCombineDocumentsChain
from langchain.embeddings.base import Embeddings

from threading import Lock

# Console to variable
from io import StringIO
import sys
import re

from openai.error import AuthenticationError, InvalidRequestError, RateLimitError

# Pertains to Express-inator functionality
from langchain.prompts import PromptTemplate

from polly_utils import PollyVoiceData, NEURAL_ENGINE
from azure_utils import AzureVoiceData

# Pertains to question answering functionality
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
from langchain.vectorstores.base import VectorStore
from langchain.docstore.document import Document
from langchain.chains.question_answering import load_qa_chain

import elevenlabs
from elevenlabs import generate, play, save, stream

import pprint as pp
pprint = pp.PrettyPrinter(sort_dicts=False).pprint
pformat = pp.PrettyPrinter(sort_dicts=False).pformat

news_api_key = os.environ["NEWS_API_KEY"]
tmdb_bearer_token = os.environ["TMDB_BEARER_TOKEN"]

TOOLS_LIST = [
    "serpapi",
    "google-search",
    "requests_all",
    "wolfram-alpha",
    "pal-math",
    "pal-colored-objects",
    "news-api",
    "tmdb-api",
    # 'open-meteo-api'
]
TOOLS_DEFAULT_LIST = [
    "serpapi",
    "requests_all", 
    # "google-search",
    "wolfram-alpha",
    "pal-math"
]
BUG_FOUND_MSG = "Congratulations, you've found a bug in this application!"
# AUTH_ERR_MSG = "Please paste your OpenAI key from openai.com to use this application. It is not necessary to hit a button or key after pasting it."
AUTH_ERR_MSG = "Please paste your OpenAI key from openai.com to use this application. "
MAX_TOKENS = 512

LOOPING_TALKING_HEAD = "videos/Masahiro.mp4"
TALKING_HEAD_WIDTH = "192"
MAX_TALKING_HEAD_TEXT_LENGTH = 155

# Pertains to Express-inator functionality
NUM_WORDS_DEFAULT = 0
MAX_WORDS = 400
FORMALITY_DEFAULT = "N/A"
TEMPERATURE_DEFAULT = 0.5
EMOTION_DEFAULT = "N/A"
LANG_LEVEL_DEFAULT = "N/A"
TRANSLATE_TO_DEFAULT = "N/A"
LITERARY_STYLE_DEFAULT = "N/A"
PROMPT_TEMPLATE = PromptTemplate(
    input_variables=[
        "original_words",
        "num_words",
        "formality",
        "emotions",
        "lang_level",
        "translate_to",
        "literary_style",
    ],
    template="Restate {num_words}{formality}{emotions}{lang_level}{translate_to}{literary_style}the following: \n{original_words}\n",
)

FORCE_TRANSLATE_DEFAULT = False  # TODO: Change back to True?
USE_GPT4_DEFAULT = False

POLLY_VOICE_DATA = PollyVoiceData()
AZURE_VOICE_DATA = AzureVoiceData()



# Translate To languages available
TRANSLATE_TO_LANGS = [
    "Arabic", "Arabic (Gulf)", "Catalan", "Chinese (Cantonese)", "Chinese (Mandarin)",
    "Danish", "Dutch", "English (Australian)", "English (British)", "English (Indian)", "English (New Zealand)",
    "English (South African)", "English (US)", "English (Welsh)", "Finnish", "French", "French (Canadian)",
    "German", "German (Austrian)", "Georgian", "Hindi", "Icelandic", "Indonesian", "Italian", "Japanese",
    "Korean", "Norwegian", "Polish",
    "Portuguese (Brazilian)", "Portuguese (European)", "Romanian", "Russian", "Spanish (European)",
    "Spanish (Mexican)", "Spanish (US)", "Swedish", "Turkish", "Ukrainian", "Welsh"]

TRANSLATE_TO_DEFAULT_LANGS = [
    "English (US)",
    "Chinese (Mandarin)",
]


# Pertains to WHISPER functionality
WHISPER_DETECT_LANG = "Detect language"
WHISPER_LANGS = [
    "Arabic", "Arabic (Gulf)", "Catalan", "Chinese (Cantonese)", "Chinese (Mandarin)",
    "Danish", "Dutch", "English (Australian)", "English (British)", "English (Indian)", "English (New Zealand)",
    "English (South African)", "English (US)", "English (Welsh)", "Finnish", "French", "French (Canadian)",
    "German", "German (Austrian)", "Georgian", "Hindi", "Icelandic", "Indonesian", "Italian", "Japanese",
    "Korean", "Norwegian", "Polish",
    "Portuguese (Brazilian)", "Portuguese (European)", "Romanian", "Russian", "Spanish (European)",
    "Spanish (Mexican)", "Spanish (US)", "Swedish", "Turkish", "Ukrainian", "Welsh",
    "emojis", "Gen Z slang", "how the stereotypical Karen would say it", "Klingon", "Neanderthal",
    "Pirate", "Strange Planet expospeak technical talk", "Yoda"]

WHISPER_DEFAULT_LANGS = [
    "English (US)",
    "Chinese (Mandarin)",
]
# UNCOMMENT TO USE WHISPER
warnings.filterwarnings("ignore")
WHISPER_MODEL = whisper.load_model("tiny")
print("WHISPER_MODEL", WHISPER_MODEL)

# Lang Level languages available
LANG_LEVELS = [
    "N5 (beginner)", "N4 (basic)", "N3 (intermediate)", "N2 (proficient)", "N1 (advanced)",
    "1st grade", "2nd grade", "3rd grade", "4th grade", "5th grade", "6th grade",
    "7th grade", "8th grade", "9th grade", "10th grade", "11th grade", "12th grade", "University"]

LANG_DEFAULT_LEVELS = [
    "N5 (beginner)", "N4 (basic)", "N3 (intermediate)", "N2 (proficient)", "N1 (advanced)", 
    "High School", "University", "Graduate School"
]

# Lit Style languages available
LITERARY_STYLES = [
    "Prose", "Story", "Summary", "Outline", "Bullets", 
    "Poetry", "Haiku", "Limerick", "Rap", "Joke", "Knock-knock", "FAQ"]

LITERARY_DEFAULT_STYLES = [
    "Prose",
    "Story",
    "Summary",
    "Outline",
    "Bullets",
    "FAQ"
]


# UNCOMMENT TO USE WHISPER
def transcribe(aud_inp, whisper_lang):
    if aud_inp is None:
        return ""
    aud = whisper.load_audio(aud_inp)
    aud = whisper.pad_or_trim(aud)
    mel = whisper.log_mel_spectrogram(aud).to(WHISPER_MODEL.device)
    _, probs = WHISPER_MODEL.detect_language(mel)
    options = whisper.DecodingOptions()
    if whisper_lang != WHISPER_DETECT_LANG:
        whisper_lang_code = POLLY_VOICE_DATA.get_whisper_lang_code(whisper_lang)
        options = whisper.DecodingOptions(language=whisper_lang_code)
    result = whisper.decode(WHISPER_MODEL, mel, options)
    print("result.text", result.text)
    result_text = ""
    if result and result.text:
        result_text = result.text
    return result_text


# Temporarily address Wolfram Alpha SSL certificate issue
ssl._create_default_https_context = ssl._create_unverified_context


# TEMPORARY FOR TESTING
def transcribe_dummy(aud_inp_tb, whisper_lang):
    if aud_inp_tb is None:
        return ""
    # aud = whisper.load_audio(aud_inp)
    # aud = whisper.pad_or_trim(aud)
    # mel = whisper.log_mel_spectrogram(aud).to(WHISPER_MODEL.device)
    # _, probs = WHISPER_MODEL.detect_language(mel)
    # options = whisper.DecodingOptions()
    # options = whisper.DecodingOptions(language="ja")
    # result = whisper.decode(WHISPER_MODEL, mel, options)
    result_text = "Whisper will detect language"
    if whisper_lang != WHISPER_DETECT_LANG:
        whisper_lang_code = POLLY_VOICE_DATA.get_whisper_lang_code(whisper_lang)
        result_text = f"Whisper will use lang code: {whisper_lang_code}"
    print("result_text", result_text)
    return aud_inp_tb


# Pertains to Express-inator functionality
def transform_text(
    desc: str,
    express_chain: Optional[LLMChain],
    num_words: int,
    formality: str,
    anticipation_level: str,
    joy_level: str,
    trust_level: str,
    fear_level: str,
    surprise_level: str,
    sadness_level: str,
    disgust_level: str,
    anger_level: str,
    lang_level: str,
    translate_to: str,
    literary_style: str,
    force_translate: bool,
):
    num_words_prompt = ""
    if num_words and int(num_words) != 0:
        num_words_prompt = "using up to " + str(num_words) + " words, "

    # Change some arguments to lower case
    formality = formality.lower()
    anticipation_level = anticipation_level.lower()
    joy_level = joy_level.lower()
    trust_level = trust_level.lower()
    fear_level = fear_level.lower()
    surprise_level = surprise_level.lower()
    sadness_level = sadness_level.lower()
    disgust_level = disgust_level.lower()
    anger_level = anger_level.lower()

    formality_str = ""
    if formality != "n/a":
        formality_str = "in a " + formality + " manner, "

    # put all emotions into a list
    emotions = []
    if anticipation_level != "n/a":
        emotions.append(anticipation_level)
    if joy_level != "n/a":
        emotions.append(joy_level)
    if trust_level != "n/a":
        emotions.append(trust_level)
    if fear_level != "n/a":
        emotions.append(fear_level)
    if surprise_level != "n/a":
        emotions.append(surprise_level)
    if sadness_level != "n/a":
        emotions.append(sadness_level)
    if disgust_level != "n/a":
        emotions.append(disgust_level)
    if anger_level != "n/a":
        emotions.append(anger_level)

    emotions_str = ""
    if len(emotions) > 0:
        if len(emotions) == 1:
            emotions_str = "with emotion of " + emotions[0] + ", "
        else:
            emotions_str = (
                "with emotions of " + ", ".join(emotions[:-1]) + " and " + emotions[-1] + ", "
            )

    lang_level_str = ""
    lang_level_frag = "at a level that a person in " + lang_level + " can easily comprehend"
    is_N_level = lang_level[0] == "N" and len(lang_level) >= 2 and lang_level[1].isdigit()
    if lang_level != LANG_LEVEL_DEFAULT and not is_N_level:
        lang_level_str = lang_level_frag + ", " if translate_to == TRANSLATE_TO_DEFAULT else ""

    translate_to_str = ""
    if translate_to != TRANSLATE_TO_DEFAULT and (
        force_translate
        or (lang_level != LANG_LEVEL_DEFAULT and not is_N_level)
        or literary_style != LITERARY_STYLE_DEFAULT
        or len(emotions_str) > 0
        or len(formality_str) > 0
        or num_words_prompt != ""
    ):
        print("===translate_to", translate_to)
        print("===lang_level", lang_level)
        print("===is_N_level", is_N_level)
        translate_to_str = (
            "translated to "
            + translate_to
            + ("" if lang_level == LANG_LEVEL_DEFAULT or is_N_level else " " + lang_level_frag)
            + ", "
        )

    literary_style_str = ""
    if literary_style != LITERARY_STYLE_DEFAULT:
        if literary_style == "Prose":
            literary_style_str = "as prose, "
        if literary_style == "Story":
            literary_style_str = "as a story, "
        elif literary_style == "Summary":
            literary_style_str = "as a summary, "
        elif literary_style == "Outline":
            literary_style_str = "as an outline numbers and lower case letters, "
        elif literary_style == "Bullets":
            literary_style_str = "as bullet points using bullets, "
        elif literary_style == "Poetry":
            literary_style_str = "as a poem, "
        elif literary_style == "Haiku":
            literary_style_str = "as a haiku, "
        elif literary_style == "Limerick":
            literary_style_str = "as a limerick, "
        elif literary_style == "Rap":
            literary_style_str = "as a rap, "
        elif literary_style == "Joke":
            literary_style_str = "as a very funny joke with a setup and punchline, "
        elif literary_style == "Knock-knock":
            literary_style_str = "as a very funny knock-knock joke, "
        elif literary_style == "FAQ":
            literary_style_str = "as a FAQ with several questions and answers, "

    formatted_prompt = PROMPT_TEMPLATE.format(
        original_words=desc,
        num_words=num_words_prompt,
        formality=formality_str,
        emotions=emotions_str,
        lang_level=lang_level_str,
        translate_to=translate_to_str,
        literary_style=literary_style_str,
    )

    trans_instr = (
        num_words_prompt
        + formality_str
        + emotions_str
        + lang_level_str
        + translate_to_str
        + literary_style_str
    )
    if express_chain and (len(trans_instr.strip()) > 0):
        generated_text = express_chain.run(
            {
                "original_words": desc,
                "num_words": num_words_prompt,
                "formality": formality_str,
                "emotions": emotions_str,
                "lang_level": lang_level_str,
                "translate_to": translate_to_str,
                "literary_style": literary_style_str,
            }
        ).strip()
    else:
        print("Not transforming text")
        generated_text = desc

    # replace all newlines with <br> in generated_text
    generated_text = generated_text.replace("\n", "\n\n")

    prompt_plus_generated = "GPT prompt: " + formatted_prompt + "\n\n" + generated_text

    print(
        "\n==== date/time: " + str(datetime.datetime.now() - datetime.timedelta(hours=5)) + " ===="
    )
    print("prompt_plus_generated: " + prompt_plus_generated)

    return generated_text


def load_chain(
    tools_list: List[str], llm: BaseLanguageModel
) -> Tuple[AgentExecutor, LLMChain, BaseMemory]:
    chain = None
    express_chain = None
    memory = None
    if llm:
        print("\ntools_list", tools_list)
        tool_names = tools_list
        tools = load_tools(
            tool_names, llm=llm, news_api_key=news_api_key, tmdb_bearer_token=tmdb_bearer_token
        )

        memory = ConversationBufferMemory(memory_key="chat_history")

        chain: AgentExecutor = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            memory=memory,
        )
        express_chain: LLMChain = LLMChain(llm=llm, prompt=PROMPT_TEMPLATE, verbose=True)
    return chain, express_chain, memory


def set_openai_api_key(
    api_key: str, use_gpt4: bool
) -> Tuple[
    AgentExecutor,
    LLMChain,
    BaseLanguageModel,
    OpenAIEmbeddings,
    BaseCombineDocumentsChain,
    BaseMemory,
    bool
]:
    """Set the api key and return chain.
    If no api_key, then None is returned.
    """
    if api_key and api_key.startswith("sk-") and len(api_key) > 50:
        os.environ["OPENAI_API_KEY"] = api_key
        print("\n\n ++++++++++++++ Setting OpenAI API key ++++++++++++++ \n\n")
        print(
            str(datetime.datetime.now())
            + ": Before OpenAI, OPENAI_API_KEY length: "
            + str(len(os.environ["OPENAI_API_KEY"]))
        )

        if use_gpt4:
            llm: BaseLanguageModel = ChatOpenAI(
                temperature=0, max_tokens=MAX_TOKENS, model_name="gpt-4"
            )
            print("Trying to use llm ChatOpenAI with gpt-4")
        else:
            print("Trying to use llm ChatOpenAI with gpt-3.5-turbo")
            llm: BaseLanguageModel = ChatOpenAI(
                temperature=0, max_tokens=MAX_TOKENS, model_name="gpt-3.5-turbo"
            )

        print(
            str(datetime.datetime.now())
            + ": After OpenAI, OPENAI_API_KEY length: "
            + str(len(os.environ["OPENAI_API_KEY"]))
        )
        chain, express_chain, memory = load_chain(TOOLS_DEFAULT_LIST, llm)

        # Pertains to question answering functionality
        embeddings = OpenAIEmbeddings()

        if use_gpt4:
            qa_chain: BaseCombineDocumentsChain = load_qa_chain(
                ChatOpenAI(temperature=0, model_name="gpt-4"), chain_type="stuff"
            )
            print("Trying to use qa_chain ChatOpenAI with gpt-4")
        else:
            print("Trying to use qa_chain ChatOpenAI with gpt-3.5-turbo")
            qa_chain: BaseCombineDocumentsChain = load_qa_chain(
                ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo"), chain_type="stuff"
            )

        print(
            str(datetime.datetime.now())
            + ": After load_chain, OPENAI_API_KEY length: "
            + str(len(os.environ["OPENAI_API_KEY"]))
        )
        os.environ["OPENAI_API_KEY"] = ""
        return chain, express_chain, llm, embeddings, qa_chain, memory, use_gpt4
    return None, None, None, None, None, None, None


def run_chain(chain, inp, capture_hidden_text):
    output = ""
    hidden_text = None
    if capture_hidden_text:
        error_msg = None
        tmp = sys.stdout
        hidden_text_io = StringIO()
        sys.stdout = hidden_text_io

        try:
            output = chain.run(input=inp)
        except AuthenticationError as ae:
            error_msg = AUTH_ERR_MSG + str(datetime.datetime.now()) + ". " + str(ae)
            print("error_msg", error_msg)
        except RateLimitError as rle:
            error_msg = "\n\nRateLimitError: " + str(rle)
        except ValueError as ve:
            pass
            # error_msg = "\n\nValueError: " + str(ve)
        except InvalidRequestError as ire:
            error_msg = "\n\nInvalidRequestError: " + str(ire)
        except Exception as e:
            if "Could not parse LLM output" in str(e):
                error_msg = re.sub(r"Could not parse LLM output", "", str(e))
                error_msg = re.sub(r"`", "", error_msg)
            else:
                error_msg = "\n\n" + BUG_FOUND_MSG + ":\n\n" + str(e)

        sys.stdout = tmp
        hidden_text = hidden_text_io.getvalue()

        # remove escape characters from hidden_text
        hidden_text = re.sub(r"\x1b[^m]*m", "", hidden_text)

        # remove "Entering new AgentExecutor chain..." from hidden_text
        hidden_text = re.sub(r"Entering new AgentExecutor chain...\n", "", hidden_text)

        # remove "Finished chain." from hidden_text
        hidden_text = re.sub(r"Finished chain.", "", hidden_text)

        # Add newline after "Thought:" "Action:" "Observation:" "Input:" and "AI:"
        hidden_text = re.sub(r"Thought:", "\n\nThought:", hidden_text)
        hidden_text = re.sub(r"Action:", "\n\nAction:", hidden_text)
        hidden_text = re.sub(r"Observation:", "\n\nObservation:", hidden_text)
        hidden_text = re.sub(r"Input:", "\n\nInput:", hidden_text)
        hidden_text = re.sub(r"AI:", "\n\nAI:", hidden_text)

        if error_msg:
            hidden_text += error_msg

        print("hidden_text: ", hidden_text)
    else:
        try:
            output = chain.run(input=inp)
        except AuthenticationError as ae:
            output = AUTH_ERR_MSG + str(datetime.datetime.now()) + ". " + str(ae)
            print("output", output)
        except RateLimitError as rle:
            output = "\n\nRateLimitError: " + str(rle)
        except ValueError as ve:
            pass
            # output = "\n\nValueError: " + str(ve)
        except InvalidRequestError as ire:
            output = "\n\nInvalidRequestError: " + str(ire)
        except Exception as e:
            if "Could not parse LLM output" in str(e):
                output = re.sub(r"Could not parse LLM output", "", str(e))
                output = re.sub(r"`", "", output)
            else:
                output = "\n\n" + BUG_FOUND_MSG + ":\n\n" + str(e)

    return output, hidden_text


def reset_memory(history, memory):
    memory.clear()
    history = []
    return history, history, memory


class ChatWrapper:
    def __init__(self):
        self.lock = Lock()

    def __call__(
        self,
        api_key: str,
        inp: str,
        history: Optional[Tuple[str, str]],
        chain: Optional[ConversationChain],
        trace_chain: bool,
        speak_text: bool,
        talking_head: bool,
        monologue: bool,
        express_chain: Optional[LLMChain],
        num_words: int,
        formality: str,
        anticipation_level: str,
        joy_level: str,
        trust_level: str,
        fear_level: str,
        surprise_level: str,
        sadness_level: str,
        disgust_level: str,
        anger_level: str,
        lang_level: str,
        translate_to: str,
        literary_style: str,
        qa_chain: Optional[BaseCombineDocumentsChain],
        docsearch: Optional[VectorStore],
        use_embeddings: bool,
        force_translate: bool,
    ):
        """Execute the chat functionality."""
        self.lock.acquire()
        try:
            print("\n==== date/time: " + str(datetime.datetime.now()) + " ====")
            print(f"inp:                {inp}") # + inp)
            print(f"chain:              {chain}")
            print(f"trace_chain:        {trace_chain}") #, trace_chain)
            print(f"speak_text:         {speak_text}") #, speak_text)
            print(f"talking_head:       {talking_head}") #, talking_head)
            print(f"monologue:          {monologue}") #, monologue)
            print(f"express_chain:      {express_chain}")
            print(f"num_words:          {num_words}")
            print(f"formality:          {formality}")
            print(f"anticipation_level: {anticipation_level}")
            print(f"joy_level:          {joy_level}")
            print(f"trust_level:        {trust_level}")
            print(f"fear_level:         {fear_level}")
            print(f"surprise_level:     {surprise_level}")
            print(f"sadness_level:      {sadness_level}")
            print(f"disgust_level:      {disgust_level}")
            print(f"anger_level:        {anger_level}")
            print(f"lang_level:         {lang_level}")
            print(f"translate_to:       {translate_to}")
            print(f"literary_style:     {literary_style}")
            print(f"qa_chain:           {qa_chain}")
            print(f"docsearch:          {docsearch}")
            print(f"use_embeddings:     {use_embeddings}")
            print(f"force_translate:    {force_translate}")
            history = history or []
            # If chain is None, that is because no API key was provided.
            output = "Please paste your OpenAI key from openai.com to use this app. " + str(
                datetime.datetime.now()
            )
            hidden_text = output

            if chain:
                # Set OpenAI key
                import openai

                openai.api_key = api_key
                if not monologue:
                    if use_embeddings:
                        if inp and inp.strip() != "":
                            if docsearch:
                                docs = docsearch.similarity_search(inp)
                                output = str(qa_chain.run(input_documents=docs, question=inp))
                            else:
                                output, hidden_text = (
                                    "Please supply some text in the the Embeddings tab.",
                                    None,
                                )
                        else:
                            output, hidden_text = "What's on your mind?", None
                    else:
                        complete_inp = inp
                        # If the user has selected an N1-N5 language level and an output language,
                        # then put that in the request so that the response is at that level of language proficiency.
                        if (
                            lang_level
                            and lang_level != LANG_LEVEL_DEFAULT
                            and translate_to
                            and translate_to != TRANSLATE_TO_DEFAULT
                        ):
                            # if lang_level starts with "N" and a single digit and a space, then it is an N1-N5 level
                            if re.match(r"N\d ", lang_level):
                                # jlp_level = the first two characters of lang_level
                                jlpt_level = lang_level[:2]
                                print("jlpt_level", lang_level)
                                jlpt_range = "N5"  # default to N5
                                if jlpt_level == "N1":
                                    jlpt_range = "N1, N2, N3, N4 and N5"
                                elif jlpt_level == "N2":
                                    jlpt_range = "N2, N3, N4 and N5"
                                elif jlpt_level == "N3":
                                    jlpt_range = "N3, N4 and N5"
                                elif jlpt_level == "N4":
                                    jlpt_range = "N4 and N"

                                complete_inp = (
                                    f"{inp} Your response should be short, and in {translate_to}"
                                    f" using only vocabulary and grammar equivalent"
                                    f" to that found in JLPT level {jlpt_range}."
                                    f" Don't translate anything back into English."
                                )
                        print("complete_inp to run_chain", complete_inp)
                        output, hidden_text = run_chain(
                            chain, inp=complete_inp, capture_hidden_text=trace_chain
                        )
                else:
                    output, hidden_text = inp, None

            output = transform_text(
                output,
                express_chain,
                num_words,
                formality,
                anticipation_level,
                joy_level,
                trust_level,
                fear_level,
                surprise_level,
                sadness_level,
                disgust_level,
                anger_level,
                lang_level,
                translate_to,
                literary_style,
                force_translate,
            )

            text_to_display = output
            if trace_chain:
                text_to_display = hidden_text + "\n\n" + output
            history.append((inp, text_to_display))

            html_video, temp_file, html_audio, temp_aud_file = None, None, None, None
            if speak_text:
                if talking_head:
                    if len(output) <= MAX_TALKING_HEAD_TEXT_LENGTH:
                        html_video, temp_file = do_html_video_speak(output, translate_to)
                    else:
                        temp_file = LOOPING_TALKING_HEAD
                        html_video = create_html_video(temp_file, TALKING_HEAD_WIDTH)
                        html_audio, temp_aud_file = do_html_audio_speak(output, translate_to)
                else:
                    html_audio, temp_aud_file = do_html_audio_speak(output, translate_to)
            else:
                if talking_head:
                    temp_file = LOOPING_TALKING_HEAD
                    html_video = create_html_video(temp_file, TALKING_HEAD_WIDTH)
                else:
                    # html_audio, temp_aud_file = do_html_audio_speak(output, translate_to)
                    # html_video = create_html_video(temp_file, "128")
                    pass

        except Exception as e:
            raise e
        finally:
            self.lock.release()
        return history, history, html_video, temp_file, html_audio, temp_aud_file, ""
        # return history, history, html_audio, temp_aud_file, ""


chat = ChatWrapper()


def do_html_audio_speak(words_to_speak, polly_language):
    polly_client = boto3.Session(
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=os.environ["AWS_DEFAULT_REGION"],
    ).client("polly")

    # voice_id, language_code, engine = POLLY_VOICE_DATA.get_voice(polly_language, "Female")
    voice_id, language_code, engine = POLLY_VOICE_DATA.get_voice(polly_language, "Male")
    if not voice_id:
        # voice_id = "Joanna"
        voice_id = "Matthew"
        language_code = "en-US"
        engine = NEURAL_ENGINE
    response = polly_client.synthesize_speech(
        Text=words_to_speak,
        OutputFormat="mp3",
        VoiceId=voice_id,
        LanguageCode=language_code,
        Engine=engine,
    )

    html_audio = "<pre>no audio</pre>"

    # Save the audio stream returned by Amazon Polly on Lambda's temp directory
    if "AudioStream" in response:
        with closing(response["AudioStream"]) as stream:
            # output = os.path.join("/tmp/", "speech.mp3")

            try:
                with open("audios/tempfile.mp3", "wb") as f:
                    f.write(stream.read())
                temp_aud_file = gr.File("audios/tempfile.mp3")
                temp_aud_file_url = "/file=" + temp_aud_file.value["name"]
                html_audio = (
                    f'<audio autoplay><source src={temp_aud_file_url} type="audio/mp3"></audio>'
                )
            except IOError as error:
                # Could not write to file, exit gracefully
                print(error)
                return None, None
    else:
        # The response didn't contain audio data, exit gracefully
        print("Could not stream audio")
        return None, None

    return html_audio, "audios/tempfile.mp3"


def create_html_video(file_name, width):
    temp_file_url = "/file=" + tmp_file.value["name"]
    html_video = f'<video width={width} height={width} autoplay muted loop><source src={temp_file_url} type="video/mp4" poster="Masahiro.png"></video>'
    return html_video


import re


def clean_text(text):
    text = re.sub(r"\n", " ", text)  # Replaces newlines with spaces
    text = re.sub(r"\r", "", text)  # Removes carriage returns
    text = re.sub(r"\t", " ", text)  # Replaces tabs with spaces
    text = re.sub(r"=", " equals ", text)  # Replaces tabs with spaces
    text = re.sub(r"\[", " ", text)  # Replaces tabs with spaces
    text = re.sub(r"\]", " ", text)  # Replaces tabs with spaces
    text = re.sub(r" -", " negative ", text)  # Replaces tabs with spaces
    # text = re.sub(r'[^a-zA-Z0-9 ]', '', text) # Removes all non-alphanumeric characters excluding spaces
    return text


from bs4 import BeautifulSoup


def clean_html(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    clean_text = soup.get_text(separator=" ")
    return clean_text


wav_idx = 0


def tts(history, voice="Bella"):
    global wav_idx
    original_string = text = history[-1][1]
    if text is None:
        return False
    text = clean_html(text)
    text = clean_text(text)
    if text == "":
        return False
    print(f"\ntts: {text}")
    audio = generate(
        text=text,
        voice=voice,
        model="eleven_monolingual_v1",
        stream=False,
    )
    audio_file = f"audio/audio_steve_{wav_idx:06d}.wav"
    audio_string = f'<audio src="file/{audio_file}" controls autoplay></audio>'
    save(audio, audio_file)
    wav_idx += 1
    history[-1][1] = f"{audio_string}\n\n{original_string}"
    return history, audio_file


def do_html_video_speak(words_to_speak, azure_language):
    azure_voice = AZURE_VOICE_DATA.get_voice(azure_language, "Male")
    if not azure_voice:
        azure_voice = "en-US-ChristopherNeural"

    headers = {"Authorization": f"Bearer {os.environ['EXHUMAN_API_KEY']}"}
    body = {
        "bot_name": "Masahiro",
        "bot_response": words_to_speak,
        "azure_voice": azure_voice,
        "azure_style": "friendly",
        "animation_pipeline": "high_speed",
    }
    api_endpoint = "https://api.exh.ai/animations/v1/generate_lipsync"
    res = requests.post(api_endpoint, json=body, headers=headers)
    print("res.status_code: ", res.status_code)

    html_video = "<pre>no video</pre>"
    if isinstance(res.content, bytes):
        response_stream = io.BytesIO(res.content)
        print("len(res.content)): ", len(res.content))

        with open("videos/tempfile.mp4", "wb") as f:
            f.write(response_stream.read())
        temp_file = gr.File("videos/tempfile.mp4")
        temp_file_url = "/file=" + temp_file.value["name"]
        html_video = f'<video width={TALKING_HEAD_WIDTH} height={TALKING_HEAD_WIDTH} autoplay><source src={temp_file_url} type="video/mp4" poster="Masahiro.png"></video>'
    else:
        print("video url unknown")
    return html_video, "videos/tempfile.mp4"


def update_selected_tools(widget, state, llm):
    if widget:
        state = widget
        chain, express_chain, memory = load_chain(state, llm)
        return state, llm, chain, express_chain


def update_talking_head(widget, state):
    if widget:
        state = widget

        video_html_talking_head = create_html_video(LOOPING_TALKING_HEAD, TALKING_HEAD_WIDTH)
        return state, video_html_talking_head
    else:
        # return state, create_html_video(LOOPING_TALKING_HEAD, "32")
        return None, "<pre></pre>"


def update_foo(widget, state):
    if widget:
        state = widget
        return state


# Pertains to question answering functionality
def update_embeddings(embeddings_text, embeddings, qa_chain) -> VectorStore:
    if embeddings_text:
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_text(embeddings_text)

        docsearch = FAISS.from_texts(texts, embeddings)
        print("Embeddings updated")
        return docsearch


# Pertains to question answering functionality
def update_use_embeddings(widget, state: gr.State) -> gr.State:
    if widget:
        state = widget
        return state


with gr.Blocks(css=".gradio-container {background-color: lightgray}") as demo:
    llm_state = gr.State()
    history_state = gr.State()
    chain_state = gr.State()
    express_chain_state = gr.State()
    tools_list_state = gr.State(TOOLS_DEFAULT_LIST)
    trace_chain_state = gr.State(False)
    speak_text_state = gr.State(False)
    talking_head_state = gr.State(False)
    monologue_state = gr.State(
        False
    )  # Takes the input and repeats it back to the user, optionally transforming it.
    force_translate_state = gr.State(FORCE_TRANSLATE_DEFAULT)  #
    memory_state = gr.State()

    # Pertains to Express-inator functionality
    num_words_state = gr.State(NUM_WORDS_DEFAULT)
    formality_state = gr.State(FORMALITY_DEFAULT)
    anticipation_level_state = gr.State(EMOTION_DEFAULT)
    joy_level_state = gr.State(EMOTION_DEFAULT)
    trust_level_state = gr.State(EMOTION_DEFAULT)
    fear_level_state = gr.State(EMOTION_DEFAULT)
    surprise_level_state = gr.State(EMOTION_DEFAULT)
    sadness_level_state = gr.State(EMOTION_DEFAULT)
    disgust_level_state = gr.State(EMOTION_DEFAULT)
    anger_level_state = gr.State(EMOTION_DEFAULT)
    lang_level_state = gr.State(LANG_LEVEL_DEFAULT)
    translate_to_state = gr.State(TRANSLATE_TO_DEFAULT)
    literary_style_state = gr.State(LITERARY_STYLE_DEFAULT)

    # Pertains to WHISPER functionality
    whisper_lang_state = gr.State(WHISPER_DETECT_LANG)

    # Pertains to question answering functionality
    embeddings_state = gr.State()
    qa_chain_state = gr.State()
    docsearch_state = gr.State()
    use_embeddings_state = gr.State(False)

    use_gpt4_state = gr.State(USE_GPT4_DEFAULT)

    with gr.Tab("Chat"):
        with gr.Row():
            with gr.Column():
                gr.HTML(
                    """<b><center>GPT + WolframAlpha + Whisper</center></b>
                    <p><center>Hit Enter after pasting your OpenAI API key.</center></p>
                    <i><center>Experimental: N5-N1 levels for practicing any language</center></i>"""
                )

            openai_api_key_textbox = gr.Textbox(
                placeholder="Paste your OpenAI API key (sk-...) and hit Enter",
                show_label=False,
                lines=1,
                type="password",
            )

        with gr.Row():
            with gr.Column(scale=1, min_width=TALKING_HEAD_WIDTH, visible=True):
                speak_text_cb = gr.Checkbox(label="Enable speech", value=False)
                speak_text_cb.change(
                    update_foo, inputs=[speak_text_cb, speak_text_state], outputs=[speak_text_state]
                )

                my_file = gr.File(label="Upload a file", type="file", visible=False)
                tmp_file = gr.File(LOOPING_TALKING_HEAD, visible=False)
                # tmp_file_url = "/file=" + tmp_file.value['name']
                htm_video = create_html_video(LOOPING_TALKING_HEAD, TALKING_HEAD_WIDTH)
                video_html = gr.HTML(htm_video)

                # my_aud_file = gr.File(label="Audio file", type="file", visible=True)
                tmp_aud_file = gr.File("audios/tempfile.mp3", visible=False)
                tmp_aud_file_url = "/file=" + tmp_aud_file.value["name"]
                htm_audio = f'<audio><source src={tmp_aud_file_url} type="audio/mp3"></audio>'
                audio_html = gr.HTML(htm_audio)

            with gr.Column(scale=7):
                chatbot = gr.Chatbot()

        with gr.Row():
            message = gr.Textbox(
                label="What's on your mind??",
                placeholder="What's the answer to life, the universe, and everything?",
                lines=1,
            )
            submit = gr.Button(value="Send", variant="secondary").style(full_width=False)

        # UNCOMMENT TO USE WHISPER
        with gr.Row():
            audio_comp = gr.Microphone(
                source="microphone",
                type="filepath",
                label="Just say it!",
                interactive=True,
                streaming=False,
            )
            audio_comp.change(
                transcribe, inputs=[audio_comp, whisper_lang_state], outputs=[message]
            )

        # TEMPORARY FOR TESTING
        # with gr.Row():
        #     audio_comp_tb = gr.Textbox(label="Just say it!", lines=1)
        #     audio_comp_tb.submit(transcribe_dummy, inputs=[audio_comp_tb, whisper_lang_state], outputs=[message])

        with gr.Accordion("General examples", open=False):
            gr.Examples(
                examples=[
                    "How many people live in Canada?",
                    "What is 2 to the 30th power?",
                    "If x+y=10 and x-y=4, what are x and y?",
                    "How much did it rain in SF today?",
                    "Get me information about the movie 'Avatar'",
                    "What are the top tech headlines in the US?",
                    "On the desk, you see two blue booklets, two purple booklets, and two yellow pairs of sunglasses - "
                    "if I remove all the pairs of sunglasses from the desk, how many purple items remain on it?",
                ],
                inputs=message,
            )
        with gr.Accordion(
            "Language practice examples. Select N5-N1 on Output Language tab. Best with GPT-4",
            open=False,
        ):
            gr.Examples(
                examples=[
                    "Let's play three truths and a lie",
                    "Let's play a game of rock paper scissors",
                    "Let's play a game of 20 questions. Please think of something and I will try to guess what it is",
                    "Let's play a game of 20 questions. I am thinking of something so please try to guess what it is",
                    "Please ask me a question about cats",
                    "Please write a short story about a dog and a cat trying to find their way home. Then ask me a multiple "
                    "choice question about the story, but don’t reveal the answer until I attempt to answer it.",
                    "Please write a dialog between students named Mary and Takeshi in "
                    "which they are planning a study date. Then ask me a multiple choice question about the "
                    "dialog, but don’t reveal the answer until I attempt to answer it.",
                    "Please write a dialog between a waiter and a customer at an expensive restaurant. Then ask "
                    "me a multiple choice question about the dialog, but don’t reveal the answer until I "
                    "attempt to answer it.",
                    "Please write a dialog between a mother and a child in which the child is asking for a "
                    "present. Then ask me a multiple choice question about the dialog, but don’t reveal the "
                    "answer until I attempt to answer it.",
                    "Please write a dialog between a student and a teacher in which the student is asking for "
                    "help with their homework. Then ask me a multiple choice question about the dialog, but "
                    "don’t reveal the answer until I attempt to answer it.",
                    "Please write a dialog between a customer and a salesperson in which the customer is "
                    "looking for a new pair of shoes. Then ask me a multiple choice question about the dialog, "
                    "but don’t reveal the answer until I attempt to answer it.",
                ],
                inputs=message,
            )

    with gr.Tab("Settings"):
        tools_cb_group = gr.CheckboxGroup(
            label="Tools:", choices=TOOLS_LIST, value=TOOLS_DEFAULT_LIST
        )
        tools_cb_group.change(
            update_selected_tools,
            inputs=[tools_cb_group, tools_list_state, llm_state],
            outputs=[tools_list_state, llm_state, chain_state, express_chain_state],
        )

        trace_chain_cb = gr.Checkbox(label="Show reasoning chain in chat bubble", value=False)
        trace_chain_cb.change(
            update_foo, inputs=[trace_chain_cb, trace_chain_state], outputs=[trace_chain_state]
        )

        force_translate_cb = gr.Checkbox(
            label="Force translation to selected Output Language", value=FORCE_TRANSLATE_DEFAULT
        )
        force_translate_cb.change(
            update_foo,
            inputs=[force_translate_cb, force_translate_state],
            outputs=[force_translate_state],
        )

        # speak_text_cb = gr.Checkbox(label="Speak text from agent", value=False)
        # speak_text_cb.change(update_foo, inputs=[speak_text_cb, speak_text_state],
        #                      outputs=[speak_text_state])

        talking_head_cb = gr.Checkbox(label="Show talking head", value=talking_head_state.value)
        talking_head_cb.change(
            update_talking_head,
            inputs=[talking_head_cb, talking_head_state],
            outputs=[talking_head_state, video_html],
        )
        demo.load(
            update_talking_head,
            inputs=[talking_head_cb, talking_head_state],
            outputs=[talking_head_state, video_html],
        )
        monologue_cb = gr.Checkbox(
            label="Babel fish mode (translate/restate what you enter, no conversational agent)",
            value=False,
        )
        monologue_cb.change(
            update_foo, inputs=[monologue_cb, monologue_state], outputs=[monologue_state]
        )

        use_gpt4_cb = gr.Checkbox(
            label="Use GPT-4 (experimental) if your OpenAI API has access to it",
            value=USE_GPT4_DEFAULT,
        )
        use_gpt4_cb.change(
            set_openai_api_key,
            inputs=[openai_api_key_textbox, use_gpt4_cb],
            outputs=[
                chain_state,
                express_chain_state,
                llm_state,
                embeddings_state,
                qa_chain_state,
                memory_state,
                use_gpt4_state,
            ],
        )

        reset_btn = gr.Button(value="Reset chat", variant="secondary").style(full_width=False)
        reset_btn.click(
            reset_memory,
            inputs=[history_state, memory_state],
            outputs=[chatbot, history_state, memory_state],
        )

    with gr.Tab("Whisper STT"):
        whisper_lang_radio = gr.Radio(
            label="Whisper speech-to-text language:",
            choices=[
                WHISPER_DETECT_LANG,
                *WHISPER_DEFAULT_LANGS,
            ],
            value=WHISPER_DETECT_LANG,
        )

        whisper_lang_radio.change(
            update_foo,
            inputs=[whisper_lang_radio, whisper_lang_state],
            outputs=[whisper_lang_state],
        )

    with gr.Tab("Output Language"):
        lang_level_radio = gr.Radio(
            label="Language level:",
            choices=[
                LANG_LEVEL_DEFAULT,
                *LANG_DEFAULT_LEVELS,
            ],
            value=LANG_LEVEL_DEFAULT,
        )
        lang_level_radio.change(
            update_foo, 
            inputs=[lang_level_radio, lang_level_state], 
            outputs=[lang_level_state]
        )

        translate_to_radio = gr.Radio(
            label="Language:",
            choices=[
                TRANSLATE_TO_DEFAULT,
                *TRANSLATE_TO_DEFAULT_LANGS,
            ],
            value=TRANSLATE_TO_DEFAULT,
        )

        translate_to_radio.change(
            update_foo,
            inputs=[translate_to_radio, translate_to_state],
            outputs=[translate_to_state],
        )

    with gr.Tab("Formality"):
        formality_radio = gr.Radio(label="Formality:",
                                   choices=[FORMALITY_DEFAULT, "Casual", "Polite", "Honorific"],
                                   value=FORMALITY_DEFAULT)
        formality_radio.change(update_foo,
                               inputs=[formality_radio, formality_state],
                               outputs=[formality_state])

    with gr.Tab("Lit Style"):
        literary_style_radio = gr.Radio(
            label="Literary style:",
            choices=[
                LITERARY_STYLE_DEFAULT,
                *LITERARY_DEFAULT_STYLES,
            ],
            value=LITERARY_STYLE_DEFAULT,
        )

        literary_style_radio.change(
            update_foo,
            inputs=[literary_style_radio, literary_style_state],
            outputs=[literary_style_state],
        )

    with gr.Tab("Emotions"):
        anticipation_level_radio = gr.Radio(
            label="Anticipation level:",
            choices=[EMOTION_DEFAULT, "Interest", "Anticipation", "Vigilance"],
            value=EMOTION_DEFAULT,
        )
        anticipation_level_radio.change(
            update_foo,
            inputs=[anticipation_level_radio, anticipation_level_state],
            outputs=[anticipation_level_state],
        )

        joy_level_radio = gr.Radio(
            label="Joy level:",
            choices=[EMOTION_DEFAULT, "Serenity", "Joy", "Ecstasy"],
            value=EMOTION_DEFAULT,
        )
        joy_level_radio.change(
            update_foo, inputs=[joy_level_radio, joy_level_state], outputs=[joy_level_state]
        )

        trust_level_radio = gr.Radio(
            label="Trust level:",
            choices=[EMOTION_DEFAULT, "Acceptance", "Trust", "Admiration"],
            value=EMOTION_DEFAULT,
        )
        trust_level_radio.change(
            update_foo, inputs=[trust_level_radio, trust_level_state], outputs=[trust_level_state]
        )

        fear_level_radio = gr.Radio(
            label="Fear level:",
            choices=[EMOTION_DEFAULT, "Apprehension", "Fear", "Terror"],
            value=EMOTION_DEFAULT,
        )
        fear_level_radio.change(
            update_foo, inputs=[fear_level_radio, fear_level_state], outputs=[fear_level_state]
        )

        surprise_level_radio = gr.Radio(
            label="Surprise level:",
            choices=[EMOTION_DEFAULT, "Distraction", "Surprise", "Amazement"],
            value=EMOTION_DEFAULT,
        )
        surprise_level_radio.change(
            update_foo,
            inputs=[surprise_level_radio, surprise_level_state],
            outputs=[surprise_level_state],
        )

        sadness_level_radio = gr.Radio(
            label="Sadness level:",
            choices=[EMOTION_DEFAULT, "Pensiveness", "Sadness", "Grief"],
            value=EMOTION_DEFAULT,
        )
        sadness_level_radio.change(
            update_foo,
            inputs=[sadness_level_radio, sadness_level_state],
            outputs=[sadness_level_state],
        )

        disgust_level_radio = gr.Radio(
            label="Disgust level:",
            choices=[EMOTION_DEFAULT, "Boredom", "Disgust", "Loathing"],
            value=EMOTION_DEFAULT,
        )
        disgust_level_radio.change(
            update_foo,
            inputs=[disgust_level_radio, disgust_level_state],
            outputs=[disgust_level_state],
        )

        anger_level_radio = gr.Radio(
            label="Anger level:",
            choices=[EMOTION_DEFAULT, "Annoyance", "Anger", "Rage"],
            value=EMOTION_DEFAULT,
        )
        anger_level_radio.change(
            update_foo, 
            inputs=[anger_level_radio, anger_level_state], 
            outputs=[anger_level_state]
        )

    with gr.Tab("Max Words"):
        num_words_slider = gr.Slider(label="Max number of words to generate (0 for don't care)",
                                     value=NUM_WORDS_DEFAULT, minimum=0, maximum=MAX_WORDS, step=10)
        num_words_slider.change(update_foo,
                                inputs=[num_words_slider, num_words_state],
                                outputs=[num_words_state])

    with gr.Tab("Embeddings"):
        embeddings_text_box = gr.Textbox(label="Enter text for embeddings and hit Create:",
                                         lines=20)

        with gr.Row():
            use_embeddings_cb = gr.Checkbox(label="Use embeddings", value=False)
            use_embeddings_cb.change(update_use_embeddings,
                                     inputs=[use_embeddings_cb, use_embeddings_state],
                                     outputs=[use_embeddings_state])

            embeddings_text_submit = gr.Button(value="Create", variant="secondary").style(full_width=False)
            embeddings_text_submit.click(update_embeddings,
                                         inputs=[embeddings_text_box, embeddings_state, qa_chain_state],
                                         outputs=[docsearch_state])

    gr.HTML(
        """
        <p>This application, developed by <a href='https://www.linkedin.com/in/pmmcbride/'>Patrick M. McBride</a> (originally forked from <a href='https://huggingface.co/spaces/JavaFXpert/Chat-GPT-LangChain'>Chat-GPT-LangChain by James L. Weaver</a>), 
        demonstrates a conversational agent implemented with OpenAI GPT-3.5 and LangChain. 
        When necessary, it leverages tools for complex math, searching the internet, and accessing news and weather.
        </p>"""
    )

    gr.HTML(
        """<center>
        Powered by <a href='https://github.com/hwchase17/langchain'>LangChain 🦜️🔗</a>
        </center>"""
    )

    message.submit(
        chat,
        inputs=[
            openai_api_key_textbox,
            message,
            history_state,
            chain_state,
            trace_chain_state,
            speak_text_state,
            talking_head_state,
            monologue_state,
            express_chain_state,
            num_words_state,
            formality_state,
            anticipation_level_state,
            joy_level_state,
            trust_level_state,
            fear_level_state,
            surprise_level_state,
            sadness_level_state,
            disgust_level_state,
            anger_level_state,
            lang_level_state,
            translate_to_state,
            literary_style_state,
            qa_chain_state,
            docsearch_state,
            use_embeddings_state,
            force_translate_state,
        ],
        outputs=[chatbot, history_state, video_html, my_file, audio_html, tmp_aud_file, message],
    )

    submit.click(
        chat,
        inputs=[
            openai_api_key_textbox,
            message,
            history_state,
            chain_state,
            trace_chain_state,
            speak_text_state,
            talking_head_state,
            monologue_state,
            express_chain_state,
            num_words_state,
            formality_state,
            anticipation_level_state,
            joy_level_state,
            trust_level_state,
            fear_level_state,
            surprise_level_state,
            sadness_level_state,
            disgust_level_state,
            anger_level_state,
            lang_level_state,
            translate_to_state,
            literary_style_state,
            qa_chain_state,
            docsearch_state,
            use_embeddings_state,
            force_translate_state,
        ],
        outputs=[chatbot, history_state, video_html, my_file, audio_html, tmp_aud_file, message],
    )

    openai_api_key_textbox.change(set_openai_api_key,
                                  inputs=[openai_api_key_textbox, use_gpt4_state],
                                  outputs=[chain_state, express_chain_state, llm_state, embeddings_state,
                                           qa_chain_state, memory_state, use_gpt4_state],
    )
    openai_api_key_textbox.submit(set_openai_api_key,
                                  inputs=[openai_api_key_textbox, use_gpt4_state],
                                  outputs=[chain_state, express_chain_state, llm_state, embeddings_state,
                                           qa_chain_state, memory_state, use_gpt4_state],
    )
    demo.load(lambda: os.getenv("OPENAI_API_KEY", ""), inputs=None, outputs=openai_api_key_textbox)

demo.launch(debug=True)
