from collections import OrderedDict
import json
import re
import requests

CODEQ_API_ENDPOINT_LAST = 'https://api.codeq.com/v1'


class OrderedClass(object):
    """
    Helper meta class to store variables in order of declaration within __init__ method.
    """

    def __new__(cls, *args, **kwargs):
        instance = object.__new__(cls)
        instance.__dict__ = OrderedDict()
        return instance

    def __setattr__(self, key, value):
        if key != '__dict__':
            self.__dict__[key] = value
        object.__setattr__(self, key, value)

    def keys(self):
        return self.__dict__.keys()

    def items(self):
        return self.__dict__.items()


class Document(OrderedClass):
    """
    A Document is a top level object used to store a list of sentences and its corresponding annotations.
    It needs to be created with a text string as required input parameter.

    Document attributes:

    - raw_text: the input string used to create the Document
    - tokens: a list of words
    - summary: a string containing the summary of the input text
    - summary_detokens: a string containing the summary of the input text in detokenized form
    - compressed_summary: a string containing the compressed summary of the input text
    - compressed_summary_detokens: a string containing the compressed summary of the input text in detokenized form
    - sentences: a list of Sentences objects
    - run_time_stats: a dict containing run time statistics about each annotator

    """

    def __init__(self, raw_text, tokens=None, sentences=None):
        # Document content
        self.raw_text = raw_text
        self.tokens = tokens
        self.sentences = sentences
        self.raw_detokens = None
        self.summary = None
        self.summary_detokens = {}
        self.compressed_summary = None
        self.compressed_summary_detokens = {}
        # Errors
        self.errors = []
        # Stats
        self.run_time_stats = {}

    @classmethod
    def from_list_of_strings(cls, list_of_strings):
        """
        Constructs a Document object from a list of sentences in string format.

        :param list_of_strings:
            A list of sentences strings.
        :return:
            A Document object
        """
        sentences = []
        for idx, raw_sentence in enumerate(list_of_strings):
            sentence = Sentence(raw_sentence=raw_sentence)
            sentence.position = idx
            sentences.append(sentence)

        document = Document(raw_text='\n'.join(list_of_strings))
        document.sentences = sentences
        return document

    def to_dict(self):
        """
        Converts a Document object into a dict from its not None attributes.
        """
        doc_dict = OrderedDict()
        for attr, value in self.items():
            if value is not None and value != {} and value != []:
                if attr == 'sentences':
                    doc_dict[attr] = [s.to_dict() for s in value]
                else:
                    doc_dict[attr] = value
        return doc_dict

    def pretty_print(self):
        return json.dumps(self.to_dict(), indent=2)

    def __str__(self):
        return 'Document: %s' % self.to_dict().__str__()


class Sentence(OrderedClass):
    """
    A Sentence is the basic object used to store different annotations.
    It needs to be created with a string as required input parameter.

    Sentence attributes:

    - raw_sentence: the input string used to create the Sentence
    - position: a number indicating the index position of the sentence in the Document
    - paragraph: a number indicating the index paragrah of the sentence in the Document
    - tokens: a list of words
    - tokens_filtered: a list of words without stop words
    - stems: a list of stemmed words
    - lemmas: a list of lemmatized words
    - pos_tags: a list of Part of Speech tags, corresponding to each word in the list of tokens
    - truecase_sentence: a string with a Truecase sentence
    - detruecase_sentence: a string with a Detruecase sentence
    - speech_acts: a list of tags indicating its corresponding speech act
    - speech_act_values: a list of numeric values associated to a speech act
    - question_types: a list of the question types, if the sentence is categorized as speech act: 'question'
    - question_tags: a list of one- or two-letter question tags, if sentence is categorized as speech act: 'question'
    - named_entities: a list of named_entities tuples containing (entity tokens, type, list of tokens positions)
    - emotions: a list of emotions conveyed in a sentence
    - sentiments: a list of sentiments conveyed in a sentence
    - dates: a list of date named entities with the resolved date in ISO format
    - is_task: a boolean to indicate if a sentence is a task or not
    - task_subclassification: a list of tags indicating its predicted task sub type
    - task_actions: a list of tuples indicating suggested task actions
    - coreferences: a list of dicts containing resolved pronominal coreferences.
        Each coreference is a dictionary that includes: mention, referent, first_referent,
        where each of those elements is a tuple containing a coreference id, the tokens and the span of the item.
        Additionally, each coreference dict contains a coreference chain (all the ids of the linked mentions)
        and the first referent of a chain.
    - compressed_sentence: a string with a a shortened version of a sentence.
    """

    def __init__(self, raw_sentence):
        self.raw_sentence = raw_sentence
        self.position = None
        self.paragraph = None
        self.tokens = None
        self.tokens_filtered = None

        self.stems = None
        self.lemmas = None
        self.pos_tags = None

        self.dependencies = None

        self.truecase_sentence = None
        self.detruecase_sentence = None

        self.speech_acts = None
        self.speech_act_values = None
        self.question_types = None
        self.question_tags = None

        self.named_entities = None
        self.nes_terms = None
        self.nes_types = None
        self.nes_positions = None

        self.emotions = None
        self.sarcasm = None

        self.sentiments = None

        self.dates = None

        self.is_task = None
        self.task_subclassification = None
        self.task_actions = None

        self.coreferences = None

        self.compressed_sentence = None

    @property
    def tagged_sentence(self):
        if not self.pos_tags:
            return None
        tagged_sentence = [t + '/' + self.pos_tags[i] for i, t in enumerate(self.tokens)]
        tagged_sentence = ' '.join(tagged_sentence)
        return tagged_sentence

    def to_dict(self):
        """
        Converts a Sentence object into a dict from its not None attributes
        """
        sent_dict = OrderedDict()
        for attr, value in self.items():
            if value is not None:
                sent_dict[attr] = value
        return sent_dict

    def pretty_print(self):
        sent_dict = OrderedDict()
        for attr, value in self.items():
            if value is not None:
                sent_dict[attr] = value if type(value) == str else str(value)
        return json.dumps(sent_dict, indent=2)

    def __str__(self):
        return 'Sentence: %s' % self.to_dict().__str__()


class CodeqAPIError(Exception):
    pass


class CodeqClient(object):
    def __init__(self, user_id, user_key):
        self.user_id = user_id
        self.user_key = user_key
        self.endpoint = CODEQ_API_ENDPOINT_LAST

    def tokenize(self, text):
        return self.__run_request(text, pipeline='tokenize')

    def ssplit(self, text):
        return self.__run_request(text, pipeline='ssplit')

    def stopword(self, text):
        return self.__run_request(text, pipeline='stopword')

    def stem(self, text):
        return self.__run_request(text, pipeline='stem')

    def truecase(self, text):
        return self.__run_request(text, pipeline='truecase')

    def detruecase(self, text):
        return self.__run_request(text, pipeline='detruecase')

    def pos(self, text):
        return self.__run_request(text, pipeline='pos')

    def parse(self, text):
        return self.__run_request(text, pipeline='parse')

    def emotion(self, text):
        return self.__run_request(text, pipeline='emotion')

    def sarcasm(self, text):
        return self.__run_request(text, pipeline='sarcasm')

    def sentiment(self, text):
        return self.__run_request(text, pipeline='sentiment')

    def ner(self, text):
        return self.__run_request(text, pipeline='ner')

    def speechact(self, text):
        return self.__run_request(text, pipeline='speechact')

    def question(self, text):
        return self.__run_request(text, pipeline='question')

    def task(self, text):
        return self.__run_request(text, pipeline='task')

    def date(self, text):
        return self.__run_request(text, pipeline='date')

    def coreferences(self, text):
        return self.__run_request(text, pipeline='coreference')

    def compress(self, text):
        return self.__run_request(text, pipeline='compress')

    def summarize(self, text):
        return self.__run_request(text, pipeline='summarize')

    def summarize_compress(self, text):
        return self.__run_request(text, pipeline='summarize_compress')

    def analyze(self, text, pipeline=None, benchmark=False):
        """
        :param text: A string
        :param pipeline: A list of strings or a comma-separated string
            indicating the specific annotators to apply to the input text.
            Example: ['speechact', 'tasks'] or 'speechact, tasks'.
            Analyzer Annotator options:
                tokenize, ssplit, stopword, stem, truecase,
                detruecase, pos, emotion, sarcasm, sentiment, ner, speechact,
                parse, question, task, date, coreference,
                compress, summarize, summarize_compress
        :param benchmark:
        :return:
        """
        if isinstance(pipeline, str):
            pipeline = re.split(r'\s*,\s*', pipeline)
        return self.__run_request(text, pipeline=pipeline, benchmark=benchmark)

    def __run_request(self, text, pipeline, benchmark=False):
        params = {
            'user_id': self.user_id,
            'user_key': self.user_key,
            'text': text,
            'pipeline': pipeline,
            'benchmark': benchmark
        }
        request = requests.post(url=self.endpoint, json=params)

        if request.status_code == 200:
            # Make OrderedDict from request.text output
            document_json = json.loads(request.text, object_pairs_hook=OrderedDict)
            return self.__document_from_dict(document_json, benchmark)
        else:
            raise CodeqAPIError("%s; %s" % (request.status_code, request.reason))

    @staticmethod
    def __document_from_dict(document_json_dict, benchmark):
        document = Document(raw_text=document_json_dict['raw_text'])
        document.raw_detokens = document_json_dict['raw_detokens']
        document.summary = document_json_dict['summary']
        document.summary_detokens = document_json_dict['summary_detokens']
        document.compressed_summary = document_json_dict['compressed_summary']
        document.compressed_summary_detokens = document_json_dict['compressed_summary_detokens']
        sentences = []
        for sentence_dict in document_json_dict['sentences']:
            sentence = Sentence(raw_sentence=sentence_dict['raw_sentence'])
            for key, value in sentence_dict.items():
                if key == 'raw_sentence':
                    # We already set this
                    continue
                sentence.__setattr__(key, value)
            sentences.append(sentence)
        document.sentences = sentences

        if benchmark:
            document.run_time_stats = document_json_dict['run_time_stats']
            document.errors = document_json_dict['errors']
        else:
            document.run_time_stats = None
            document.errors = None

        return document
