from .documents import ProductDocument
from elasticsearch_dsl.query import Q as ES_Q
from math import ceil


def get_rating_stats(product):
    total = product.total_people_rated or 1
    return {
        'rating_percentages': {
            '5': round((product.rating_5_count / total) * 100, 1),
            '4': round((product.rating_4_count / total) * 100, 1),
            '3': round((product.rating_3_count / total) * 100, 1),
            '2': round((product.rating_2_count / total) * 100, 1),
            '1': round((product.rating_1_count / total) * 100, 1),
        }
    }


def elasticsearch_query(search_text, price_filter, sale_filter, rating_filter):
    q = ES_Q("multi_match", query=search_text, fields=["name^3", "category.name^1"], fuzziness=1, type="best_fields", tie_breaker=0.3)

    filters = []

    if price_filter == 'under_10':
        filters.append(ES_Q('range', final_price={'lt': 10}))
    elif price_filter == '10_50':
        filters.append(ES_Q('range', final_price={'gte': 10, 'lte': 50}))
    elif price_filter == '50_100':
        filters.append(ES_Q('range', final_price={'gte': 50, 'lte': 100}))
    elif price_filter == 'over_100':
        filters.append(ES_Q('range', final_price={'gt': 100}))

    if sale_filter == 'on_sale':
        filters.append(ES_Q('term', on_sale=True))
    elif sale_filter == 'not_on_sale':
        filters.append(ES_Q('term', on_sale=False))

    rating = {
        '1_and_up': 1,
        '2_and_up': 2,
        '3_and_up': 3,
        '4_and_up': 4,
        '5_and_up': 5,
    }.get(rating_filter, 1)
    filters.append(ES_Q('range', average_rating={'gte': rating}))

    final_query = ES_Q('bool', must=q, filter=filters)

    return ProductDocument.search().query(final_query)


def search_with_pagination(search_text, price_filter, sale_filter, rating_filter, page):
    result = elasticsearch_query(search_text, price_filter, sale_filter, rating_filter)

    # get total number of records and pages
    page_size = 8
    total_hits = result.count()
    total_pages = ceil(total_hits / page_size)

    # now get the documents for current page
    start = (page - 1) * page_size

    result = result.extra(from_ = start, size = page_size)

    # Perform the search
    result = result.to_queryset()

    return {
        "result": result,
        "total_hits": total_hits,
        "total_pages": total_pages,
        "current_page": page
    }