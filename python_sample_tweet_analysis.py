###PYTHON CODE 
### Analyzing Election Tweets
### Jaehoon Ahn 

import argparse
import json
import string
import sys
from util import sort_count_pairs, grab_year_month, pretty_print_by_month
from basic_algorithms import find_top_k, find_min_count, find_frequent

##################### BASIC SETUP ##################### 

PUNCTUATION = '!"$%\'()*+,-./:;<=>?[\\]^_`{|}~' + u"\u2014" + u"\u2026"

STOP_WORDS_SHORT = set(["a", "an", "the", "this", "that", "of", "for", "or", "and", "on", "to", "be", "if", "we", "you", "in", "is", "at", "it", "rt", "mt"])

STOP_WORDS = {"basic":STOP_WORDS_SHORT,
              "hrc":set(["clinton", "hillary", "tim", "timothy", "kaine"]).union(STOP_WORDS_SHORT),
              "djt": set(["donald", "trump", "mike", "michael", "pence"]).union(STOP_WORDS_SHORT),
              "both": STOP_WORDS_SHORT.union(set(["clinton", "hillary", "donald", "trump", "tim", "timothy", "kaine", "mike", "michael", "pence"])),
              "none": set([])}

STOP_PREFIXES  = {"default": set(["@", "#", "http", "&amp"]),
                  "hashtags_only": set(["#"]),
                  "none": set([])}

HRC_STOP_WORDS = STOP_WORDS["hrc"]
DT_STOP_WORDS = STOP_WORDS["djt"]
BOTH_CAND_STOP_WORDS = STOP_WORDS["both"]

# Tweets are represented as dictionaries that has the same keys and
# values as the JSON returned by twitter's search interface.


def entitylist(tweets, entity_key, value_key):
    '''
    Returns complete list of entity values 

    Inputs:
        tweets: a list of tweets
        entity_key: a string ("hashtags", "user_mentions", etc)
        value_key: string (appropriate value depends on the entity type)

    Returns: list of entity values
    '''

    entities = []
    for tweet in tweets: 
        entity = tweet['entities'][entity_key]
        for subentity in entity: 
            value = subentity[value_key]
            entities.append(value.lower())

    return entities 


def find_top_k_entities(tweets, entity_key, value_key, k):
    '''
    Find the K most frequently occuring entitites

    Inputs:
        tweets: a list of tweetss
        entity_key: a string ("hashtags", "user_mentions", etc)
        value_key: string (appropriate value depends on the entity type)
        k: integer 

    Returns: list of entity, count pairs sorted in non-decreasing order by count.

    '''
    
    all_entities = entitylist(tweets, entity_key, value_key)
    top_k_entities = find_top_k(all_entities, k)

    return top_k_entities


def find_min_count_entities(tweets, entity_key, value_key, min_count):
    '''
    Find the entitites that occur at least min_count times.

    Inputs:
        tweets: a list of tweets
        entity_key: a string ("hashtags", "user_mentions", etc)
        value_key: string (appropriate value depends on the entity type)
        min_count: integer 

    Returns: list of entity, count pairs sorted in non-decreasing order by count.
    '''

    all_entities = entitylist(tweets, entity_key, value_key)

    min_count_entities = find_min_count(all_entities, min_count)

    return min_count_entities 


def find_frequent_entities(tweets, entity_key, value_key, k):
    '''
    Find entities where the number of times the specific entity occurs
    is at least fraction * the number of entities in across the tweets.

    Input: 
        tweets: a list of tweets
        entity_key: a string ("hashtags", "user_mentions", etc)
        value_key: string (appropriate value depends on the entity type)
        k: integer

    Returns: list of entity, count pairs sorted in non-decreasing order by count.
    '''

    all_entities = entitylist(tweets, entity_key, value_key)

    frequent_entities = find_frequent(all_entities, k)

    return frequent_entities


def preprocess_words(tweets, n, stop_words, stop_prefixes):
    '''
    Pre-processes extracted words from a tweet

    Inputs:    
        tweets: a list of tweets
        n: integer
        stop_words: a set of strings to ignore
        stop_prefixes: a set of strings.  Words w/ a prefix that
          appears in this list should be ignored.

    Output: 
        processed_value(string): processed words 
    '''

    #make a list of words
    allWords = []
    for tweet in tweets:
        text = tweet['text'] #extract text 
        split_text = text.split(' ') #separates text into words

        for word in split_text: 
            punct_free = word.strip(PUNCTUATION) #strips punctuation
            clean_word = punct_free.lower() #makes words lower case
            if clean_word and \
            (clean_word not in STOP_WORDS[stop_words]): #checks stop words
                l = 0
                for prefix in STOP_PREFIXES[stop_prefixes]: #checks prefix
                    l += 1
                    if clean_word.startswith(prefix):
                        break
                    elif l == len(STOP_PREFIXES[stop_prefixes]): 
                        allWords.append(clean_word)      
                 
    #break up words list into n grams 
    wordTuples = []
    for i in range(0, len(allWords)): 
        lastPosition = i + n 
        if lastPosition <= len(allWords): 
            groupWord = ()
            for j in range(i, lastPosition): 
                groupWord += (allWords[j],)
            wordTuples.append(groupWord)
    
    return wordTuples


def find_top_k_ngrams(tweets, n, stop_words, stop_prefixes, k):
    '''
    Find k most frequently occurring n-grams or
    if k < 0, count occurrences of all n-grams
    
    Inputs:
        tweets: a list of tweets
        n: integer
        stop_words: a set of strings to ignore
        stop_prefixes: a set of strings.  Words w/ a prefix that
          appears in this list should be ignored.
        k: integer

    Returns: list of key/value pairs sorted in non-increasing order
      by value.
    '''

    wordTuples = preprocess_words(tweets, n, stop_words, stop_prefixes)
    
    if k < 0:
        return compute_counts(wordTuples)
    else: 
        return find_top_k(wordTuples, k)


def find_min_count_ngrams(tweets, n, stop_words, stop_prefixes, min_count):
    '''
    Find n-grams that occur at least min_count times.
    
    Inputs:
        tweets: a list of tweets
        n: integer
        stop_words: a set of strings to ignore
        stop_prefixes: a set of strings.  Words w/ a prefix that
          appears in this list should be ignored.
        min_count: integer


    Returns: list of key/value pairs sorted in non-increasing order
      by value.
    '''

    wordTuples = preprocess_words(tweets, n, stop_words, stop_prefixes)

    return find_min_count(wordTuples, min_count)


def find_frequent_ngrams(tweets, n, stop_words, stop_prefixes, k):
    '''
    Find frequently occurring n-grams

    Inputs:
        tweets: a list of tweets
        n: integer
        stop_words: a set of strings to ignore
        stop_prefixes: a set of strings.  Words w/ a prefix that
          appears in this list should be ignored.
        k: integer

    Returns: list of key/value pairs sorted in non-increasing order
      by value.
    '''

    wordTuples = preprocess_words(tweets, n, stop_words, stop_prefixes)
    
    return find_frequent(wordTuples, k)


def find_top_k_ngrams_by_month(tweets, n, stop_words, stop_prefixes, k):
    '''                                                                                                            
    Find the top k ngrams for each month.

    Inputs:
        tweets: list of tweet dictionaries
        n: integer
        stop_words: a set of strings to ignore
        stop_prefixes: a set of strings.  Words w/ a prefix that
          appears in this list should be ignored.
        k: integer

    Returns: sorted list of pairs.  Each pair has the form: 
        ((year,  month), (sorted top-k n-grams for that month with their counts))
    '''

    #creat dictionary of date key and tweets as values
    top_k_byDate_dict = {}
    for tweet in tweets: #each tweet
        date = grab_year_month(tweet['created_at']) 
        top_k_byDate_dict.setdefault(date, []).append(tweet) 
    
    #create list of pairs (date & sorted top-k n-grams)
    top_k_byDate_list = []    
    for date in top_k_byDate_dict: 
        tweet = top_k_byDate_dict[date]
        #print(tweet)
       
        top_k_byDate = find_top_k_ngrams(tweet, n, stop_words, stop_prefixes, k)
        print(top_k_byDate)

        top_k_byDate_list.append((date, top_k_byDate)) #fine 

    
    return sorted(top_k_byDate_list)


def parse_args(args):
    '''                                                                                                                
    Parse the arguments                                                                                                
    '''
    parser = argparse.ArgumentParser(description='Analyze presidential candidate tweets .')
    parser.add_argument('-t', '--task', nargs=1, help="<task number>", type=int, default=[0])
    parser.add_argument('-k', '--k', nargs=1, help="value for k", type=int, default=[1])
    parser.add_argument('-c', '--min_count', nargs=1, help="min count value", type=int, default=[1])
    parser.add_argument('-n', '--n', nargs=1, help="number of words in an n-gram", type=int, default=[1])
    parser.add_argument('-e', '--entity_key', nargs=1, help="entity key for task 1", type=str, default=["hashtags"])
    parser.add_argument('file', nargs=1, help='name of JSON file with tweets')

    try:
        return parser.parse_args(args[1:])
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)

def go(args):
    task = args.task
    
    task = task[0]

    if task <= 0 or task > 7:
        print("The task number needs to be a value between 1 and 7 inclusive.",
              file=sys.stderr)
        sys.exit(1)
        
    ek2vk = {"hashtags":"text", 
             "urls":"url", 
             "user_mentions":"screen_name"}

    if task in [1,2,3]:
        ek = args.entity_key=args.entity_key[0]
        if ek not in ek2vk:
            print("Entity type must be one of: hashtags, urls, or user_mentions", 
                  file=sys.stderr)
            sys.exit(1)
        else:
            vk = ek2vk[ek]

    try:
        tweets = json.load(open(args.file[0]))
    except OSError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    if task == 1:
        print(find_top_k_entities(tweets, ek, vk, args.k[0]))

    elif task == 2:
        print(find_min_count_entities(tweets, ek, vk, args.min_count[0]))

    elif task == 3:
        print(find_frequent_entities(tweets, ek, vk, args.k[0]))

    elif task == 4:
        print(find_top_k_ngrams(tweets, args.n[0], BOTH_CAND_STOP_WORDS, 
                                STOP_PREFIXES["default"], args.k[0]))
    elif task == 5:
        print(find_min_count_ngrams(tweets, args.n[0], BOTH_CAND_STOP_WORDS, 
                                    STOP_PREFIXES["default"], args.min_count[0]))
    elif task == 6:
        print(find_frequent_ngrams(tweets, args.n[0], BOTH_CAND_STOP_WORDS, 
                                   STOP_PREFIXES["default"], args.k[0]))
    elif task == 7:
        result = find_top_k_ngrams_by_month(tweets, args.n[0], BOTH_CAND_STOP_WORDS, 
                                            STOP_PREFIXES["default"], args.k[0])
        pretty_print_by_month(result)



if __name__=="__main__":
    args = parse_args(sys.argv)
    go(args)



