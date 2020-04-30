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

    - language: predicted language
    - language_probability: probability of predicted language
    - raw_text: the input string used to create the Document
    - tokens: a list of words
    - raw_detokens: a list of words in detokenized form
    - summary: a string containing the summary of the input text
    - summary_detokens: a string containing the summary of the input text in detokenized form
    - compressed_summary: a string containing the compressed summary of the input text
    - compressed_summary_detokens: a string containing the compressed summary of the input text in detokenized form
    - keyphrases: a list of extracted keyphrases for the document, in decreasing order of relevance
    - keyphrases_scored: a list of extracted keyphrases for the document, including their scores
    - errors: a list of error messages collected while analyzing a Document
    - run_time_stats: a dict containing run time statistics about each annotator
    - sentences: a list of Sentences objects
    """

    def __init__(self, raw_text, tokens=None, sentences=None):
        # Document content
        self.language = None
        self.language_probability = None
        self.raw_text = raw_text
        self.tokens = tokens
        self.raw_detokens = None
        self.summary = None
        self.summary_detokens = {}
        self.compressed_summary = None
        self.compressed_summary_detokens = {}
        self.keyphrases = None
        self.keyphrases_scored = None
        # Errors
        self.errors = []
        # Stats
        self.run_time_stats = {}
        # Sentences
        self.sentences = sentences

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
    - dependencies: a list of tuples containing the dependencies of each word, including: head, dependent and relation.
    - semantic_roles: a dictionary giving information on the retrieved predicates for the sentence, their lemmas,
        the constituents of the sentence found to be arguments of each predicate,
        and the argument type classified for the each argument.
    - chunks: list of non-overlapping groups based on prominent parts of speech, e.g., noun or verbal phrases
    - chunk_labels: list of chunk tags for each word
    - chunk_tuples: list of tuples containing the chunk tag, chunk tokens and chunk tokens positions
    - truecase_sentence: a string with a Truecase sentence
    - detruecase_sentence: a string with a Detruecase sentence
    - speech_acts: a list of tags indicating its corresponding speech act
    - speech_act_values: a list of numeric values associated to a speech act
    - question_types: a list of the question types, if the sentence is categorized as speech act: 'question'
    - question_tags: a list of one- or two-letter question tags, if sentence is categorized as speech act: 'question'
    - named_entities: a list of tuples containing (entity tokens, type, list of tokens positions)
    - named_entities_linked: a list of dictionaries containing disambiguated entities with a reference
        to Wikipedia and Wikidata URLs.
    - named_entities_salience: a list of tuples indicating if a named entity is salient or not, and its salience score.
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

        self.semantic_roles = None

        self.chunks = None
        self.chunk_labels = None
        self.chunk_tuples = None

        self.truecase_sentence = None
        self.detruecase_sentence = None

        self.speech_acts = None
        self.speech_act_values = None
        self.question_types = None
        self.question_tags = None

        self.named_entities = None
        self.named_entities_linked = None
        self.named_entities_salience = None
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

    def language(self, text):
        return self.__run_request(text, pipeline='language')

    def tokenize(self, text):
        return self.__run_request(text, pipeline='tokenize')

    def detokenize(self, text):
        return self.__run_request(text, pipeline='detokenize')

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

    def lemma(self, text):
        return self.__run_request(text, pipeline='lemma')

    def speechact(self, text):
        return self.__run_request(text, pipeline='speechact')

    def question(self, text):
        return self.__run_request(text, pipeline='question')

    def ner(self, text):
        return self.__run_request(text, pipeline='ner')

    def parse(self, text):
        return self.__run_request(text, pipeline='parse')

    def semantic_roles(self, text):
        return self.__run_request(text, pipeline='semantic_roles')

    def coreferences(self, text):
        return self.__run_request(text, pipeline='coreference')

    def date(self, text):
        return self.__run_request(text, pipeline='date')

    def task(self, text):
        return self.__run_request(text, pipeline='task')

    def sentiment(self, text):
        return self.__run_request(text, pipeline='sentiment')

    def emotion(self, text):
        return self.__run_request(text, pipeline='emotion')

    def sarcasm(self, text):
        return self.__run_request(text, pipeline='sarcasm')

    def compress(self, text):
        return self.__run_request(text, pipeline='compress')

    def summarize(self, text):
        return self.__run_request(text, pipeline='summarize')

    def summarize_compress(self, text):
        return self.__run_request(text, pipeline='summarize_compress')

    def chunk(self, text):
        return self.__run_request(text, pipeline='chunk')

    def nel(self, text):
        return self.__run_request(text, pipeline='nel')

    def salience(self, text):
        return self.__run_request(text, pipeline='salience')

    @staticmethod
    def _json_to_class(cls, data):
        """
        Deserialize a json string into an instance of a given class
        :param cls: Class name
        :param data: Json string
        :return:
        """
        instance = object.__new__(cls)
        for key, value in list(data.items()):
            setattr(instance, key, value)
        return instance

    def __document_from_json(self, document_json, benchmark):
        document = self._json_to_class(cls=Document, data=document_json)
        document.sentences = [self._json_to_class(cls=Sentence, data=sent_dict) for sent_dict in document.sentences]
        if not benchmark:
            document.run_time_stats = None

        return document

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
            # Deserialize JSON response
            document_json = json.loads(request.text, object_pairs_hook=OrderedDict)
            document = self.__document_from_json(document_json, benchmark)
            return document
        else:
            raise CodeqAPIError("%s; %s" % (request.status_code, request.reason))

    def analyze(self, text, pipeline=None, benchmark=False):
        """
        :param text: A string
        :param pipeline: A list of strings or a comma-separated string indicating the specific annotators
            to apply to the input text. Example: ['speechact', 'tasks'] or 'speechact, tasks'.
            Analyzer Annotator options, see: https://api.codeq.com/api
        :param benchmark: Boolean to indicate the storage of benchmark run times for each Annotator
        :return: Instance of a Document object with analyzed Sentences
        """
        if isinstance(pipeline, str):
            pipeline = re.split(r'\s*,\s*', pipeline)
        document = self.__run_request(text, pipeline=pipeline, benchmark=benchmark)
        return document
