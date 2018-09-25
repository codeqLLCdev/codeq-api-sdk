from collections import OrderedDict
import json
import re
import requests

CODEQ_API_ENDPOINT_LAST = 'http://api.codeq.com:8870/v1'


class OrderedClass:
    """
    Helper meta class to store variables in order of declaration within __init__ method.
    """

    def __new__(cls, *args, **kwargs):
        instance = object.__new__(cls)
        instance.__odict__ = OrderedDict()
        return instance

    def __setattr__(self, key, value):
        if key != '__odict__':
            self.__odict__[key] = value
        object.__setattr__(self, key, value)

    def keys(self):
        return self.__odict__.keys()

    def items(self):
        return self.__odict__.items()


class Document(OrderedClass):
    """
    A Document is a top level object used to store a list of sentences and its corresponding annotations.
    It needs to be created with a text string as required input parameter.

    Document attributes:

    - raw_text: the input string used to create the Document
    - tokens: a list of words
    - sentences: a list of Sentences objects
    - run_time_stats: a dict containing run time statistics about each annotator

    (The tokens, tokens_filtered and stems attributes can be stored at Document level, without the need to split into
    sentences)
    """

    def __init__(self, raw_text, tokens=None, sentences=None):
        # Document content
        self.raw_text = raw_text
        self.tokens = tokens
        self.sentences = sentences
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
        doc_dict = dict()
        for attr, value in self.items():
            if value is not None:
                if attr == 'sentences':
                    doc_dict[attr] = [s.to_dict() for s in value]
                else:
                    doc_dict[attr] = value
        return doc_dict

    def __str__(self):
        return 'Document: %s' % self.to_dict().__str__()


class Sentence(OrderedClass):
    """
    A Sentence is the basic object used to store different annotations.
    It needs to be created with a string as required input parameter.

    Sentence attributes:

    - raw_sentence: the input string used to create the Sentence
    - position: a number indicating the index position of the sentence in the Document
    - tokens: a list of words
    - tokens_filtered: a list of words without stop words
    - stems: a list of stemmed words
    - lemmas: a list of lemmatized words
    - pos_tags: a list of Part of Speech tags, corresponding to each word in the list of tokens
    - truecase_sentence: a string with a Truecase sentence
    - detruecase_sentence: a string with a Detruecase sentence
    - speech_act: a tag indicating its corresponding speech act
    - speech_act_value: the numeric value of the speech act
    - question_types: a list of the question types, if the sentence is categorized as speech act: 'question'
    - question_tags: a list of one- or two-letter question tags, if sentence is categorized as speech act: 'question'
    - named_entities: a list of named_entities tuples containing (entity tokens, type, list of tokens positions)
    - emotions: a list of emotions conveyed in a sentence
    - sentiment: sentiment conveyed in a sentence
    - task: an integer signaling if a sentence is a task or not
    - resolved_anaphora: a list of tokens with resolved personal pronouns
    """

    def __init__(self, raw_sentence):
        self.raw_sentence = raw_sentence
        self.position = None
        self.tokens = None
        self.tokens_filtered = None

        self.stems = None
        self.lemmas = None
        self.pos_tags = None

        self.truecase_sentence = None
        self.detruecase_sentence = None

        self.speech_act = None
        self.speech_act_value = None
        self.question_types = None
        self.question_tags = None

        self.named_entities = None
        self.nes_terms = None
        self.nes_types = None
        self.nes_positions = None

        self.emotions = None
        self.sarcastic = None

        self.sentiment = None

        self.dates = None

        self.is_task = None
        self.task_subclassification = None
        self.task_actions = None

        self.resolved_anaphora = None

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


def document_from_dict(document_json_dict):
    document = Document(raw_text=document_json_dict['raw_text'])
    document.run_time_stats = document_json_dict['run_time_stats']
    sentences = []
    for sentence_dict in document_json_dict['sentences']:
        sentence = Sentence(raw_sentence=sentence_dict['raw_sentence'])
        for key, value in sentence_dict.items():
            if key == 'raw_sentence':
                continue  # We already set this.
            sentence.__setattr__(key, value)
        sentences.append(sentence)
    document.sentences = sentences
    return document


class CodeqAPIError(Exception):
    pass


class CodeqClient(object):
    def __init__(self, user_id, user_key):
        self.user_id = user_id
        self.user_key = user_key
        self.endpoint = CODEQ_API_ENDPOINT_LAST

    def tokenize(self, text):
        pipeline = 'tokenize'
        return self.run_request(text, pipeline)

    def ssplit(self, text):
        pipeline = 'ssplit'
        return self.run_request(text, pipeline)

    def stopword(self, text):
        pipeline = 'stopword'
        return self.run_request(text, pipeline)

    def stem(self, text):
        pipeline = 'stem'
        return self.run_request(text, pipeline)

    def truecase(self, text):
        pipeline = 'truecase'
        return self.run_request(text, pipeline)

    def detruecase(self, text):
        pipeline = 'detruecase'
        return self.run_request(text, pipeline)

    def pos(self, text):
        pipeline = 'pos'
        return self.run_request(text, pipeline)

    def emotion(self, text):
        pipeline = 'emotion'
        return self.run_request(text, pipeline)

    def sarcasm(self, text):
        pipeline = 'sarcasm'
        return self.run_request(text, pipeline)

    def sentiment(self, text):
        pipeline = 'sentiment'
        return self.run_request(text, pipeline)

    def ner(self, text):
        pipeline = 'ner'
        return self.run_request(text, pipeline)

    def speechact(self, text):
        pipeline = 'speechact'
        return self.run_request(text, pipeline)

    def questions(self, text):
        pipeline = 'questions'
        return self.run_request(text, pipeline)

    def anaphora(self, text):
        pipeline = 'anaphora'
        return self.run_request(text, pipeline)

    def tasks(self, text):
        pipeline = 'tasks'
        return self.run_request(text, pipeline)

    def dates(self, text):
        pipeline = 'dates'
        return self.run_request(text, pipeline)

    def analyze(self, text, pipeline=None):
        """Input pipeline as a list of strings or a comma-separated string.
        Example: ['speechact', 'tasks'] or 'speechact, tasks'.
        Analyzer options: tokenize, ssplit, stopword, stem, truecase,
        detruecase, pos, emotion, sarcasm, sentiment, ner, speechact,
        questions, anaphora, tasks, dates"""
        if isinstance(pipeline, str):
            pipeline = re.split(r'\s*,\s*', pipeline)
        return self.run_request(text, pipeline=pipeline)

    def run_request(self, text, pipeline):
        params = {
            'user_id': self.user_id,
            'user_key': self.user_key,
            'text': text,
            'pipeline': pipeline,
        }
        request = requests.post(url=self.endpoint, json=params)

        if request.status_code == 200:
            # Make OrderedDict from request.text output
            document_json = json.loads(request.text, object_pairs_hook=OrderedDict)
            document = document_from_dict(document_json)
            return document
        else:
            raise CodeqAPIError("%s; %s" % (request.status_code, request.reason))
