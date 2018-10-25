import logging
import re
import sys
from operator import mul


logger = logging.getLogger('words_to_number.words_to_number')
# logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.NullHandler())
def log_exception(exc_type, exc_value, exc_traceback):
    # http://stackoverflow.com/a/16993115/2954547
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    raise exc_type(exc_value).with_traceback(exc_traceback)
sys.excepthook = log_exception
# logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.ERROR)


ONES = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9}
TEENS = {'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19}
UNITS = {**ONES, **TEENS}
TENS = {'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90}
HUNDREDS = {'hundred'}
MILLS = {'thousand': int(1e3), 'million': int(1e6), 'billion': int(1e9), 'trillion': int(1e12)}
STARTING_NUMBERS = set(UNITS) | set(TENS)
AND = {'and'}
SPLIT_REGEX = re.compile(r'\s+|-')

_ONE_t = 'one'
_TEN_t = 'ten'
_TEEN_t = 'teen'
_HUNDRED_t = 'hundred'
_MILL_t = 'mill'
_COMPOUND_t = 'compound'
_UNRECONIZED_t = 'unrecognized'


def unzip(seq_of_tuples):
    return zip(*seq_of_tuples)


def split_text(string):
    tokens = SPLIT_REGEX.split(string)
    return list(filter(bool, tokens))


def get_type(string):
    if string in ONES:
        return _ONE_t
    if string in TEENS:
        return _TEEN_t
    if string in TENS:
        return _TEN_t
    if string in HUNDREDS:
        return _HUNDRED_t
    if string in MILLS:
        return _MILL_t
    if "-" in string:
        ten, unit = string.split("-")
        if (ten in TENS) and (unit in ONES):
            return _COMPOUND_t
    return _UNRECONIZED_t


# def is_valid_next_type(types_so_far, next_token):
#     """
#     Valid overall sequence:
#         [ ... [ hundreds_chunk mill ] ] [ hundreds_chunk ]
#     Valid hundreds chunks:
#         [tens_chunk [hundred] ] [ tens_chunk ]
#     """
#     next_type = get_type(next_token)
#     return None


def split_list_once(items, value):
    """ Split `items` where `value` occurs """
    if not items:
        return ()

    try:
        index = items.index(value)
    except ValueError:
        return (items,)

    return items[:index], items[(index + 1):]


def parse_chunk(tokens):
    """ Parse a "hundreds" chunk """
    if not tokens:
        return 0

    split_tokens = split_list_once(tokens, 'hundred')

    if len(split_tokens) == 2:
        pre_hundred, post_hundred = split_tokens
        logger.debug("\t\tReceived hundreds chunk: %s, %s", pre_hundred, post_hundred)
        return 100 * parse_chunk(pre_hundred) + parse_chunk(post_hundred)

    tokens = split_tokens

    if len(tokens) == 2:
        first, second = tokens
        first_type = get_type(first)
        second_type = get_type(second)
        logger.debug("\t\tReceived chunk: '%s' (%s), '%s' (%s)", first, first_type, second, second_type)

        # "sixty five"  ->   65
        if first_type == 'tens' and second_type == _ONE_t:
            first_value = TENS[first] * 10
            second_value = UNITS[second] * 1

        # "twenty eighty"  ->  2080
        elif first_type in 'tens' and second_type == _TEN_t:
            first_value = TENS[first] * 100
            second_value = TENS[second] * 10

        # "one eighty"  ->  180 / "sixteen fifty"  ->  1650
        # ... note, I haven't gotten to "sixteen fifty-five" yet...
        elif first_type in (_ONE_t, _TEEN_t) and second_type == _TEN_t:  
            first_value = UNITS[first] * 100
            second_value = TENS[second] * 10

        # "one sixteen"  ->  116
        elif first_type == _ONE_t and second_type == _TEEN_t:
            first_value = UNITS[first] * 100
            second_value = UNITS[second] * 1

        else:
            raise ValueError("Unrecognized sequence {}".format(tokens))

        result = first_value + second_value
        logger.debug("\t\tValue: %i + %i = %s", first_value, second_value, result)
        return result

    elif len(tokens) == 1:
        token = tokens[0]
        logger.debug("\t\tReceived singleton: '%s'", token)

        if "-" in token:
            return parse_chunk(token.split("-"))
        try:
            return 10 * TENS[token]
        except ValueError:
            try:
                return UNITS[token]
            except ValueError:
                raise ValueError("Unrecognized number: {}".format(token))

    else:
        raise ValueError("Unrecognized format: {}".format(tokens))


def parse_tokens(tokens):
    """Break at separators and parse each chunk as a hundred"""
    if 'point' in tokens:
        raise ValueError("Decimals not implemented")

    # positions_types = list(zip(*((i, get_type(token)) for i, token in enumerate(tokens))))
    #positions_tokens_types = unzip((i, token, get_type(token)) for i, token in enumerate(tokens))
    #positions_mills = list(unzip((i, token) for i, token, ttype in unzip(positions_tokens_types) if ttype == 'mills'))
    positions_mills = list(unzip((i, token) for i, token in enumerate(tokens) if get_type(token) == _MILL_t))

    n_separators = 0
    if positions_mills:
        positions, mills = positions_mills  # only split after we know it won't be an error
        logger.debug("\tFound {} separators at {} of mills {}".format(len(positions), positions, mills))

        powers = [*(MILLS[t] for t in mills), 1]
        positions = (*positions, len(tokens))

        start = 0
        parsed_chunks = []
        for stop in positions:
            chunk = tokens[start:stop]
            logger.debug("\tBefore separator, parsing chunk from {} until {}: {}".format(start, stop, chunk))

            try:
                parsed_chunk = parse_chunk(chunk)
            except (ValueError, NotImplementedError):
                # Bail out immediately if parsing fails, so we can return the
                # problem back up to find_numbers, so it can start its search
                # over again
                return None

            parsed_chunks.append(parsed_chunk)
            start = stop + 1

        return sum(map(mul, powers, parsed_chunks))

    else:
        logger.debug("\tBy itself, parsing chunk: {}".format(tokens))

        try:
            return parse_chunk(tokens)
        except (ValueError, NotImplementedError):
            # Bail out immediately if parsing fails, so we can return the
            # problem back up to find_numbers, so it can start its search
            # over again
            return None


def find_numbers(text):
    """Extract numbers from text, tokenizing on whitespace"""
    if isinstance(text, str):
        tokens = split_text(text.lower())
    else:
        tokens = list(map(str.lower, text))

    results, starts, lengths = [], [], []
    prev_type = None
    attempting = False
    attempt_number = -1
    logger.debug("Parsing sequence of length {}:\n\t{}".format(len(tokens), tokens))
    for i, token in enumerate(tokens):
        logger.debug("Checking token {}".format(token))
        if not attempting:
            if token in STARTING_NUMBERS:
                # Move into the "attempting match" state
                attempting = True
                attempt_number += 1
                logger.debug("Start attempt {} at {}".format(attempt_number, i))
                start = i
                length = 0
                and_offset = 0
                stop = start + length + 1 + and_offset
                result = parse_tokens(tokens[start:stop])
                logger.debug("First result: {}".format(result))
                # initialize placeholders for the values we're going to save
                starts.append(None)
                lengths.append(None)
                results.append(None)
        else:
            # Continue in the "attempting match" state
            logger.debug("Continuing attempt {} at {} (length of previous result: {})".format(attempt_number, i, length))
            if token in AND:
                # we want to skip "and" but not cause it to trigger a failure
                continue
            if token in ALL_NUMBERS:
                logger.debug("Match successful")
                stop = start + length + 1 + and_offset
                to_be_parsed = tokens[start:stop]
                # remove all the and's before continuing
                for and_word in AND:
                    logger.debug("Looking for 'and's to remove")
                    try:
                        to_be_parsed.remove(and_word)
                    except ValueError:
                        pass
                    else:
                        logger.debug("Removed an 'and'")
                        and_offset += 1
                    break
                result = parse_tokens(to_be_parsed)
                if result:
                    # We got a result, so bank what we got and keep going
                    length += 1
                    logger.debug("Longest result so far: %s at length %i", result, length)
                    logger.debug("Banking results so far: %s, %i until %i", result, start, start + length)
                    starts[attempt_number] = start
                    lengths[attempt_number] = stop - start
                    results[attempt_number] = result
                else:
                    # Drop out of the "attempting match" state
                    logger.debug("Attempt of length %i terminated on parse failure with result %s", length, result)
                    attempting = False
            else:
                # Drop out of the "attempting match" state
                logger.debug("Attempt of length %i terminated on non-match with result %s", length, result)
                attempting = False

    # Save the latest results, knowing that if they are never
    # overwritten then we never found anything better
    logger.debug("Final starts: %s", starts)
    logger.debug("Final lengths: %s", lengths)
    logger.debug("Final results: %s", results)
    if results:
        return {result: (start, length) for result, start, length in zip(results, starts, lengths)}
    else:
        return None


def replace_numbers(text, formatstr=None):
    # TODO in the distant future: save the whitespace and return it as it was input
    tokens = split_text(text.lower())
    results = find_numbers(tokens)
    if not results:
        return text
    for replacement, (start, length) in results.items():
        if formatstr:
            tokens[start] = formatstr % replacement
        else:
            tokens[start] = str(replacement)
        for i in range(start + 1, start+length):
            tokens[i] = None
    return ' '.join(token for token in tokens if token)

