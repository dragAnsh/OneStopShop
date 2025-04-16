from elasticsearch_dsl import analyzer, tokenizer


# For substring search (like 'oard' in 'board')
ngram_analyzer = analyzer(
    'ngram_analyzer',
    tokenizer=tokenizer(
        'ngram_tokenizer', 'ngram',
        min_gram=4,
        max_gram=5,
        token_chars=['letter', 'digit']
    ),
    filter=['lowercase']
)